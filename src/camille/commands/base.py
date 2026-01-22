from argparse import ArgumentParser, Namespace

from sqlalchemy.ext.asyncio.engine import AsyncEngine


class BaseCommand:
    name: str

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add command-specific arguments to the parser."""
        pass

    async def handle(self, engine: AsyncEngine, args: Namespace) -> None:
        """Handle the command with the given arguments."""
        pass
