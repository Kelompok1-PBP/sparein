from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from devices.selectors import get_device_or_404
from diagnostics.selectors import get_symptom_qs
from diagnostics.serializers import DiagnosisResultSerializer, SymptomSerializer
from diagnostics.services import rank_causes


class SymptomPagination(PageNumberPagination):
    page_size = 60


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    """List dan detail gejala untuk aplikasi mobile, filter sama dengan `/api/symptoms/`."""

    serializer_class = SymptomSerializer
    pagination_class = SymptomPagination
    lookup_field = "slug"

    def get_queryset(self):
        params = self.request.query_params
        return get_symptom_qs(
            device=params.get("device", "").strip(),
            severity=params.get("severity", "").strip(),
        )


class DiagnoseView(APIView):
    """Hitung ranking penyebab dari gejala yang dicentang. Tidak menulis ke database."""

    def get(self, request):
        slug = request.query_params.get("device", "").strip()
        if not slug:
            raise ValidationError({"device": "Parameter device wajib diisi."})
        device = get_device_or_404(slug)
        ticked = [int(v) for v in request.query_params.getlist("symptom") if v.isdigit()]
        results = rank_causes(device.pk, ticked)
        return Response(
            {
                "count": len(results),
                "results": DiagnosisResultSerializer(results, many=True).data,
            }
        )
