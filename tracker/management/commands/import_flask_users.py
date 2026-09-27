"""Import legacy Flask accounts without requiring users to reset their passwords."""
import base64
import sqlite3
from contextlib import closing
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Import users from the original instance/users.db Flask database"

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, default=Path("instance/users.db"))

    def handle(self, *args, **options):
        source = options["source"]
        if not source.is_file():
            raise CommandError(f"Legacy database not found: {source}")
        imported = 0
        skipped = 0
        with closing(sqlite3.connect(source)) as connection:
            try:
                rows = connection.execute("SELECT username, email, password_hash FROM user").fetchall()
            except sqlite3.Error as exc:
                raise CommandError("Legacy database has no readable user table") from exc
        User = get_user_model()
        for username, email, legacy_hash in rows:
            if User.objects.filter(username=username).exists():
                skipped += 1
                continue
            try:
                method, salt, digest = legacy_hash.split("$", 2)
                kind, algorithm, iterations = method.split(":", 2)
                if kind != "pbkdf2" or algorithm != "sha256":
                    raise ValueError("unsupported password format")
                django_hash = f"pbkdf2_sha256${int(iterations)}${salt}${base64.b64encode(bytes.fromhex(digest)).decode()}"
            except (ValueError, TypeError) as exc:
                raise CommandError(f"Unsupported password format for {username}; no account was imported for this user") from exc
            user = User(username=username, email=email, password=django_hash)
            user.save()
            imported += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {imported} account(s), skipped {skipped} existing account(s)."))
