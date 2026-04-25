import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        INSPECTOR = "inspector", "Inspector"
        TRANSPORTER = "transporter", "Transporter"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Sheep(models.Model):
    tag_id = models.CharField(max_length=64, unique=True, db_index=True)
    origin_country = models.CharField(max_length=100)
    import_date = models.DateField()
    batch_number = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    # Hash + tx of the registration event itself
    registration_hash = models.CharField(max_length=66, blank=True)
    registration_tx = models.CharField(max_length=80, blank=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sheep_registered"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sheep {self.tag_id}"

    @staticmethod
    def generate_tag_id() -> str:
        return f"ADH-{uuid.uuid4().hex[:10].upper()}"


class Event(models.Model):
    class Status(models.TextChoices):
        IMPORTED = "imported", "Imported"
        QUARANTINE = "quarantine", "Quarantine"
        HEALTH_CHECK = "health_check", "Health Check"
        TRANSPORTED = "transported", "Transported"
        DELIVERED = "delivered", "Delivered"
        ISSUE = "issue", "Issue"

    sheep = models.ForeignKey(Sheep, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=20, choices=Status.choices)
    location = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    actor_role = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Optional GPS / photo
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    photo = models.ImageField(upload_to="events/", null=True, blank=True)

    # Blockchain anchoring
    data_hash = models.CharField(max_length=66, db_index=True)
    blockchain_tx = models.CharField(max_length=80, blank=True)
    on_chain_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sheep.tag_id} → {self.status}"
