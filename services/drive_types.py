from dataclasses import dataclass
from typing import BinaryIO, Protocol


class UploadLike(Protocol):
    filename: str
    stream: BinaryIO
    mimetype: str


@dataclass(slots=True, frozen=True, kw_only=True)
class DriveFile:
    id: str | None = None
    filename: str
    stream: BinaryIO | None = None
    mimetype: str
    size: int | None = None

    @classmethod
    def from_upload(
        cls,
        uploaded: UploadLike,
    ) -> "DriveFile":
        return cls(
            filename=uploaded.filename,
            stream=uploaded.stream,
            mimetype=uploaded.mimetype,
        )
