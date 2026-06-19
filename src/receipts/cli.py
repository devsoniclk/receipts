"""CLI interface for receipts verification."""

from __future__ import annotations

import sys

import click

from receipts import verify


@click.group()
def cli() -> None:
    """receipts — verify that agents actually did their job."""


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Machine-readable JSON output.")
@click.option("--workdir", type=click.Path(), default=None, help="Override working directory.")
def verify_cmd(spec_file: str, as_json: bool, workdir: str | None) -> None:
    """Verify a task spec against real-world state.

    SPEC_FILE is the path to a YAML task specification.
    """
    try:
        verdict = verify(spec_file, workdir=workdir)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(2)
    except ValueError as e:
        click.echo(f"Error: Invalid spec: {e}", err=True)
        sys.exit(2)

    if as_json:
        click.echo(verdict.to_json())
    else:
        try:
            from rich.console import Console
            from rich.text import Text

            console = Console()
            report = verdict.to_report()

            for line in report.split("\n"):
                if line.startswith("✅"):
                    console.print(Text(line, style="bold green"))
                elif line.startswith("❌"):
                    console.print(Text(line, style="bold red"))
                elif line.startswith("  [✗]"):
                    console.print(Text(line, style="red"))
                elif line.startswith("  [✓]"):
                    console.print(Text(line, style="green"))
                else:
                    console.print(line)
        except ImportError:
            click.echo(verdict.to_report())

    sys.exit(0 if verdict.passed else 1)


# Register the command with a name that matches the CLI usage
cli.add_command(verify_cmd, "verify")


if __name__ == "__main__":
    cli()
