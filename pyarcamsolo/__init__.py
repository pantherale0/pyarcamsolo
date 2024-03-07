# pylint: disable=import-error,broad-except
"""Arcam Solo telnet communication library."""

import asyncio
import time
import logging
import re
import math

from datetime import datetime
from collections.abc import Callable
from inspect import isfunction

from .commands import (
    ARCAM_COMM_END,
    ARCAM_COMM_START,
    COMMAND_CODES,
    IR_COMMAND_CODES,
    SOURCE_IR_CONTROL_MAP,
    ARCAM_QUERY_COMMANDS
)
from .util import sock_set_keepalive, cancel_task, get_backoff_delay
from .parser import parse_response
from ._version import __version__ as VERSION

_LOGGER = logging.getLogger(__name__)

class ArcamSolo:
    """Base Arcam Solo module."""

    def __init__(
        self,
        host,
        port,
        timeout=2,
        scan_interval=60,
        params=None):
        """Initialise the Arcam Solo interface."""
        _LOGGER.info("Starting pyarcamsolo %s", VERSION)
        _LOGGER.debug(
            '>> ArcamSolo.__init__(host="%s", port="%s", timeout="%s", params="%s")',
            host,
            port,
            timeout,
            params
        )
        self._host = host
        self._port = port
        self._timeout = timeout
        self.scan_interval = scan_interval

        # Public props
        self.software_version = None
        self.available = False

        # Data
        self.zones = {}

        # Locks
        self._connect_lock = asyncio.Lock()
        self._disconnect_lock = asyncio.Lock()
        self._update_lock = asyncio.Lock()
        self._request_lock = asyncio.Lock()
        # Events
        self._update_event = asyncio.Event()
        self._response_event = asyncio.Event()
        self._response_queue = []
        self._queue_responses = False
        self._reconnect = True
        self._full_update = True
        self._last_command = None
        self._last_updated = None
        self._reader = None
        self._writer = None
        self._listener_task = None
        self._responder_task = None
        self._reconnect_task = None
        self._updater_task = None
        self._command_queue_task = None
        self._initial_query = True
        # Stores a list of commands to run after receiving an event
        self._command_queue = []
        self._power_zone_1 = None

    def __del__(self):
        _LOGGER.debug(">> ArcamSolo.__del__()")

    def _set_socket_options(self):
        """Set socket keepalive options."""
        sock_set_keepalive(
            self._writer.get_extra_info("socket"),
            after_idle_sec=int(self._timeout),
            interval_sec=int(self._timeout),
            max_fails=3,
        )

    @property
    def get_unique_id(self):
        """Return a unique ID."""
        return f"{self._host}:{self._port}"

    async def _responder_cancel(self):
        """Cancel any active responder task."""
        await cancel_task(self._responder_task, "responder")
        self._responder_task = None

    async def _connection_listener(self):
        """Arcam connection listener. Parse responses and update state."""
        _LOGGER.debug(">> ArcamSolo._connection_listener() started")
        running = True
        while self.available:
            action = " listening for responses"
            try:
                response = await self._read_response()
                if response is None:
                    # Connection closed or exception
                    break
                self._last_updated = time.time()
                if not response:
                    # Skip empty response
                    continue
                _LOGGER.debug("received Arcam response: %s", response.hex())
                action = " parsing response " + response.hex()
                value = parse_response(response)
                if value is not None:
                    _LOGGER.debug("parsed response %s", value)
                    if value["z"] not in self.zones:
                        self.zones[value["z"]] = {}
                    self.zones[value["z"]][value["k"]] = value["v"]
            except asyncio.CancelledError:
                _LOGGER.debug((">> ArcamSolo._connection_listener() cancelled"))
                running = False
                break
            except Exception as exc:
                _LOGGER.error("listener exception%s: %s",
                              action,
                              str(exc))
                # continue listening on exception

        if running and self.available:
            # Trigger disconnection
            await self.disconnect()

        _LOGGER.debug(">> ArcamSolo._connection_listener() completed")

    async def _listener_schedule(self):
        """Schedule the listener task."""
        _LOGGER.debug(">> ArcamSolo._listener_schedule()")
        await self._listener_cancel()
        self._listener_task = asyncio.create_task(self._connection_listener())

    async def _listener_cancel(self):
        """Cancel the listener task."""
        await cancel_task(self._listener_task, "listener")
        self._listener_task = None

    async def connect(self, reconnect=True):
        """Open a connection to the Hi-Fi and start listener thread."""
        _LOGGER.debug(">> ArcamSolo.connect() started")
        if self._connect_lock.locked():
            _LOGGER.warning("Connection is already in progress, skipping connect.")
            return
        if self.available:
            _LOGGER.warning("Device is connected, skipping connection.")
            return

        async with self._connect_lock:
            _LOGGER.debug("Opening Arcam connection.")
            if self._writer is not None:
                raise RuntimeError("Device already connected.")

            # open a connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout
            )
            _LOGGER.info("Device connection established.")
            self._reader = reader
            self._writer = writer
            self.available = True
            self._reconnect = reconnect
            self._set_socket_options()

            await self._responder_cancel()
            await self._listener_schedule()
            await asyncio.sleep(0) # yield to listener task

            # perform initial queries
            for query in ARCAM_QUERY_COMMANDS:
                await self.send_raw_command(
                    command=query,
                    data=[b'\xF0']
                )

            # auto set RTC to current time
            await self.send_raw_command(
                command="time",
                data=[
                    (datetime.today().weekday()+1).to_bytes(1, 'little'),
                    datetime.now().hour.to_bytes(1, 'little'),
                    datetime.now().minute.to_bytes(1, 'little'),
                    datetime.now().second.to_bytes(1, 'little')
                ]
            )

        _LOGGER.debug(">> ArcamSolo.connect() completed")

    async def disconnect(self):
        """Shutdown and close telnet connection to Arcam."""
        _LOGGER.debug(">> ArcamSolo.disconnect() started")

        if self._disconnect_lock.locked():
            _LOGGER.warning(
                "Arcam connection is already disconnecting, skipping disconnect"
            )
            return
        if not self.available:
            _LOGGER.warning("Arcam not connected, skipping disconnect")
            return

        async with self._disconnect_lock:
            _LOGGER.debug("disconnecting Arcam connection")
            self.available = False

            await self._listener_cancel()
            await self._responder_cancel()

            writer = self._writer
            if writer:
                # Close AVR connection
                _LOGGER.debug("closing Arcam connection")
                self._writer.close()
                try:
                    await self._writer.wait_closed()
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.debug("ignoring responder exception %s", str(exc))
            self._reader = None
            self._writer = None
            _LOGGER.info("Arcam connection closed")

            await self._reconnect_schedule()

        _LOGGER.debug(">> ArcamSolo.disconnect() completed")

    async def shutdown(self):
        """Shutdown the client."""
        _LOGGER.debug(">> ArcamSolo.shutdown()")
        self._reconnect = False
        await self._reconnect_cancel()
        await self.disconnect()

    async def reconnect(self):
        """Reconnect to an ArcamSolo."""
        _LOGGER.debug(">> ArcamSolo.reconnect() started")
        retry = 0
        try:
            while not self.available:
                delay = get_backoff_delay(retry)
                _LOGGER.debug("waiting %ds before retrying connection", delay)
                await asyncio.sleep(delay)

                retry += 1
                try:
                    await self.connect()
                    if self.available:
                        break
                except asyncio.CancelledError:  # pylint: disable=try-except-raise
                    # pass through to outer except
                    raise
                except Exception as exc:  # pylint: disable=broad-except
                    _LOGGER.debug(
                        "could not reconnect to Arcam Solo: %s: %s", type(exc).__name__, exc
                    )
                    # fall through to reconnect outside try block

                if self.available:
                    await self.disconnect()
        except asyncio.CancelledError:
            _LOGGER.debug(">> ArcamSolo.reconnect() cancelled")

        _LOGGER.debug(">> ArcamSolo.reconnect() completed")

    async def _reconnect_schedule(self):
        """Schedule reconnection to ArcamSolo."""
        if self._reconnect:
            _LOGGER.debug(">> ArcamSolo._reconnect_schedule()")
            reconnect_task = self._reconnect_task
            if reconnect_task:
                await asyncio.sleep(0)  # yield to reconnect task if running
                if reconnect_task.done():
                    reconnect_task = None  # trigger new task creation
            if reconnect_task is None:
                _LOGGER.info("reconnecting to ArcamSolo")
                reconnect_task = asyncio.create_task(self.reconnect())
                self._reconnect_task = reconnect_task
            else:
                _LOGGER.error("ArcamSolo listener reconnection already running")

    async def _reconnect_cancel(self):
        """Cancel any active reconnect task."""
        await cancel_task(self._reconnect_task, "reconnect")
        self._reconnect_task = None

    # Reader co-routine
    async def _reader_readuntil(self):
        """Read from reader with cancel detection."""
        try:
            return await self._reader.readuntil(ARCAM_COMM_END)
        except asyncio.CancelledError:
            _LOGGER.debug("reader: readuntil() was cancelled")
            return None

    async def _read_response(self, timeout=None):
        """Wait for a response from device and return to all readers."""
        _LOGGER.debug(">> ArcamSolo._read_response(timeout=%s)", timeout)

        # Schedule responder task if not already created
        responder_task = self._responder_task
        if responder_task:
            if responder_task.done():
                responder_task = None  # trigger new task creation
        if responder_task is None:
            responder_task = asyncio.create_task(self._reader_readuntil())
            self._responder_task = responder_task
            _LOGGER.debug(">> ArcamSolo._read_response() created responder task %s",
                          responder_task.get_name())
        else:
            # Wait on existing responder task
            _LOGGER.debug(">> ArcamSolo._read_response() using responder task %s",
                          responder_task.get_name())

        # Wait for result and process
        task_name = asyncio.current_task().get_name()
        try:
            if timeout:
                _LOGGER.debug(
                    ">> ArcamSolo._read_response() %s: waiting for data (timeout=%s)",
                    task_name,
                    timeout
                )
                done, pending = await asyncio.wait(  # pylint: disable=unused-variable
                    [responder_task], timeout=timeout
                )
                if done:
                    raw_response = responder_task.result()
                else:
                    _LOGGER.debug(">> ArcamSolo._read_response() %s: timed out waiting for data",
                                  task_name)
                    return None
            else:
                _LOGGER.debug(">> ArcamSolo._read_response() %s: waiting for data", task_name)
                raw_response = await responder_task
        except (EOFError, TimeoutError):
            # Connection closed
            _LOGGER.debug(">> ArcamSolo._read_response() %s: connection closed", task_name)
            return None
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.error(">> ArcamSolo._read_response() %s: exception: %s", task_name, exc)
            return None
        if raw_response is None:  # task cancelled
            return None
        # Arcam works in bytes so we just pass the bytes around
        _LOGGER.debug(">> ArcamSolo._read_response() %s: received response: %s",
                      task_name,
                      raw_response)
        return raw_response

    async def send_raw_command(self,
                               command: str,
                               data: list[bytes],
                               zone: bytes=b'\x01',
                               rate_limit=True):
        """Send a raw command to the Arcam."""
        _LOGGER.debug(
            '>> ArcamSolo.send_raw_command("%s", rate_limit=%s)',
            command,
            rate_limit,
        )
        if not self.available:
            raise RuntimeError("AVR connection not available")

        if rate_limit:
            # Rate limit commands
            command_delay = 0.1
            since_command = command_delay + 0.1
            if self._last_command:
                since_command = time.time() - self._last_command
            if since_command < command_delay:
                delay = command_delay - since_command
                _LOGGER.debug("delaying command for %.3f s", delay)
                await asyncio.sleep(command_delay - since_command)
        raw_command = COMMAND_CODES.get(command)
        raw_command = ARCAM_COMM_START + zone + raw_command + len(data).to_bytes(1, 'little')
        for b in data:
            raw_command += b
        raw_command += ARCAM_COMM_END
        _LOGGER.debug("sending command: %s", raw_command)
        self._writer.write(raw_command)
        await self._writer.drain()
        self._last_command = time.time()

    async def send_ir_command(self,
                              command: str):
        """Send an IR command to the Arcam."""
        ir_data = IR_COMMAND_CODES.get(command, None)
        if ir_data is None:
            raise ValueError("Command does not exist.")
        await self.send_raw_command(
            command="virtual_remote",
            data=[
                ir_data["system_code"].to_bytes(1, 'little'),
                ir_data["command_code"].to_bytes(1, 'little')
            ]
        )

    async def set_source(self,
                         source: str):
        """Set the source of the system."""
        await self.send_ir_command(
            SOURCE_IR_CONTROL_MAP.get(source)
        )

    async def set_volume(self,
                         volume: int):
        """Set the volume level of the system."""
        if volume > 72:
            raise ValueError("Max volume is 72.")
        await self.send_raw_command(
            command="volume",
            data=[
                volume.to_bytes(1, 'little')
            ]
        )

    async def mute_on(self):
        """Turn mute on."""
        await self.send_ir_command(
            command="mute_on"
        )

    async def mute_off(self):
        """Turn mute on."""
        await self.send_ir_command(
            command="mute_off"
        )

    async def turn_off(self):
        """Turn the unit off."""
        await self.send_ir_command(
            command="standby_on"
        )

    async def turn_on(self):
        """Turn the unit on."""
        # send the command twice as sometimes the device doesn't respond
        await self.send_ir_command(
            command="standby_off"
        )
        await self.send_ir_command(
            command="standby_off"
        )
