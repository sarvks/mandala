"""Tests for the NEW favourites, notifications and map-coords features."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

DONOR = {"email": "devotee@mandala.in", "password": "devotee123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def donor():
    return _login(DONOR)


@pytest.fixture(scope="module")
def second_donor():
    email = f"test_fav_{uuid.uuid4().hex[:8]}@mandala.in"
    r = requests.post(f"{API}/auth/signup", json={
        "name": "Second Devotee", "email": email, "password": "passw0rd!"
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def temples():
    r = requests.get(f"{API}/temples", timeout=30)
    assert r.status_code == 200
    return r.json()


# ─── lat/lng on /temples ───
class TestTemplesCoords:
    def test_temples_have_numeric_lat_lng(self, temples):
        assert len(temples) >= 20
        for t in temples:
            assert isinstance(t.get("lat"), (int, float)), f"{t['name']} missing lat"
            assert isinstance(t.get("lng"), (int, float)), f"{t['name']} missing lng"
            assert 6 <= t["lat"] <= 37
            assert 68 <= t["lng"] <= 97


# ─── favourites toggle ───
class TestFavourites:
    def test_toggle_requires_auth(self, temples):
        tid = temples[0]["id"]
        r = requests.post(f"{API}/favourites/{tid}/toggle", timeout=30)
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = requests.get(f"{API}/favourites/me", timeout=30)
        assert r.status_code == 401

    def test_toggle_invalid_temple_404(self, donor):
        r = requests.post(f"{API}/favourites/INVALID/toggle",
                          headers=_h(donor["token"]), timeout=30)
        assert r.status_code == 404

    def test_toggle_on_off_flow(self, donor, temples):
        # Pick Vaishno Devi Shrine
        vaishno = next(t for t in temples if t["name"] == "Vaishno Devi Shrine")

        # Clean slate: if already favourited, toggle off first
        r = requests.get(f"{API}/favourites/me", headers=_h(donor["token"]), timeout=30)
        assert r.status_code == 200
        if vaishno["id"] in r.json()["temple_ids"]:
            requests.post(f"{API}/favourites/{vaishno['id']}/toggle",
                          headers=_h(donor["token"]), timeout=30)

        # Toggle ON
        r = requests.post(f"{API}/favourites/{vaishno['id']}/toggle",
                          headers=_h(donor["token"]), timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert body["favourited"] is True
        assert vaishno["id"] in body["temple_ids"]

        # Verify via /me
        r = requests.get(f"{API}/favourites/me", headers=_h(donor["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert vaishno["id"] in d["temple_ids"]
        assert any(t["id"] == vaishno["id"] for t in d["temples"])

        # Toggle OFF
        r = requests.post(f"{API}/favourites/{vaishno['id']}/toggle",
                          headers=_h(donor["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["favourited"] is False
        assert vaishno["id"] not in r.json()["temple_ids"]

    def test_favourites_are_per_user(self, second_donor, donor, temples):
        vaishno = next(t for t in temples if t["name"] == "Vaishno Devi Shrine")
        # Second donor favourites Vaishno
        r = requests.post(f"{API}/favourites/{vaishno['id']}/toggle",
                          headers=_h(second_donor["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["favourited"] is True

        # First donor's favourites should NOT include it (already toggled off above)
        r = requests.get(f"{API}/favourites/me", headers=_h(donor["token"]), timeout=30)
        assert vaishno["id"] not in r.json()["temple_ids"]

        # Second donor's /me confirms
        r = requests.get(f"{API}/favourites/me",
                         headers=_h(second_donor["token"]), timeout=30)
        assert vaishno["id"] in r.json()["temple_ids"]


# ─── notifications ───
class TestNotifications:
    def test_unauth_401(self):
        r = requests.get(f"{API}/notifications/me", timeout=30)
        assert r.status_code == 401

    def test_empty_for_new_donor(self):
        # Fresh donor with no favourites
        email = f"test_fresh_{uuid.uuid4().hex[:8]}@mandala.in"
        s = requests.post(f"{API}/auth/signup", json={
            "name": "Fresh", "email": email, "password": "passw0rd!"
        }, timeout=30).json()
        r = requests.get(f"{API}/notifications/me",
                         headers=_h(s["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["notifications"] == []

    def test_vaishno_durga_festivals(self, temples):
        """Fresh donor + Vaishno Devi fav → Navratri + Durga Puja; NO Mahashivratri."""
        email = f"test_vd_{uuid.uuid4().hex[:8]}@mandala.in"
        s = requests.post(f"{API}/auth/signup", json={
            "name": "VD Test", "email": email, "password": "passw0rd!"
        }, timeout=30).json()
        vaishno = next(t for t in temples if t["name"] == "Vaishno Devi Shrine")
        requests.post(f"{API}/favourites/{vaishno['id']}/toggle",
                      headers=_h(s["token"]), timeout=30)

        r = requests.get(f"{API}/notifications/me",
                         headers=_h(s["token"]), timeout=30)
        assert r.status_code == 200
        notifs = r.json()["notifications"]
        names = {n["festival"] for n in notifs}
        assert "Navratri (Sharad)" in names
        assert "Durga Puja" in names
        assert "Mahashivratri" not in names
        # Sorted ascending by days_until and no past dates
        days = [n["days_until"] for n in notifs]
        assert days == sorted(days)
        assert all(d >= 0 for d in days)

    def test_kashi_adds_mahashivratri(self, temples):
        email = f"test_kv_{uuid.uuid4().hex[:8]}@mandala.in"
        s = requests.post(f"{API}/auth/signup", json={
            "name": "KV Test", "email": email, "password": "passw0rd!"
        }, timeout=30).json()
        vaishno = next(t for t in temples if t["name"] == "Vaishno Devi Shrine")
        kashi = next(t for t in temples if t["name"] == "Kashi Vishwanath")
        for tid in (vaishno["id"], kashi["id"]):
            requests.post(f"{API}/favourites/{tid}/toggle",
                          headers=_h(s["token"]), timeout=30)

        r = requests.get(f"{API}/notifications/me",
                         headers=_h(s["token"]), timeout=30)
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()
        notifs = r.json()["notifications"]
        names = {n["festival"] for n in notifs}
        # Shaivism festivals: Mahashivratri (2026-02-15), Shravan Somvar (2026-07-27)
        # Whichever is still upcoming must appear.
        maha = datetime.fromisoformat("2026-02-15").date()
        shrav = datetime.fromisoformat("2026-07-27").date()
        if maha >= today:
            assert "Mahashivratri" in names
        if shrav >= today:
            assert "Shravan Somvar" in names
        # Durga-tradition festivals still matched via Vaishno
        assert "Durga Puja" in names or "Navratri (Sharad)" in names
