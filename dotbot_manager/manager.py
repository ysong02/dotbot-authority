import asyncio
import uvicorn

from dotbot_manager.server import api
from dotbot_manager.logger import LOGGER

class Manager:
    """Main class of the Dotbot Manager."""

    def __init__(self):
        self.logger = LOGGER.bind(context=__name__)
        self.logger.debug("Creating Manager instance")

    async def web(self):
        """Starts the web server application."""
        logger = LOGGER.bind(context=__name__)
        config = uvicorn.Config(api, port=8000, log_level="critical")
        server = uvicorn.Server(config)

        try:
            logger.info("Starting web server")
            await server.serve()
        except asyncio.exceptions.CancelledError:
            logger.info("Web server cancelled")
        else:
            logger.info("Stopping web server")
            raise SystemExit()

    async def run(self):
        """Launch the manager."""
        tasks = []
        try:
            tasks = [
                asyncio.create_task(self.web()),
            ]
            await asyncio.gather(*tasks)
        except SystemExit:
            self.logger.info("Stopping manager")
        finally:
            for task in tasks:
                task.cancel()
