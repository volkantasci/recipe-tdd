"""
Django command to wait for database to be available
"""
import time
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError as DjangoOperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Django command to pause execution until database is available
    """

    def handle(self, *args, **options):
        """
        Handle the command
        """
        self.stdout.write("Waiting for database...")
        dp_up = False
        while not dp_up:
            try:
                self.check(databases=['default'])
                dp_up = True
            except (Psycopg2OperationalError, DjangoOperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
