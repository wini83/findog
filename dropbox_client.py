import string

import dropbox


class DropboxClient:
    _api_key: string = None
    _dbx: dropbox.Dropbox = None

    def __init__(self, api_key: string):
        self._api_key = api_key
        self._dbx = dropbox.Dropbox(self._api_key)

    @property
    def api_key(self):
        return self._api_key

    def retrieve_file(self, file_path: string) -> bytes:
        metadata, res = self._dbx.files_download(path=file_path)
        return res.content

    def commit_file(self, file: bytes, file_path: string):
        pass
