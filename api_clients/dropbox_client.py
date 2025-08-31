"""Dropbox client wrapper for downloading and uploading files."""

import string

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode
from loguru import logger

from api_clients.client import Client


class DropboxClient(Client):
    """Light wrapper over the Dropbox SDK used by the pipeline."""

    _api_key: string = None
    _dbx: dropbox.Dropbox = None

    def login(self):
        pass

    def __init__(self, api_key: string):
        """Initialize Dropbox SDK client with the given API key."""
        self._api_key = api_key
        self._dbx = dropbox.Dropbox(self._api_key)

    @property
    def api_key(self):
        """Return configured API key."""
        return self._api_key

    def retrieve_file(self, file_path: string) -> bytes:
        """Download a file from Dropbox and return its bytes."""
        metadata, res = self._dbx.files_download(path=file_path)
        return res.content

    def commit_file(self, file_path_loc: string, file_path: string):
        """Upload a local file to Dropbox path (overwrite)."""
        with open(file_path_loc, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            f_bytes = f.read()
            return self.commit_file_bytes(f_bytes, file_path)

    def commit_file_bytes(self, file_local: bytes, file_path: string):
        """Upload bytes to Dropbox path. Returns True on success."""
        try:
            self._dbx.files_upload(file_local, file_path, mode=WriteMode('overwrite'))
            return True
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (
                err.error.is_path()
                and err.error.get_path().reason.is_insufficient_space()
            ):
                logger.exception("ERROR:dropbox Cannot back up; insufficient space.")
            elif err.user_message_text:
                logger.exception(err.user_message_text)
            else:
                logger.exception(err)
            return False
