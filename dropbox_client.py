import string

import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import WriteMode


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

    def commit_file(self, file_path_loc: string, file_path: string):
        with open(file_path_loc, 'rb') as f:
            # We use WriteMode=overwrite to make sure that the settings in the file
            # are changed on upload
            f_bytes = f.read()
            return self.commit_file_bytes(f_bytes,file_path)



    def commit_file_bytes(self, file_local: bytes, file_path: string):
        try:
            self._dbx.files_upload(file_local, file_path, mode=WriteMode('overwrite'))
            return True
        except ApiError as err:
            # This checks for the specific error where a user doesn't have
            # enough Dropbox space quota to upload this file
            if (err.error.is_path() and
                    err.error.get_path().reason.is_insufficient_space()):
                print("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                print(err.user_message_text)
            else:
                print(err)
            return False
