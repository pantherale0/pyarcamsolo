"""Arcam Solo commands."""

ARCAM_QUERY_COMMANDS = [
    "software_version",
    "rs232_version",
    "status",
    "source",
    "volume",
    "balance",
    "bass",
    "treble",
    "mute",
    "display_brightness",
    "stby_display_brightness"
]

ARCAM_COMM_START = b'\x21'
ARCAM_COMM_END = b'\x0D'

COMMAND_CODES = {
    "status": b'\x00',
    "source": b'\x01',
    "volume": b'\x02',
    "balance": b'\x04',
    "bass": b'\x05',
    "treble": b'\x06',
    "mute": b'\x08',
    "preset_select": b'\x13',
    "display_brightness": b'\x0A',
    "stby_display_brightness": b'\x16',
    "snooze": b'\x29',
    "sleep": b'\x31',
    "headphones": b'\x32',
    "tuner_type": b'\x37',
    "radio_station": b'\xDE',
    "radio_station_info": b'\xDF',
    "radio_programme_type": b'\xE6',
    "radio_rds_information": b'\xE7',
    "virtual_remote": b'\xE9',
    "cd_playback_state": b'\xEC',
    "cd_play_mode": b'\x54',
    "usb_playback_state": b'\x58',
    "usb_play_mode": b'\x59',
    "cdusb_total_track_time": b'\x55',
    "cdusb_total_playback_time": b'\x56',
    "preset_save": b'\xDC',
    "cdusb_current_track": b'\xE8',
    "usb_track_name": b'\x60',
    "usb_folder_name": b'\x61',
    "cdusb_playback_time": b'\xEB',
    "cd_disc_type": b'\xED',
    "time": b'\xF8',
    "rs232_version": b'\xF1',
    "software_version": b'\xF2'
}

ACCEPTED_ANSWER_CODES = ["status_update", "command_accepted_completed"]
ANSWER_CODES = {
    "status_update": b'\x00',
    "command_accepted_completed": b'\x01',
    "command_accepted_processing": b'\x02',
    "zone_invalid": b'\x82',
    "command_not_recognised": b'\x83',
    "parameter_not_recognised": b'\x84',
    "command_invalid_at_this_time": b'\x85',
    "invalid_data_length": b'\x86'
}

SOURCE_SELECTION_CODES = {
    b'\x00': "N/A",
    b'\x01': "FM",
    b'\x02': "DAB",
    b'\x03': "TAPE",
    b'\x04': "AV",
    b'\x05': "N/A",
    b'\x06': "N/A",
    b'\x07': "AM",
    b'\x08': "GAME",
    b'\x09': "USB",
    b'\x0A': "CD",
    b'\x0B': "TV",
    b'\x0C': "AUX"
}

SOURCE_IR_CONTROL_MAP = {
    "FM": "src_fm",
    "AM": "src_am",
    "DAB": "src_dab",
    "TAPE": "src_tape",
    "AV": "src_av",
    "GAME": "src_game",
    "USB": "src_usb",
    "CD": "src_cd",
    "TV": "src_tv",
    "AUX": "src_aux"
}

POWER_STATUS_CODES = {
    b'\x00': "Standby",
    b'\x01': "Power on",
    b'\x02': "Alarm",
    b'\x03': "Basic Menu",
    b'\x04': "N/A",
    b'\x05': "Clock Menu",
    b'\x06': "initialising"
}

DISPLAY_BRIGHTNESS_CODES = {
    b'\x00': "Off",
    b'\x01': "25%",
    b'\x02': "50%",
    b'\x03': "75%",
    b'\x04': "100%"
}

TUNER_MODULE_TYPE_CODES = {
    b'\x00': "UK DAB/FM/AM",
    b'\x01': "US AM/FM",
    b'\x02': "Japan",
    b'\x03': "EU"
}

CD_PLAYBACK_STATUS_CODES = {
    b'\x01': "Loading",
    b'\x02': "Playing",
    b'\x03': "Stopped",
    b'\x04': "Scanning Back",
    b'\x05': "Scanning Forward",
    b'\x08': "Tray Open / Empty",
    b'\x09': "Paused",
    b'\x0D': "Track Skipping"
}

USB_PLAYBACK_STATUS_CODES = {
    b'\x01': "Initialising",
    b'\x02': "Playing",
    b'\x03': "Stopped",
    b'\x04': "Scanning Back",
    b'\x05': "Scanning Forward",
    b'\x08': "No Device",
    b'\x09': "Paused",
    b'\x10': "Invalid File",
    b'\x11': "No Valid Files Present",
    b'\x0D': "Track Skipping"
}

IR_COMMAND_CODES = {
    "src_tv": {
        "system_code": 16,
        "command_code": 0
    },
    "src_av": {
        "system_code": 16,
        "command_code": 2
    },
    "src_dab": {
        "system_code": 16,
        "command_code": 3
    },
    "src_tape": {
        "system_code": 16,
        "command_code": 5
    },
    "src_cd": {
        "system_code": 16,
        "command_code": 7
    },
    "src_aux": {
        "system_code": 16,
        "command_code": 8
    },
    "standby": {
        "system_code": 16,
        "command_code": 12
    },
    "mute": {
        "system_code": 16,
        "command_code": 13
    },
    "volume_plus": {
        "system_code": 16,
        "command_code": 16
    },
    "volume_minus": {
        "system_code": 16,
        "command_code": 17
    },
    "bass_plus": {
        "system_code": 16,
        "command_code": 22
    },
    "bass_minus": {
        "system_code": 16,
        "command_code": 23
    },
    "treble_plus": {
        "system_code": 16,
        "command_code": 24
    },
    "treble_minus": {
        "system_code": 16,
        "command_code": 25
    },
    "balance_right": {
        "system_code": 16,
        "command_code": 26
    },
    "balance_left": {
        "system_code": 16,
        "command_code": 27
    },
    "src_am": {
        "system_code": 16,
        "command_code": 52
    },
    "src_fm": {
        "system_code": 16,
        "command_code": 53
    },
    "display_brightness": {
        "system_code": 16,
        "command_code": 59
    },
    "navigate_right": {
        "system_code": 16,
        "command_code": 80
    },
    "navigate_left": {
        "system_code": 16,
        "command_code": 81
    },
    "menu": {
        "system_code": 16,
        "command_code": 82
    },
    "navigate_down": {
        "system_code": 16,
        "command_code": 85
    },
    "navigate_up": {
        "system_code": 16,
        "command_code": 86
    },
    "ok": {
        "system_code": 16,
        "command_code": 87
    },
    "alarm_1_toggle": {
        "system_code": 16,
        "command_code": 113
    },
    "alarm_2_toggle": {
        "system_code": 16,
        "command_code": 114
    },
    "alarm_3_toggle": {
        "system_code": 16,
        "command_code": 115
    },
    "alarm_4_toggle": {
        "system_code": 16,
        "command_code": 116
    },
    "snooze": {
        "system_code": 16,
        "command_code": 117
    },
    "sleep": {
        "system_code": 16,
        "command_code": 118
    },
    "mute_on": {
        "system_code": 16,
        "command_code": 119
    },
    "mute_off": {
        "system_code": 16,
        "command_code": 120
    },
    "standby_off": {
        "system_code": 16,
        "command_code": 123
    },
    "standby_on": {
        "system_code": 16,
        "command_code": 124
    },
}
