import datetime
from argparse import ArgumentParser, Namespace
from asyncio import run
from getpass import getpass
from typing import Optional

import argon2
import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from sqlmodel import Field, Session, SQLModel, create_engine

load_dotenv()

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str  # Hashed password with Argon2
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[datetime.date] = None


agent = Agent("bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0")

sqlite_file_name = "db.sqlite3"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


async def cmd_clai(args: Namespace):
    await agent.to_cli()


async def cmd_create_user(args: Namespace):
    while True:
        username = args.username or ""
        while not username:
            username = input("Username: ")

        password = ""
        while not password:
            password = getpass("Password: ")
        email = args.email or input("Email (optional): ") or None
        first_name = args.first_name or input("First name (optional): ") or None
        last_name = args.last_name or input("Last name (optional): ") or None
        birthdate_str = (
            args.birthdate or input("Birthdate (YYYY-MM-DD, optional): ") or None
        )
        birthdate = (
            datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
            if birthdate_str
            else None
        )

        confirm = ""
        while confirm.lower() not in ("y", "n"):
            print("\nPlease confirm the entered information:")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"First name: {first_name}")
            print(f"Last name: {last_name}")
            print(f"Birthdate: {birthdate}")
            confirm = input("Is this information correct? (y/n): ")

        if confirm.lower() == "y":
            break

    ph = argon2.PasswordHasher()
    password = ph.hash(password)

    user = User(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        birthdate=birthdate,
    )

    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)

    print(f"User {user.username} created with ID {user.id}")


async def amain():
    parser = ArgumentParser(description="Camille CLI")
    subparsers = parser.add_subparsers(title="subcommands", dest="command")

    clai_parser = subparsers.add_parser("clai", help="Launch the Camille AI CLI")
    clai_parser.set_defaults(func=cmd_clai)

    create_user_parser = subparsers.add_parser("createuser", help="Create a new user")
    create_user_parser.add_argument(
        "-u", "--username", type=str, help="Username for the new user"
    )
    create_user_parser.add_argument(
        "-e", "--email", type=str, help="Email address for the new user"
    )
    create_user_parser.add_argument(
        "-f", "--first-name", type=str, help="First name of the new user"
    )
    create_user_parser.add_argument(
        "-l", "--last-name", type=str, help="Last name of the new user"
    )
    create_user_parser.add_argument(
        "-b", "--birthdate", type=str, help="Birthdate (YYYY-MM-DD) of the new user"
    )
    create_user_parser.set_defaults(func=cmd_create_user)

    args = parser.parse_args()

    if (func := getattr(args, "func", None)) is not None:
        await func(args)
    else:
        parser.print_help()


def main():
    run(amain())
