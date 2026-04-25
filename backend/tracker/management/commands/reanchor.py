"""Re-anchor any sheep / events that are missing a blockchain tx.

Useful when:
  - You seeded data while BLOCKCHAIN_DISABLED=True
  - The RPC was temporarily down when an event was created
  - You changed CONTRACT_ADDRESS and want to re-publish hashes

Run:
    python manage.py reanchor             # re-anchor all missing
    python manage.py reanchor --force     # re-anchor EVERYTHING (even already-anchored)
"""
import time
from django.core.management.base import BaseCommand

from tracker.models import Sheep, Event
from tracker.blockchain import compute_hash, blockchain


class Command(BaseCommand):
    help = "Re-anchor sheep registrations and events whose data_hash is not on-chain."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Re-anchor every event, even if already verified.")
        parser.add_argument("--sleep", type=float, default=2.0,
                            help="Seconds to sleep between txs (avoid nonce collisions).")

    def handle(self, *args, **opts):
        if blockchain.disabled:
            self.stderr.write(self.style.ERROR(
                "Blockchain is DISABLED. Set BLOCKCHAIN_DISABLED=False in .env and re-run."))
            return

        force = opts["force"]
        sleep_s = opts["sleep"]
        anchored = 0
        skipped = 0
        failed = 0

        # ----------- Sheep registrations
        for s in Sheep.objects.all():
            if s.registration_tx and not force:
                ok, _ = blockchain.verify(s.registration_hash)
                if ok:
                    skipped += 1
                    continue

            payload = {
                "type": "registration",
                "tag_id": s.tag_id,
                "origin_country": s.origin_country,
                "import_date": str(s.import_date),
                "batch_number": s.batch_number,
                "created_at": s.created_at.isoformat(),
            }
            new_hash = compute_hash(payload)
            tx = blockchain.register_sheep(new_hash, wait_receipt=False)
            if tx:
                s.registration_hash = new_hash
                s.registration_tx = tx
                s.save(update_fields=["registration_hash", "registration_tx"])
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ sheep {s.tag_id} → tx {tx[:16]}…"))
                anchored += 1
            else:
                self.stderr.write(f"  ✗ sheep {s.tag_id} failed")
                failed += 1
            time.sleep(sleep_s)

        # ----------- Events
        for ev in Event.objects.all().order_by("timestamp"):
            if ev.on_chain_verified and not force:
                ok, _ = blockchain.verify(ev.data_hash)
                if ok:
                    skipped += 1
                    continue

            payload = {
                "type": "event",
                "tag_id": ev.sheep.tag_id,
                "status": ev.status,
                "location": ev.location,
                "notes": ev.notes,
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "actor": ev.actor.username if ev.actor else "system",
                "timestamp": ev.timestamp.isoformat(),
            }
            new_hash = compute_hash(payload)
            tx = blockchain.add_event(new_hash, wait_receipt=False)
            if tx:
                ev.data_hash = new_hash
                ev.blockchain_tx = tx
                # Will flip to True once the tx is mined; /verify/ updates this lazily.
                ev.on_chain_verified = False
                ev.save(update_fields=["data_hash", "blockchain_tx", "on_chain_verified"])
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ event {ev.id} ({ev.status} for {ev.sheep.tag_id}) → tx {tx[:16]}…"))
                anchored += 1
            else:
                self.stderr.write(f"  ✗ event {ev.id} failed")
                failed += 1
            time.sleep(sleep_s)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. anchored={anchored}  skipped={skipped}  failed={failed}"))
