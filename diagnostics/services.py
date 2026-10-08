from diagnostics.models import Cause, DiagnosisResult

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
            key = (-matched / len(own), -matched, cause.title)
            result = {
                "cause": cause,
                "likelihood": _likelihood(matched, len(own)),
                "note": cause.note,
            }
            scored.append((key, result))
    return [result for _, result in sorted(scored, key=lambda pair: pair[0])]
