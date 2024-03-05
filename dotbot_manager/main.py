#!/usr/bin/env python3

"""Main module of the Dotbot Manager."""

import asyncio
import os
import sys

import click

from dotbot_manager.logger import setup_logging
from dotbot_manager.manager import Manager


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
    default=os.path.join(os.getcwd(), "dotbot_manager.log"),
    help="Filename where logs are redirected",
)
def main(
    log_level,
    log_output,
):
    """DotBotManager, central server for managing DotBots."""
    print(f"Welcome to the DotBot Manager.")

    setup_logging(log_output, log_level, ["console", "file"])
    try:
        manager = Manager()
        asyncio.run(manager.run())
    except (SystemExit, KeyboardInterrupt):
        sys.exit(0)


if __name__ == "__main__":
    main()
