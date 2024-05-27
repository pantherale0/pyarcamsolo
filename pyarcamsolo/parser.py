"""Arcam Parser Helper."""

import logging

from .commands import (
    SOURCE_SELECTION_CODES,
    ANSWER_CODES,
    ACCEPTED_ANSWER_CODES,
    COMMAND_CODES,
    POWER_STATUS_CODES,
    CD_PLAYBACK_STATUS_CODES,
    RADIO_QUERY_COMMANDS,
    RADIO_MPEG_MODES
)

_LOGGER = logging.getLogger(__name__)
CURRENT_SOURCE = ""

def get_answer_code(ac: bytes) -> str:
    """Return the answer code from the byte."""
    return (list(ANSWER_CODES.keys())[list(ANSWER_CODES.values()).index(ac)])

def get_command_code(cc: bytes) -> str:
    """Return the command code from the byte."""
    return (list(COMMAND_CODES.keys())[list(COMMAND_CODES.values()).index(cc)])

def get_radio_query_code(d1: bytes) -> str:
    """Return the command name from the byte."""
    return (list(RADIO_QUERY_COMMANDS.keys())[list(RADIO_QUERY_COMMANDS.values()).index(d1)])

def parse_response(response: bytes) -> dict | list[dict] | None:
    """Convert response bytes into a tuple for the main module to handle."""
    global CURRENT_SOURCE
    output = {
        "k": "",
        "v": None,
        "z": None
    }
    # Ignore start byte
    output["z"] = response[1:2][0] # Second byte is zone
    cc = response[2:3] # Third byte is command code
    ac = response[3:4] # Forth byte is answer code
    size = response[4:5][0] # Fith byte is length
    data = response[5:(5+size)] # Sixth byte+ is data

    cc = get_command_code(cc)
    ac = get_answer_code(ac)
    # check answer code is valid
    if ac not in ACCEPTED_ANSWER_CODES:
        if ac == "command_invalid_at_this_time":
            _LOGGER.warning("Command %s is unavailable in current state. Will retry later.", cc)
            return None
        raise ValueError(
            f"Provided response for {cc} is invalid at this time: {get_answer_code(ac)}"
        )
    _LOGGER.debug(">> Decoded response as command %s", cc)

    if cc == "volume":
        output["k"] = cc
        output["v"] = data[0]
    elif cc == "mute":
        output["k"] = "muted"
        output["v"] = bool(data[0])
    elif cc == "source":
        output["k"] = "source"
        output["v"] = SOURCE_SELECTION_CODES.get(data)
        CURRENT_SOURCE = output["v"]
    elif cc == "status":
        output["k"] = "power"
        output["v"] = POWER_STATUS_CODES.get(data)
    elif cc == "software_version":
        output["k"] = cc
        output["v"] = f"{data[0]}.{data[1]}"
    elif cc == "rs232_version":
        output["k"] = cc
        output["v"] = f"{data[0]}.{data[1]}"
    elif cc == "balance":
        output["k"] = cc
        output["v"] = (data[0])-100
    elif cc == "bass":
        output["k"] = cc
        output["v"] = (int.from_bytes(data[0:])-100)*2
    elif cc == "treble":
        output["k"] = cc
        output["v"] = (int.from_bytes(data[0:])-100)*2
    elif cc == "display_brightness":
        output["k"] = cc
        output["v"] = data[0]
    elif cc == "stby_display_brightness":
        output["k"] = "standby_display_brightness"
        output["v"] = data[0]
    elif cc == "cd_playback_state":
        output["k"] = cc
        output["v"] = CD_PLAYBACK_STATUS_CODES.get(data, "Unknown")
    elif cc == "cdusb_playback_time":
        output["k"] = "current_track_position"
        hour = int.from_bytes(data[0:1]) * 3600
        minute = int.from_bytes(data[1:2]) * 60
        sec = int.from_bytes(data[2:3])
        output["v"] = hour+minute+sec
    elif cc == "cdusb_total_track_time":
        output["k"] = "current_track_duration"
        hour = int.from_bytes(data[0:1]) * 3600
        minute = int.from_bytes(data[1:2]) * 60
        sec = int.from_bytes(data[2:3])
        output["v"] = hour+minute+sec
    elif cc == "cd_play_mode":
        binary = bin(int(data.hex(), 16))[2:]
        if len(binary) == 4:
            shuffle_value = int(binary[1])
            repeat_value = binary[2:4]
            program_value = int(binary[0])
        elif len(binary) == 3:
            shuffle_value = int(binary[0])
            repeat_value = binary[1:3]
            program_value = "0"
        elif len(binary) == 2:
            repeat_value = binary[0:1]
            program_value = 0
            shuffle_value = 0
        else:
            repeat_value = "0"
            program_value = 0
            shuffle_value = 0
        # sort repeat value properly
        if repeat_value == "0":
            repeat_value = "off"
        elif repeat_value == "1":
            repeat_value = "single"
        elif repeat_value == "11":
            repeat_value = "all"
        return [
            {
                "k": "repeat",
                "v": repeat_value,
                "z": output["z"]
            },
            {
                "k": "shuffle",
                "v": bool(shuffle_value),
                "z": output["z"]
            },
            {
                "k": "program",
                "v": bool(program_value),
                "z": output["z"]
            }
        ]
    elif cc == "cdusb_current_track":
        return parse_cdusb_current_track(
            z=output["z"],
            b=data
        )
    elif cc == "radio_station_info":
        return parse_radio_station_info(
            z=output["z"],
            b=data
        )
    elif cc == "radio_station":
        output["k"] = "radio_station"
        output["v"] = data.decode("ascii")
    elif cc == "snooze" or cc == "sleep":
        output["k"] = cc
        output["v"] = int.from_bytes(data[0:])
    elif cc == "headphones":
        output["k"] = cc
        output["v"] = bool(int.from_bytes(data[0:]))

    return output if output["v"] is not None else None

