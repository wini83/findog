"""Minimal Dropbox client used by the legacy-data adapter."""

import dropbox


class DropboxClient:
    """Download workbook bytes using a Dropbox access token."""

    def __init__(self, access_token: str):
        self._access_token = access_token
        self._dbx = dropbox.Dropbox(access_token)

    @property
    def access_token(self) -> str:
        """Return the access token supplied at construction time."""
        return self._access_token

    def retrieve_file(self, file_path: str) -> bytes:
        """Download a file from Dropbox and return its bytes."""
        _metadata, res = self._dbx.files_download(path=file_path)
        return res.content
