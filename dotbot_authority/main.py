#!/usr/bin/env python3

"""Main module of the DotBot Authority."""

import asyncio
import os
import sys

import click

from dotbot_authority.logger import setup_logging
from dotbot_authority.authority import Authority


@click.command()
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error"]),
    default="info",
    help="Logging level. Defaults to info",
)
@click.option(
    "--log-output",
    type=click.Path(),
    default=os.path.join(os.getcwd(), "dotbot_authority.log"),
    help="Filename where logs are redirected",
)
def main(
    log_level,
    log_output,
):
    """DotBotAuthority, central server for managing DotBots."""
    print(f"Welcome to the DotBot Authority.")

    setup_logging(log_output, log_level, ["console", "file"])
    try:
        authority = Authority()
        asyncio.run(authority.run())
    except (SystemExit, KeyboardInterrupt):
        sys.exit(0)


if __name__ == "__main__":
    main()
