from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Sheep, Event

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "role")


class EventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Event
        fields = (
            "id", "status", "location", "notes",
            "latitude", "longitude", "photo",
            "actor_username", "actor_role", "timestamp",
            "data_hash", "blockchain_tx", "on_chain_verified",
        )
        read_only_fields = (
            "actor_username", "actor_role", "timestamp",
            "data_hash", "blockchain_tx", "on_chain_verified",
        )


class SheepSerializer(serializers.ModelSerializer):
    events = EventSerializer(many=True, read_only=True)
    qr_url = serializers.SerializerMethodField()

    class Meta:
        model = Sheep
        fields = (
            "id", "tag_id", "origin_country", "import_date",
            "batch_number", "created_at",
            "registration_hash", "registration_tx",
            "qr_url", "events",
        )
        read_only_fields = (
            "id", "tag_id", "created_at",
            "registration_hash", "registration_tx", "qr_url", "events",
        )

    def get_qr_url(self, obj):
        request = self.context.get("request")
        path = f"/api/sheep/{obj.tag_id}/qrcode/"
        return request.build_absolute_uri(path) if request else path
