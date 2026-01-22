from argparse import ArgumentParser
from asyncio import run
from os import environ

import logfire
from dotenv import load_dotenv

from camille.commands.clai import Command as ClaiCommand
from camille.commands.createuser import Command as CreateUserCommand
from camille.db import create_db_engine


async def amain():
    load_dotenv()

    logfire.configure(send_to_logfire="if-token-present")
    logfire.instrument_pydantic_ai()

    parser = ArgumentParser(description="Camille CLI")

    parser.add_argument(
        "-d",
        "--db-url",
        type=str,
        default=environ.get("CAMILLE_DB_URL"),
        help="Database URL",
    )

    subparsers = parser.add_subparsers(title="subcommands", dest="command")
    for command_class in [CreateUserCommand, ClaiCommand]:
        command = command_class()
        subparser = subparsers.add_parser(command.name, help=f"{command.name} command")
        command.add_arguments(subparser)
        subparser.set_defaults(func=command.handle)

    args = parser.parse_args()

    if not args.db_url:
        print("Database URL must be provided via --db-url or CAMILLE_DB_URL env var.")
        return
    engine = create_db_engine(args.db_url)

    if (func := getattr(args, "func", None)) is not None:
        await func(engine, args)
    else:
        parser.print_help()


def main():
    run(amain())
