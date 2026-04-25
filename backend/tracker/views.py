import io
import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions as drf_perms
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Sheep, Event
from .serializers import SheepSerializer, EventSerializer
from .permissions import IsAdmin, CanAddEvent
from .blockchain import compute_hash, blockchain


# --------------------------------------------------------------- Sheep views
class SheepListCreateView(generics.ListCreateAPIView):
    """GET: list (any logged user). POST: admin only — registers a sheep."""
    queryset = Sheep.objects.all()
    serializer_class = SheepSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [drf_perms.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        tag_id = Sheep.generate_tag_id()
        sheep = serializer.save(tag_id=tag_id, created_by=self.request.user)

        payload = {
            "type": "registration",
            "tag_id": sheep.tag_id,
            "origin_country": sheep.origin_country,
            "import_date": str(sheep.import_date),
            "batch_number": sheep.batch_number,
            "created_at": sheep.created_at.isoformat(),
        }
        h = compute_hash(payload)
        tx = blockchain.register_sheep(h) or ""

        sheep.registration_hash = h
        sheep.registration_tx = tx
        sheep.save(update_fields=["registration_hash", "registration_tx"])

        # Also create the initial "imported" event
        ev_payload = {
            "type": "event",
            "tag_id": sheep.tag_id,
            "status": Event.Status.IMPORTED,
            "location": sheep.origin_country,
            "actor": self.request.user.username,
            "timestamp": sheep.created_at.isoformat(),
        }
        ev_hash = compute_hash(ev_payload)
        ev_tx = blockchain.add_event(ev_hash) or ""
        Event.objects.create(
            sheep=sheep,
            status=Event.Status.IMPORTED,
            location=sheep.origin_country,
            notes="Initial import record",
            actor=self.request.user,
            actor_role=self.request.user.role,
            data_hash=ev_hash,
            blockchain_tx=ev_tx,
            on_chain_verified=bool(ev_tx),
        )


class SheepDetailView(generics.RetrieveAPIView):
    """Public read-only sheep detail by tag_id."""
    queryset = Sheep.objects.all()
    serializer_class = SheepSerializer
    permission_classes = [AllowAny]
    lookup_field = "tag_id"


class SheepHistoryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, tag_id):
        sheep = get_object_or_404(Sheep, tag_id=tag_id)
        events = sheep.events.all()
        return Response({
            "sheep": SheepSerializer(sheep, context={"request": request}).data,
            "timeline": EventSerializer(events, many=True).data,
        })


class SheepVerifyView(APIView):
    """Cross-checks each DB event hash against the on-chain contract."""
    permission_classes = [AllowAny]

    def get(self, request, tag_id):
        sheep = get_object_or_404(Sheep, tag_id=tag_id)
        results = []
        all_ok = True

        # Registration — recompute hash from current DB values & compare to anchored hash
        reg_payload = {
            "type": "registration",
            "tag_id": sheep.tag_id,
            "origin_country": sheep.origin_country,
            "import_date": str(sheep.import_date),
            "batch_number": sheep.batch_number,
            "created_at": sheep.created_at.isoformat(),
        }
        reg_recomputed = compute_hash(reg_payload)
        reg_anchored, reg_meta = (
            blockchain.verify(sheep.registration_hash)
            if sheep.registration_hash else (False, None)
        )
        reg_match = reg_recomputed == sheep.registration_hash
        reg_ok = reg_anchored and reg_match
        all_ok = all_ok and reg_ok
        results.append({
            "type": "registration",
            "stored_hash": sheep.registration_hash,
            "recomputed_hash": reg_recomputed,
            "tx": sheep.registration_tx,
            "anchored_on_chain": reg_anchored,
            "data_matches_hash": reg_match,
            "verified": reg_ok,
            "tampered": (reg_anchored and not reg_match),
            "chain_meta": reg_meta,
        })

        for ev in sheep.events.all():
            payload = {
                "type": "event",
                "tag_id": sheep.tag_id,
                "status": ev.status,
                "location": ev.location,
                "notes": ev.notes,
                "latitude": ev.latitude,
                "longitude": ev.longitude,
                "actor": ev.actor.username if ev.actor else "system",
                "timestamp": ev.timestamp.isoformat(),
            }
            recomputed = compute_hash(payload)
            anchored, meta = blockchain.verify(ev.data_hash) if ev.data_hash else (False, None)
            matches = recomputed == ev.data_hash
            ok = anchored and matches

            # Persist effective verification state
            if ok != ev.on_chain_verified:
                ev.on_chain_verified = ok
                ev.save(update_fields=["on_chain_verified"])
            all_ok = all_ok and ok

            results.append({
                "type": "event",
                "event_id": ev.id,
                "status": ev.status,
                "stored_hash": ev.data_hash,
                "recomputed_hash": recomputed,
                "tx": ev.blockchain_tx,
                "anchored_on_chain": anchored,
                "data_matches_hash": matches,
                "verified": ok,
                "tampered": (anchored and not matches),
                "chain_meta": meta,
            })

        return Response({
            "tag_id": sheep.tag_id,
            "verified": all_ok,
            "blockchain_disabled": blockchain.disabled,
            "records": results,
        })


# --------------------------------------------------------------- Event view
class SheepEventCreateView(APIView):
    permission_classes = [CanAddEvent]

    def post(self, request, tag_id):
        sheep = get_object_or_404(Sheep, tag_id=tag_id)
        serializer = EventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Role-gated statuses
        role = request.user.role
        status_val = serializer.validated_data["status"]
        if role == "inspector" and status_val not in {"quarantine", "health_check", "issue"}:
            return Response(
                {"detail": "Inspectors may only set quarantine/health_check/issue."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if role == "transporter" and status_val not in {"transported", "delivered"}:
            return Response(
                {"detail": "Transporters may only set transported/delivered."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ev = serializer.save(
            sheep=sheep, actor=request.user, actor_role=role,
            data_hash="", blockchain_tx="",
        )

        payload = {
            "type": "event",
            "tag_id": sheep.tag_id,
            "status": ev.status,
            "location": ev.location,
            "notes": ev.notes,
            "latitude": ev.latitude,
            "longitude": ev.longitude,
            "actor": request.user.username,
            "timestamp": ev.timestamp.isoformat(),
        }
        h = compute_hash(payload)
        tx = blockchain.add_event(h) or ""
        ev.data_hash = h
        ev.blockchain_tx = tx
        ev.on_chain_verified = bool(tx)
        ev.save(update_fields=["data_hash", "blockchain_tx", "on_chain_verified"])

        return Response(EventSerializer(ev).data, status=status.HTTP_201_CREATED)


# --------------------------------------------------------------- QR code
@api_view(["GET"])
@permission_classes([AllowAny])
def sheep_qrcode(request, tag_id):
    """Returns a PNG QR encoding `tag_id`. Mobile decodes → calls /history/."""
    get_object_or_404(Sheep, tag_id=tag_id)
    img = qrcode.make(tag_id)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")
