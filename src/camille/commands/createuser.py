import datetime
from argparse import ArgumentParser, Namespace
from getpass import getpass

import argon2
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from camille.commands.base import BaseCommand
from camille.models import User


class Command(BaseCommand):
    name = "createuser"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "-u", "--username", type=str, help="Username for the new user"
        )
        parser.add_argument(
            "-e", "--email", type=str, help="Email address for the new user"
        )
        parser.add_argument(
            "-f", "--first-name", type=str, help="First name of the new user"
        )
        parser.add_argument(
            "-l", "--last-name", type=str, help="Last name of the new user"
        )
        parser.add_argument(
            "-b", "--birthdate", type=str, help="Birthdate (YYYY-MM-DD) of the new user"
        )

    async def handle(self, engine: AsyncEngine, args: Namespace):
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

        async with AsyncSession(engine) as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)

        print(f"User {user.username} created with ID {user.id}")
