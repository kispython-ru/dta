import enum


class Status(enum.IntEnum):
    Submitted = 0
    Checked = 2
    Failed = 3
    NotSubmitted = 4
    CheckedSubmitted = 5
    CheckedFailed = 6


