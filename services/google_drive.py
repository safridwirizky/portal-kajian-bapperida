from io import BytesIO
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .drive_types import DriveFile


class GoogleDrive:

    _ROOT_FOLDER_NAME = "Portal Kajian"

    SCOPES = [
        "https://www.googleapis.com/auth/drive",
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
        """Mengambil folder jika sudah ada, atau membuat folder baru."""

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
        """Selalu membuat folder baru."""

        return self._create_folder(
            name=name,
            parent_id=parent_id,
        )
    
    def create_kajian_folder(
        self,
        tahun: int,
        judul: str,
    ) -> str:
        """Membuat struktur folder kajian dan mengembalikan ID folder kajian."""

        portal_folder_id = self.get_or_create_folder(
            self._ROOT_FOLDER_NAME,
        )

        tahun_folder_id = self.get_or_create_folder(
            str(tahun),
            parent_id=portal_folder_id,
        )

        return self.create_folder(
            name=judul,
            parent_id=tahun_folder_id,
        )

    # ==========================================================================
    # File
    # ==========================================================================

    def upload(
        self,
        folder_id: str,
        file: DriveFile,
    ) -> str:
        """Mengunggah file ke folder Google Drive."""

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
    
    def download(
        self,
        file_id: str,
    ) -> BytesIO:
        """Mengunduh file dari Google Drive."""

        request = (
            self.service.files()
            .get_media(
                fileId=file_id,
            )
        )

        stream = BytesIO()

        downloader = MediaIoBaseDownload(
            stream,
            request,
        )

        done = False

        while not done:
            _, done = downloader.next_chunk()

        stream.seek(0)

        return stream

    def delete(
        self,
        file_id: str,
    ) -> None:
        """Menghapus file atau folder."""

        (
            self.service.files()
            .delete(
                fileId=file_id,
            )
            .execute()
        )

    # ==========================================================================
    # Private Methods
    # ==========================================================================

    def _find_folder(
        self,
        name: str,
        parent_id: str | None = None,
    ) -> str | None:
        """Mencari folder berdasarkan nama."""

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
        """Membuat folder baru."""

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:
            metadata["parents"] = [parent_id]

        response = (
            self.service.files()
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

    def _authenticate(self):

        credentials = None

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

        return build(
            "drive",
            "v3",
            credentials=credentials,
        )

    def _save_token(
        self,
        credentials,
    ) -> None:

        self.TOKEN_FILE.write_text(
            credentials.to_json(),
        )
