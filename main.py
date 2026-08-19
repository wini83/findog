"""Development-only CLI for manually checking a legacy workbook."""

import json
import os
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv

from findog_legacy_adapter import load_payment_book_from_dropbox

load_dotenv()


@click.command()
@click.option(
    "--dropbox-token",
    envvar="DROPBOX_API_KEY",
    required=True,
    help="Dropbox access token; may be supplied through DROPBOX_API_KEY/.env.",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=lambda: Path(os.getenv("CONFIG_PATH", "config/config.yaml")),
    show_default=True,
    help="YAML file containing excel_dropbox_path and monitored_sheets.",
)
@click.option("--dropbox-path", help="Override the workbook path from YAML.")
@click.option(
    "--monitored-sheets",
    help='Override YAML with JSON, for example: {"Home": ["C", "I"]}.',
)
def main(
    dropbox_token: str,
    config_path: Path,
    dropbox_path: str | None,
    monitored_sheets: str | None,
) -> None:
    """Download a workbook and print the number of loaded payment records."""
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        raise click.ClickException("Configuration must be a YAML mapping.")

    if monitored_sheets:
        try:
            sheets = json.loads(monitored_sheets)
        except json.JSONDecodeError as exc:
            raise click.BadParameter(
                "must be valid JSON", param_hint="--monitored-sheets"
            ) from exc
    else:
        sheets = config.get("monitored_sheets")
    if not isinstance(sheets, dict) or not all(
        isinstance(name, str)
        and isinstance(columns, list)
        and all(isinstance(column, str) for column in columns)
        for name, columns in sheets.items()
    ):
        raise click.ClickException(
            "monitored_sheets must map sheet names to lists of column letters."
        )

    dropbox_path = dropbox_path or config.get("excel_dropbox_path")
    if not isinstance(dropbox_path, str) or not dropbox_path:
        raise click.ClickException(
            "Set excel_dropbox_path in config or pass --dropbox-path."
        )

    payment_book = load_payment_book_from_dropbox(dropbox_token, dropbox_path, sheets)
    click.echo(f"Loaded {len(payment_book.payment_list)} payment records.")


if __name__ == "__main__":
    main()
