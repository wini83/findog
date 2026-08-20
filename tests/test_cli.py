from click.testing import CliRunner

import main
from findog_legacy_adapter import PaymentCodeError


def test_cli_loads_workbook_options_from_yaml(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'excel_dropbox_path: "/legacy.xlsm"\nmonitored_sheets:\n  Home: ["C"]\n',
        encoding="utf-8",
    )
    captured = {}

    def fake_loader(
        access_token, dropbox_path, monitored_sheets, interpret_codes=False
    ):
        captured.update(
            access_token=access_token,
            dropbox_path=dropbox_path,
            monitored_sheets=monitored_sheets,
            interpret_codes=interpret_codes,
        )
        return type("PaymentBook", (), {"payment_list": [object()]})()

    monkeypatch.setattr(main, "load_payment_book_from_dropbox", fake_loader)

    result = CliRunner().invoke(
        main.main,
        ["--dropbox-token", "token", "--config", str(config_path)],
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "access_token": "token",
        "dropbox_path": "/legacy.xlsm",
        "monitored_sheets": {"Home": ["C"]},
        "interpret_codes": False,
    }
    assert result.output == "Loaded 1 payment records.\n"


def test_cli_displays_payment_code_errors(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'excel_dropbox_path: "/legacy.xlsm"\nmonitored_sheets:\n  Home: ["C"]\n',
        encoding="utf-8",
    )

    def fake_loader(*args, **kwargs):
        raise PaymentCodeError("Invalid code in cell Home!C1.")

    monkeypatch.setattr(main, "load_payment_book_from_dropbox", fake_loader)

    result = CliRunner().invoke(
        main.main,
        ["--dropbox-token", "token", "--config", str(config_path)],
    )

    assert result.exit_code == 1
    assert result.output == "Error: Invalid code in cell Home!C1.\n"
