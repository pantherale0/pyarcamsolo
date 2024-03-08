#!/usr/bin/env python3
""" Pioneer AVR testing script. """
# pylint: disable=import-error,broad-except

import asyncio
import logging
import sys
import getopt

from pyarcamsolo import ArcamSolo

_LOGGER = logging.getLogger(__name__)


async def main(argv):
    """ Main loop. """
    _LOGGER.debug(">> main()")

    host = ""
    try:
        opts, _ = getopt.getopt(argv, "hp:v", ["host=", "port="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--host"):
            host = arg
        if opt in ("-p", "--port"):
            port = arg

    if host == "" or port == "":
        _LOGGER.fatal("Host or port not specified.")
        sys.exit(2)

    arcam = ArcamSolo(
        host=host,
        port=int(port)
    )

    try:
        await arcam.connect()
    except Exception as e:  # pylint: disable=invalid-name
        print(f"Could not connect to arcam: {type(e).__name__}: {e.args}")
        return False


    # await arcam.turn_on()
    while True:
        try:
            # await arcam.send_ir_command("volume_plus")
            await asyncio.sleep(10)
            for z in arcam.zones.items():
                for a in z[1].items():
                    print(f"{z[0]}: {a[0]} - {a[1]}")
        except KeyboardInterrupt:
            # await arcam.turn_off()
            await asyncio.sleep(5)
            await arcam.shutdown()
            break

    return True

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    rc = asyncio.run(main(sys.argv[1:]))  ## pylint: disable=invalid-name
    exit(0 if rc else 1)
