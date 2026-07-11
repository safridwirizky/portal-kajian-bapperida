from io import BytesIO
from pathlib import Path

from drive_types import DriveFile

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload


class GoogleDrive:

    SCOPES = [
        "https://www.googleapis.com/auth/drive"
    ]

    BASE_DIR = Path(__file__).resolve().parent.parent

    CREDENTIALS_FILE = BASE_DIR / "credentials.json"

    TOKEN_FILE = BASE_DIR / "token.json"

    def __init__(self):

        self._service = None

    # ==========================================================================
    # Authentication
    # ==========================================================================

    @property
    def service(self):

        if self._service is None:

            self._service = self._authenticate()

        return self._service

    # ==========================================================================
    # Folder
    # ==========================================================================

    def get_or_create_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str:

        folder_id = self._find_folder(
            name,
            parent_id,
        )

        if folder_id:

            return folder_id

        return self._create_folder(
            name,
            parent_id,
        )

    # ==========================================================================
    # File
    # ==========================================================================

    def upload_file(
        self,
        folder_id: str,
        file: DriveFile,
    ) -> str:

        media = MediaIoBaseUpload(
            fd=file.stream,
            mimetype=file.mimetype,
            resumable=True,
        )

        metadata = {
            "name": file.filename,
            "parents": [folder_id],
        }

        response = (
            self.service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id",
            )
            .execute()
        )

        return response["id"]

    def delete_file(
        self,
        file: DriveFile,
    ) -> None:

        self.service.files().delete(
            fileId=file.id,
        ).execute()

    # ==========================================================================
    # Private Methods
    # ==========================================================================

    def _find_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str | None:

        safe_name = self._escape_query(name)

        query = [
            "mimeType='application/vnd.google-apps.folder'",
            "trashed=false",
            f"name='{safe_name}'",
        ]

        if parent_id:
            query.append(
                f"'{parent_id}' in parents"
            )

        response = (
            self.service.files()
            .list(
                q=" and ".join(query),
                fields="files(id, name)",
                pageSize=1,
            )
            .execute()
        )

        folders = response.get(
            "files",
            []
        )

        if not folders:
            return None

        return folders[0]["id"]

    def _create_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str:

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:

            metadata["parents"] = [parent_id]

        folder = (
            self.service.files()
            .create(
                body=metadata,
                fields="id"
            )
            .execute()
        )

        return folder["id"]
    
    def _escape_query(self, value: str) -> str:
        return value.replace("'", "\\'")
    
    def _authenticate(self):

        credentials = None

        if self.TOKEN_FILE.exists():

            credentials = Credentials.from_authorized_user_file(
                self.TOKEN_FILE,
                self.SCOPES
            )

        if credentials is None or not credentials.valid:

            if (
                credentials
                and credentials.expired
                and credentials.refresh_token
            ):

                credentials.refresh(
                    Request()
                )

            else:

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE,
                    self.SCOPES
                )

                credentials = flow.run_local_server(
                    port=0
                )

            self._save_token(
                credentials
            )

        return build(
            "drive",
            "v3",
            credentials=credentials
        )

    def _save_token(
        self,
        credentials
    ):

        self.TOKEN_FILE.write_text(
            credentials.to_json()
        )
