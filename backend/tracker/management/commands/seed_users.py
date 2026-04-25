"""Seeds only the demo users — no sample sheep.
Use this for a clean live demo where you'll register sheep manually.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo users only (admin1, inspector1, transporter1). No sample data."

    def handle(self, *args, **opts):
        users = [
            ("admin1", "admin", True),
            ("inspector1", "inspector", False),
            ("transporter1", "transporter", False),
        ]
        for username, role, is_staff in users:
            u, created = User.objects.get_or_create(
                username=username,
                defaults={"role": role, "is_staff": is_staff},
            )
            u.role = role
            u.is_staff = is_staff
            u.set_password("password123")
            u.save()
            self.stdout.write(f"  user: {username} ({role}) {'[new]' if created else '[updated]'}")
        self.stdout.write(self.style.SUCCESS("Demo users ready. DB is empty — register sheep via the app."))
