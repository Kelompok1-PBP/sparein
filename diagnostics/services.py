from django.db import transaction

from diagnostics.models import Cause, DiagnosisResult, DiagnosisSession
from diagnostics.selectors import get_symptoms_for_device

Likelihood = DiagnosisResult.Likelihood


def _likelihood(matched, total):
    """Rasio gejala cocok: >= 2/3 tinggi, >= 1/3 sedang, selebihnya rendah."""
    if matched * 3 >= total * 2:
        return Likelihood.HIGH
    if matched * 3 >= total:
        return Likelihood.MEDIUM
    return Likelihood.LOW


def rank_causes(device_id, symptom_ids):
    """Urutkan penyebab perangkat dari gejala yang dicentang, paling mungkin dulu."""
    ticked = set(symptom_ids)
    if not ticked:
        return []
    scored = []
    for cause in Cause.objects.filter(device_id=device_id).prefetch_related("symptoms"):
        own = {s.pk for s in cause.symptoms.all()}
        matched = len(own & ticked)
        if matched:
            likelihood = _likelihood(matched, len(own))
            key = (-matched / len(own), -matched, cause.title)
            result = {
                "cause": cause,
                "likelihood": likelihood,
                "likelihood_label": Likelihood(likelihood).label,
                "note": cause.note,
            }
            scored.append((key, result))
    return [result for _, result in sorted(scored, key=lambda pair: pair[0])]


@transaction.atomic
def save_session(user, device, symptom_ids):
    """Simpan sesi beserta hasilnya. Gejala milik perangkat lain dibuang. None kalau kosong."""
    symptoms = list(get_symptoms_for_device(device.pk).filter(pk__in=symptom_ids))
    if not symptoms:
        return None
    session = DiagnosisSession.objects.create(
        user=user if user.is_authenticated else None, device=device
    )
    session.symptoms.set(symptoms)
    DiagnosisResult.objects.bulk_create(
        DiagnosisResult(
            session=session, cause=r["cause"], likelihood=r["likelihood"], note=r["note"]
        )
        for r in rank_causes(device.pk, [s.pk for s in symptoms])
    )
    return session
