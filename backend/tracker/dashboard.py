"""Aggregate dashboard stats for the web UI."""
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Sheep, Event


class DashboardStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        last_7d = now - timedelta(days=7)

        total_sheep = Sheep.objects.count()
        total_events = Event.objects.count()
        verified_events = Event.objects.filter(on_chain_verified=True).count()
        unverified_events = total_events - verified_events
        verified_pct = round((verified_events / total_events) * 100, 1) if total_events else 0

        # Status distribution
        by_status = list(
            Event.objects.values("status").annotate(count=Count("id")).order_by("-count")
        )

        # Origin distribution
        by_origin = list(
            Sheep.objects.values("origin_country").annotate(count=Count("id")).order_by("-count")
        )

        # Recent activity (last 7 days, grouped by day)
        recent_events = Event.objects.filter(timestamp__gte=last_7d).order_by("timestamp")
        per_day = {}
        for ev in recent_events:
            key = ev.timestamp.strftime("%Y-%m-%d")
            per_day[key] = per_day.get(key, 0) + 1
        timeline_7d = [{"date": k, "count": v} for k, v in sorted(per_day.items())]

        # Latest 8 sheep
        latest_sheep = list(
            Sheep.objects.order_by("-created_at").values(
                "tag_id", "origin_country", "batch_number",
                "import_date", "created_at", "registration_tx",
            )[:8]
        )
        # attach latest status per sheep
        for s in latest_sheep:
            last_ev = (
                Event.objects.filter(sheep__tag_id=s["tag_id"])
                .order_by("-timestamp").values("status", "on_chain_verified").first()
            )
            s["latest_status"] = last_ev["status"] if last_ev else None
            s["latest_verified"] = last_ev["on_chain_verified"] if last_ev else False

        # Latest 10 events
        latest_events = list(
            Event.objects.select_related("sheep", "actor")
            .order_by("-timestamp")[:10]
            .values(
                "sheep__tag_id", "status", "location",
                "actor_role", "timestamp",
                "data_hash", "blockchain_tx", "on_chain_verified",
            )
        )

        return Response({
            "totals": {
                "sheep": total_sheep,
                "events": total_events,
                "verified_events": verified_events,
                "unverified_events": unverified_events,
                "verified_pct": verified_pct,
            },
            "by_status": by_status,
            "by_origin": by_origin,
            "timeline_7d": timeline_7d,
            "latest_sheep": latest_sheep,
            "latest_events": latest_events,
        })
