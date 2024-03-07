<!-- markdownlint-disable MD033 MD041 -->

Python library for controlling Arcam Solo devices via a serial network bridge (ser2net)

Based on the implementation of [aiopioneer](https://github.com/crowbarz/aiopioneer)

## Features

- Implemented in asyncio.
- Maintains single continuous telnet session to ser2net server, reconnecting where required
- Eliminates need to poll as library will decode status messages from the Hi-Fi unit
- Supports power on/off
- Supports changing source
- Supports sending custom IR commands
- Automatically sets the time on startup (if still supported by your software version)

## Source list

| ID | Name
| -- | ---
| 00 | N/A
| 01 | FM
| 02 | DAB
| 03 | TAPE
| 04 | AV
| 05 | N/A
| 06 | N/A
| 07 | AM
| 08 | GAME
| 09 | USB
| 10 | CD
| 11 | TV
| 12 | AUX

## References

- aiopioneer: [https://github.com/crowbarz/aiopioneer](https://github.com/crowbarz/aiopioneer)
- rs232server: [https://github.com/arfoll/rs232server](https://github.com/arfoll/rs232server)
- Arcam Solo Mini rs232 protocol: [https://www.arcam.co.uk/ugc/tor/solomini/RS232/solomini_rs232.pdf](https://www.arcam.co.uk/ugc/tor/solomini/RS232/solomini_rs232.pdf)
