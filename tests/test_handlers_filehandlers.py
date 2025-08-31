from handlers.filehandlers import (
    FileCommitHandler,
    FileDownloadHandler,
    FileProcessHandler,
    NotifyOngoingHandler,
    SaveFileLocallyHandler,
)


class _StubDropboxClient:
    def __init__(self, data: bytes):
        self._data = data
        self.retrieve_calls = 0
        self.commit_calls = []

    def retrieve_file(self, path: str) -> bytes:
        self.retrieve_calls += 1
        return self._data

    def commit_file(self, local_path: str, remote_path: str) -> None:
        self.commit_calls.append((local_path, remote_path))


class _StubPushover:
    def __init__(self):
        self.errors = []
        self.notifications = []

    def error(self, message: str):
        self.errors.append(message)

    def notify(self, message: str):
        self.notifications.append(message)


class _StubPaymentBook:
    def __init__(self, monitored_sheets):
        self.monitored_sheets = monitored_sheets
        self.payment_list = []
        self.loaded_with = None

    def load_and_process(self, file_bytes: bytes):
        self.loaded_with = file_bytes

    def save_to_file(self, filename: str):
        # Pretend to save
        self.saved_as = filename


class _DummyPayment:
    def __init__(self, due_soon_or_overdue: bool):
        self.due_soon_or_overdue = due_soon_or_overdue


class _DummyPaymentListItem:
    def __init__(self, flag: bool):
        self.payment = _DummyPayment(flag)

    def __str__(self) -> str:
        return "Item" if self.payment.due_soon_or_overdue else "Nope"


class _StubContext:
    def __init__(self):
        self.dropbox_client = _StubDropboxClient(b"excel-bytes")
        self.pushover = _StubPushover()
        self.payment_book = _StubPaymentBook({"Home": ["C"]})
        self.excel_dropbox_path = "/remote/path.xlsx"
        self.excel_local_path = "/local/path.xlsx"
        self.file_object = None

    @property
    def excel_file_name(self):
        return "path.xlsx"


class _TerminalHandler:
    """A terminal handler to ensure the chain continues in tests."""

    def handle(self, context):
        return context


def test_file_download_handler_success():
    ctx = _StubContext()
    h = FileDownloadHandler()
    h.set_next(_TerminalHandler())
    out = h.handle(ctx)
    assert out.file_object == b"excel-bytes"
    assert ctx.dropbox_client.retrieve_calls == 1


def test_file_process_handler_success():
    ctx = _StubContext()
    ctx.file_object = b"wb-bytes"
    h = FileProcessHandler()
    h.set_next(_TerminalHandler())
    out = h.handle(ctx)
    assert out is ctx
    assert ctx.payment_book.loaded_with == b"wb-bytes"


def test_notify_ongoing_handler_builds_payload_and_notifies():
    ctx = _StubContext()
    ctx.payment_book.payment_list = [
        _DummyPaymentListItem(True),
        _DummyPaymentListItem(False),
    ]
    h = NotifyOngoingHandler()
    h.set_next(_TerminalHandler())
    h.handle(ctx)
    # One item should trigger notification
    assert len(ctx.pushover.notifications) == 1
    assert "Item" in ctx.pushover.notifications[0]


def test_save_file_locally_handler_calls_book_save():
    ctx = _StubContext()
    h = SaveFileLocallyHandler()
    h.set_next(_TerminalHandler())
    out = h.handle(ctx)
    assert out is ctx
    assert getattr(ctx.payment_book, "saved_as", None) == ctx.excel_local_path


def test_file_commit_handler_calls_dropbox_commit():
    ctx = _StubContext()
    h = FileCommitHandler()
    h.set_next(_TerminalHandler())
    out = h.handle(ctx)
    assert out is ctx
    assert ctx.dropbox_client.commit_calls == [
        (ctx.excel_local_path, ctx.excel_dropbox_path)
    ]
