from io import BytesIO
from pathlib import Path
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseUpload

from .drive_types import DriveFile


class GoogleDrive:

    ROOT_FOLDER_NAME = "Portal Kajian"

    SCOPES = (
        "https://www.googleapis.com/auth/drive",
    )

    BASE_DIR = Path(__file__).resolve().parent.parent

    CREDENTIALS_FILE = BASE_DIR / "credentials.json"

    TOKEN_FILE = BASE_DIR / "token.json"

    def __init__(self) -> None:
        self._credentials: Credentials | None = None
        self._service: Resource | None = None

    # ==========================================================================
    # Service
    # ==========================================================================

    @property
    def service(self) -> Resource:

        if self._service is None:
            self._service = build(
                "drive",
                "v3",
                credentials=self.credentials,
            )

        return self._service

    @property
    def credentials(self) -> Credentials:

        if self._credentials is None:
            self._credentials = self._authenticate()

        return self._credentials

    def _files(self):
        return self.service.files()

    # ==========================================================================
    # Folder
    # ==========================================================================

    def create_kajian_folder(
        self,
        tahun: int,
        judul: str,
    ) -> str:
        """Membuat struktur folder kajian."""

        portal_folder_id = self.get_or_create_folder(
            self.ROOT_FOLDER_NAME,
        )

        tahun_folder_id = self.get_or_create_folder(
            str(tahun),
            parent_id=portal_folder_id,
        )

        return self.create_folder(
            judul,
            parent_id=tahun_folder_id,
        )

    def get_or_create_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str:

        folder_id = self._find_folder(
            name=name,
            parent_id=parent_id,
        )

        if folder_id:
            return folder_id

        return self._create_folder(
            name=name,
            parent_id=parent_id,
        )

    def create_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str:

        return self._create_folder(
            name=name,
            parent_id=parent_id,
        )

    # ==========================================================================
    # File
    # ==========================================================================

    def upload(
        self,
        folder_id: str,
        file: DriveFile,
    ) -> str:

        media = MediaIoBaseUpload(
            fd=file.stream,
            mimetype=file.mimetype,
            resumable=True,
        )

        response = (
            self._files()
            .create(
                body={
                    "name": file.filename,
                    "parents": [folder_id],
                },
                media_body=media,
                fields="id",
            )
            .execute()
        )

        return response["id"]

    def download(
        self,
        file_id: str,
    ) -> BytesIO:
        """Mengunduh file dari Google Drive."""

        credentials = self.credentials

        if (
            credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(
                Request(),
            )

            self._save_token(
                credentials,
            )

        response = requests.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={
                "alt": "media",
            },
            headers={
                "Authorization": (
                    f"Bearer {credentials.token}"
                ),
            },
            timeout=60,
        )

        try:
            response.raise_for_status()

        except requests.HTTPError as exc:
            raise RuntimeError(
                f"Google Drive mengembalikan HTTP {exc.response.status_code}"
            ) from exc

        return BytesIO(
            response.content,
        )

    def delete_file(
        self,
        file_id: str,
    ) -> None:
        """Menghapus file dari Google Drive."""

        self._delete(
            file_id,
        )

    def delete_folder(
        self,
        folder_id: str,
    ) -> None:
        """Menghapus folder dari Google Drive."""

        parent_folder_id = self._get_parent_folder_id(
            folder_id,
        )

        self._delete(
            folder_id,
        )

        if (
            parent_folder_id
            and self._is_folder_empty(parent_folder_id)
        ):
            self._delete(
                parent_folder_id,
            )

    # ==========================================================================
    # Private
    # ==========================================================================

    def _delete(
        self,
        resource_id: str,
    ) -> None:
        """Menghapus resource Google Drive."""

        (
            self._files()
            .delete(
                fileId=resource_id,
            )
            .execute()
        )
    
    def _is_folder_empty(
        self,
        folder_id: str,
    ) -> bool:
        """Mengembalikan True jika folder tidak memiliki isi."""

        response = (
            self._files()
            .list(
                q=(
                    f"'{folder_id}' in parents "
                    "and trashed=false"
                ),
                fields="files(id)",
                pageSize=1,
            )
            .execute()
        )

        return not response.get(
            "files",
            [],
        )

    def _get_parent_folder_id(
        self,
        folder_id: str,
    ) -> str | None:
        """Mengambil parent folder."""

        response = (
            self._files()
            .get(
                fileId=folder_id,
                fields="parents",
            )
            .execute()
        )

        parents = response.get(
            "parents",
            [],
        )

        if not parents:
            return None

        return parents[0]
    
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
            self._files()
            .list(
                q=" and ".join(query),
                fields="files(id)",
                pageSize=1,
            )
            .execute()
        )

        folders = response.get(
            "files",
            [],
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

        response = (
            self._files()
            .create(
                body=metadata,
                fields="id",
            )
            .execute()
        )

        return response["id"]

    @staticmethod
    def _escape_query(
        value: str,
    ) -> str:

        return value.replace(
            "'",
            "\\'",
        )

    def _authenticate(
        self,
    ) -> Credentials:

        credentials: Credentials | None = None

        if self.TOKEN_FILE.exists():
            credentials = Credentials.from_authorized_user_file(
                self.TOKEN_FILE,
                self.SCOPES,
            )

        if credentials is None or not credentials.valid:

            if (
                credentials
                and credentials.expired
                and credentials.refresh_token
            ):
                credentials.refresh(
                    Request(),
                )

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CREDENTIALS_FILE,
                    self.SCOPES,
                )

                credentials = flow.run_local_server(
                    port=0,
                )

            self._save_token(
                credentials,
            )

        return credentials

    def _save_token(
        self,
        credentials: Credentials,
    ) -> None:

        self.TOKEN_FILE.write_text(
            credentials.to_json(),
        )
