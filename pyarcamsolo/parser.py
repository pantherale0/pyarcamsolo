"""Arcam Parser Helper."""

from .commands import (
    SOURCE_SELECTION_CODES,
    ANSWER_CODES,
    ACCEPTED_ANSWER_CODES,
    COMMAND_CODES,
    POWER_STATUS_CODES,
)

def get_answer_code(ac: bytes) -> str:
    """Return the answer code from the byte."""
    return (list(ANSWER_CODES.keys())[list(ANSWER_CODES.values()).index(ac)])

def get_command_code(cc: bytes) -> str:
    """Return the command code from the byte."""
    return (list(COMMAND_CODES.keys())[list(COMMAND_CODES.values()).index(cc)])

def parse_response(response: bytes) -> dict | None:
    """Convert response bytes into a tuple for the main module to handle."""
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
    # check answer code is valid
    if get_answer_code(ac) not in ACCEPTED_ANSWER_CODES:
        raise ValueError(
            f"Provided response for {cc} is invalid at this time: {get_answer_code(ac)}"
        )

    if cc == "volume":
        output["k"] = cc
        output["v"] = data[0]
    elif cc == "mute":
        output["k"] = "muted"
        output["v"] = bool(data[0])
    elif cc == "source":
        output["k"] = "source"
        output["v"] = SOURCE_SELECTION_CODES.get(data)
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
        output["v"] = bytes_to_int_with_offset(data[0], 2, 0x5D,
                                               range_upper_limit=14)
    elif cc == "treble":
        output["k"] = cc
        output["v"] = bytes_to_int_with_offset(data[0], 2, 0x5D,
                                               range_upper_limit=14)
    elif cc == "display_brightness":
        output["k"] = cc
        output["v"] = data[0]
    elif cc == "stby_display_brightness":
        output["k"] = "standby_display_brightness"
        output["v"] = data[0]

    return output if output["v"] is not None else None


def bytes_to_int_with_offset(b: bytes, offset: int, normalizer, range_upper_limit: int):
    """Converts bytes to an int with a provided offset"""
    i = int.from_bytes(b, byteorder='big', signed=True)
    # apply a base range from a normalizer
    i -= normalizer
    # now apply scaling using the offset provided
    i *= offset
    i -= range_upper_limit
    return i
