from .google_drive import GoogleDrive
from .drive_types import DriveFile

drive = GoogleDrive()

__all__ = ["drive", "DriveFile"]
