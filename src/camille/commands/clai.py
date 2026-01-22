from argparse import ArgumentParser, Namespace
from os import environ

from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from camille.agents import Deps, create_agent
from camille.commands.base import BaseCommand
from camille.models import User


class Command(BaseCommand):
    name = "clai"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "-i",
            "--user-id",
            type=int,
            default=environ.get("CAMILLE_USER_ID"),
            help="User ID to use in the CLI",
        )

        parser.add_argument(
            "-u",
            "--username",
            type=str,
            default=environ.get("CAMILLE_USER_NAME"),
            help="Username to use in the CLI (overrides user ID)",
        )

    async def handle(self, engine: AsyncEngine, args: Namespace):
        async with AsyncSession(engine) as session:
            if args.user_id:
                user = await session.get(User, args.user_id)
                if not user:
                    print(f"User with ID {args.user_id} not found.")
                    return
            elif args.username:
                result = await session.exec(
                    select(User).where(User.username == args.username)
                )
                user = result.one_or_none()

                if not user:
                    print(f"User with username '{args.username}' not found.")
                    return
            else:
                print("Please provide either a user ID or a username to proceed.")
                return

        deps = Deps(user=user)

        await create_agent().to_cli(deps=deps)
