"""Teks tampilan buat data panduan. Dipakai template, filter template, dan API."""

DIFFICULTY_LABELS = {
    "Very easy": "Sangat mudah",
    "Easy": "Mudah",
    "Moderate": "Sedang",
    "Difficult": "Sulit",
    "Very difficult": "Sangat sulit",
}

# Nama warna di CSS: easy hijau, moderate oranye, hard merah
DIFFICULTY_TONES = {
    "Very easy": "easy",
    "Easy": "easy",
    "Moderate": "moderate",
    "Difficult": "hard",
    "Very difficult": "hard",
}


def difficulty_label(value):
    return DIFFICULTY_LABELS.get(value, value)


def difficulty_tone(value):
    return DIFFICULTY_TONES.get(value, "moderate")


def duration_label(minutes):
    """45 jadi "45 menit", 75 jadi "1 jam 15 menit", 120 jadi "2 jam"."""
    hours, rest = divmod(int(minutes or 0), 60)
    if not hours:
        return f"{rest} menit"
    return f"{hours} jam" if not rest else f"{hours} jam {rest} menit"
