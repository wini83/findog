from click.testing import CliRunner

import main


def test_cli_loads_workbook_options_from_yaml(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        'excel_dropbox_path: "/legacy.xlsm"\nmonitored_sheets:\n  Home: ["C"]\n',
        encoding="utf-8",
    )
    captured = {}

    def fake_loader(access_token, dropbox_path, monitored_sheets):
        captured.update(
            access_token=access_token,
            dropbox_path=dropbox_path,
            monitored_sheets=monitored_sheets,
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
    }
    assert result.output == "Loaded 1 payment records.\n"