def parse_radio_station_info(z: int, b: bytes) -> list[dict]:
    """Parse radio ration information."""
    global CURRENT_SOURCE
    d1 = get_radio_query_code(b[0:1])
    if d1 == "request_station_frequency":
        mhz = int.from_bytes(b[1:2])
        khz = int.from_bytes(b[2:3])
        if CURRENT_SOURCE == "AM":
            val = int(str(mhz).zfill(2) + str(khz).zfill(2))
        elif CURRENT_SOURCE == "FM":
            val = int(str(mhz).zfill(2) + str(khz).zfill(2))/100
        else:
            val = None
        return {
            "k": "radio_frequency",
            "v": val,
            "z": z
        }
    elif d1 == "request_station_signal":
        return {
            "k": "radio_signal",
            "v": int.from_bytes(b[1:2]),
            "z": z
        }
    elif d1 == "request_mpeg_mode":
        return {
            "k": "dab_mpeg_mode",
            "v": RADIO_MPEG_MODES.get(b[1:2], None),
            "z": z
        }
    elif d1 == "request_data_rate":
        return {
            "k": "dab_data_rate",
            "v": int.from_bytes(b[1:2]),
            "z": z
        }
    return None

def parse_cdusb_current_track(z: int, b: bytes) -> list[dict]:
    """Parse CD / USB Current Track info."""
    current_folder = int.from_bytes(b[0:1])
    total_folder = int.from_bytes(b[1:2])
    msb_current_track = int.from_bytes(b[2:3])
    lsb_current_track = int.from_bytes(b[3:4])
    msb_total_track = int.from_bytes(b[4:5])
    lsb_total_track = int.from_bytes(b[5:6])
    return [
        {
            "k": "current_folder",
            "v": current_folder,
            "z": z
        },
        {
            "k": "total_folder",
            "v": total_folder,
            "z": z
        },
        {
            "k": "msb_current_track",
            "v": msb_current_track,
            "z": z
        },
        {
            "k": "lsb_current_track",
            "v": lsb_current_track,
            "z": z
        },
        {
            "k": "msb_total_track",
            "v": msb_total_track,
            "z": z
        },
        {
            "k": "lsb_total_track",
            "v": lsb_total_track,
            "z": z
        },
    ]
