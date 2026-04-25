"""Seeds demo users + a sample sheep with events. Idempotent."""
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from tracker.models import Sheep, Event
from tracker.blockchain import compute_hash, blockchain

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo users + one sample sheep with full timeline."

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
            self.stdout.write(f"  user: {username} ({role}) {'[new]' if created else ''}")

        admin = User.objects.get(username="admin1")
        inspector = User.objects.get(username="inspector1")
        transporter = User.objects.get(username="transporter1")

        if Sheep.objects.exists():
            self.stdout.write(self.style.WARNING("Sheep already present, skipping sample."))
            return

        sheep = Sheep.objects.create(
            tag_id=Sheep.generate_tag_id(),
            origin_country="Australia",
            import_date=date.today(),
            batch_number="BATCH-2026-001",
            created_by=admin,
        )
        reg_payload = {
            "type": "registration", "tag_id": sheep.tag_id,
            "origin_country": sheep.origin_country,
            "import_date": str(sheep.import_date),
            "batch_number": sheep.batch_number,
            "created_at": sheep.created_at.isoformat(),
        }
        sheep.registration_hash = compute_hash(reg_payload)
        sheep.registration_tx = blockchain.register_sheep(sheep.registration_hash, wait_receipt=False) or ""
        sheep.save()

        timeline = [
            (admin, "imported", "Port of Jeddah", "Cleared customs"),
            (inspector, "quarantine", "Quarantine Yard A", "21-day observation"),
            (inspector, "health_check", "Vet Clinic 3", "Vaccinated, healthy"),
            (transporter, "transported", "Highway 5 → Riyadh", "En route to market"),
            (transporter, "delivered", "Riyadh Distribution Center", "Handed to retailer"),
        ]
        for actor, status_, location, notes in timeline:
            ev = Event.objects.create(
                sheep=sheep, status=status_, location=location, notes=notes,
                actor=actor, actor_role=actor.role, data_hash="",
            )
            payload = {
                "type": "event", "tag_id": sheep.tag_id, "status": status_,
                "location": location, "notes": notes,
                "actor": actor.username, "timestamp": ev.timestamp.isoformat(),
            }
            ev.data_hash = compute_hash(payload)
            ev.blockchain_tx = blockchain.add_event(ev.data_hash, wait_receipt=False) or ""
            # Mark unverified for now — will flip to True after `python manage.py reanchor`
            # or automatically on the next /verify/ call once the tx mines.
            ev.on_chain_verified = False
            ev.save()

        self.stdout.write(self.style.SUCCESS(f"Seeded sheep {sheep.tag_id}"))
