from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["username"] = self.user.username
        return data


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer


from .views import (
    SheepListCreateView, SheepDetailView, SheepHistoryView,
    SheepVerifyView, SheepEventCreateView, sheep_qrcode,
)
from .dashboard import DashboardStatsView

urlpatterns = [
    path("auth/login/", RoleTokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),

    path("sheep/", SheepListCreateView.as_view()),
    path("sheep/<str:tag_id>/", SheepDetailView.as_view()),
    path("sheep/<str:tag_id>/event/", SheepEventCreateView.as_view()),
    path("sheep/<str:tag_id>/history/", SheepHistoryView.as_view()),
    path("sheep/<str:tag_id>/verify/", SheepVerifyView.as_view()),
    path("sheep/<str:tag_id>/qrcode/", sheep_qrcode),

    path("dashboard/stats/", DashboardStatsView.as_view()),
]
