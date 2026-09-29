import requests

BASE = "https://www.ifixit.com/api/2.0"


def fetch_family(title):
    """Raw JSON wiki iFixit buat satu family device."""
    resp = requests.get(f"{BASE}/wikis/CATEGORY/{title}", timeout=15)
    resp.raise_for_status()
    return resp.json()
