from enum import Enum


class Operation(Enum):
    Sync_UpStream = "sync_upstream"
    Sync_Download = "sync_download"

    @staticmethod
    def to_enum(value: str) -> "Operation":
        try:
            return Operation(value.lower())
        except Exception:
            raise ValueError(f"'{value}' is invalid Operation")
