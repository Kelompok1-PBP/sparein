from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response

from .models import RepairLog
from .permissions import can_use_journal
from .selectors import logs_for, site_impact_totals, status_counts, user_impact_summary
from .serializers import RepairLogSerializer
from .views import PAGE_SIZE, serialize_summary

Status = RepairLog.Status


class IsJournalMember(BasePermission):
    """Sama dengan gerbang di views.py: hanya member yang boleh membuka jurnal."""

    def has_permission(self, request, view):
        return can_use_journal(request.user)


class JournalPagination(PageNumberPagination):
    page_size = PAGE_SIZE


class JournalViewSet(viewsets.ReadOnlyModelViewSet):
    """List dan detail catatan perbaikan milik user yang login, plus ringkasan dampak."""

    serializer_class = RepairLogSerializer
    pagination_class = JournalPagination
    permission_classes = [IsJournalMember]
    lookup_value_regex = r"\d+"

    def get_queryset(self):
        # guide__device dipakai `log_device` saat catatan tidak punya device sendiri
        logs = logs_for(self.request.user).select_related("guide__device")
        status = self.request.query_params.get("status", "").strip()
        if status in Status.values:
            logs = logs.filter(status=status)
        return logs

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def summary(self, request):
        """Counter dampak situs untuk semua orang, dampak pribadi hanya untuk member."""
        site = serialize_summary(site_impact_totals())
        if not can_use_journal(request.user):
            return Response({"summary": None, "site": site, "by_status": None})
        counts = status_counts(request.user)
        return Response(
            {
                "summary": serialize_summary(user_impact_summary(request.user)),
                "site": site,
                "by_status": {value: counts[value] for value in Status.values},
            }
        )
