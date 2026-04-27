"""Backend tests for Mandala — Indic financial layer.

Covers: public content, auth, donations, subscriptions, super-admin,
temple-admin, role checks, and AI deity creation.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://temple-unified.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPER_ADMIN = {"email": "admin@mandala.in", "password": "mandala123"}
DONOR = {"email": "devotee@mandala.in", "password": "devotee123"}
TEMPLE_ADMIN = {"email": "temple.vaishnodevishrine@mandala.in", "password": "temple123"}


# ─── helpers ───
def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()


@pytest.fixture(scope="session")
def donor_auth():
    return _login(DONOR)


@pytest.fixture(scope="session")
def admin_auth():
    return _login(SUPER_ADMIN)


@pytest.fixture(scope="session")
def temple_admin_auth():
    return _login(TEMPLE_ADMIN)


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# ─── public content ───
class TestPublicContent:
    def test_traditions_returns_six(self):
        r = requests.get(f"{API}/traditions", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 6
        slugs = {t["slug"] for t in data}
        assert {"shaktism", "shaivism", "lakshmi", "buddhism", "jainism", "sikhism"}.issubset(slugs)

    def test_deities_returns_eight(self):
        r = requests.get(f"{API}/deities", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 8  # 8 seeded; AI test may add 1

    def test_deities_filter_tradition(self):
        r = requests.get(f"{API}/deities", params={"tradition": "shaktism"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 2
        assert all(d["tradition_slug"] == "shaktism" for d in data)

    def test_deities_filter_featured(self):
        r = requests.get(f"{API}/deities", params={"featured": "true"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert all(d["featured"] is True for d in data)
        assert len(data) >= 1

    def test_deity_detail_and_temples(self):
        r = requests.get(f"{API}/deities", timeout=30)
        deity = r.json()[0]
        d = requests.get(f"{API}/deities/{deity['id']}", timeout=30)
        assert d.status_code == 200
        assert d.json()["id"] == deity["id"]

        t = requests.get(f"{API}/deities/{deity['id']}/temples", timeout=30)
        assert t.status_code == 200
        assert isinstance(t.json(), list)


# ─── auth ───
class TestAuth:
    def test_signup_donor(self):
        email = f"test_{uuid.uuid4().hex[:8]}@mandala.in"
        r = requests.post(f"{API}/auth/signup", json={
            "name": "Test Donor",
            "email": email,
            "password": "passw0rd!",
        }, timeout=30)
        assert r.status_code == 200
        body = r.json()
        assert "token" in body and isinstance(body["token"], str)
        assert body["user"]["email"] == email
        assert body["user"]["role"] == "donor"

    def test_login_super_admin(self, admin_auth):
        assert admin_auth["user"]["role"] == "super_admin"
        assert admin_auth["user"]["email"] == "admin@mandala.in"

    def test_login_donor(self, donor_auth):
        assert donor_auth["user"]["role"] == "donor"

    def test_me_with_token(self, donor_auth):
        r = requests.get(f"{API}/auth/me", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["email"] == DONOR["email"]

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "no@x.com", "password": "x"}, timeout=30)
        assert r.status_code == 401


# ─── donations ───
class TestDonations:
    def _shaktism_deity_with_temples(self):
        ds = requests.get(f"{API}/deities", params={"tradition": "shaktism"}, timeout=30).json()
        for d in ds:
            ts = requests.get(f"{API}/deities/{d['id']}/temples", timeout=30).json()
            if len(ts) >= 2:
                return d, ts
        return ds[0], requests.get(f"{API}/deities/{ds[0]['id']}/temples", timeout=30).json()

    def test_create_and_confirm_donation(self, donor_auth):
        deity, temples = self._shaktism_deity_with_temples()
        assert len(temples) >= 1
        total = 1100.0
        if len(temples) >= 2:
            splits = [
                {"temple_id": temples[0]["id"], "percentage": 60.0, "amount": 660.0},
                {"temple_id": temples[1]["id"], "percentage": 40.0, "amount": 440.0},
            ]
        else:
            splits = [{"temple_id": temples[0]["id"], "percentage": 100.0, "amount": total}]

        r = requests.post(f"{API}/donations",
                          json={"deity_id": deity["id"], "total_amount": total, "splits": splits,
                                "donor_note": "Jai Mata Di"},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "pending"
        assert d["payment_ref"].startswith("mock_rzp_")
        assert d["total_amount"] == total

        cr = requests.post(f"{API}/donations/{d['id']}/confirm",
                           headers=_h(donor_auth["token"]), timeout=30)
        assert cr.status_code == 200
        assert cr.json()["status"] == "succeeded"

    def test_invalid_split_percentages_rejected(self, donor_auth):
        deity, temples = self._shaktism_deity_with_temples()
        splits = [{"temple_id": temples[0]["id"], "percentage": 50.0, "amount": 500.0}]
        r = requests.post(f"{API}/donations",
                          json={"deity_id": deity["id"], "total_amount": 1000.0, "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 400

    def test_my_donations(self, donor_auth):
        r = requests.get(f"{API}/donations/me", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1


# ─── subscriptions ───
class TestSubscriptions:
    def _deity_temples(self):
        ds = requests.get(f"{API}/deities", timeout=30).json()
        for d in ds:
            ts = requests.get(f"{API}/deities/{d['id']}/temples", timeout=30).json()
            if ts:
                return d, ts
        raise AssertionError("no deity with temples")

    def test_monthly_subscription(self, donor_auth):
        deity, temples = self._deity_temples()
        amount = 501.0
        splits = [{"temple_id": temples[0]["id"], "percentage": 100.0, "amount": amount}]
        r = requests.post(f"{API}/subscriptions",
                          json={"deity_id": deity["id"], "kind": "monthly", "amount": amount, "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["amount"] == amount and s["kind"] == "monthly" and s["status"] == "active"

    def test_tier_silver_subscription_and_cancel(self, donor_auth):
        deity, temples = self._deity_temples()
        amount = 1501.0  # silver
        splits = [{"temple_id": temples[0]["id"], "percentage": 100.0, "amount": amount}]
        r = requests.post(f"{API}/subscriptions",
                          json={"deity_id": deity["id"], "kind": "tier", "tier": "silver", "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["amount"] == 1501 and s["tier"] == "silver"

        # cancel
        cr = requests.post(f"{API}/subscriptions/{s['id']}/cancel",
                           headers=_h(donor_auth["token"]), timeout=30)
        assert cr.status_code == 200
        assert cr.json()["status"] == "cancelled"

    def test_my_subscriptions(self, donor_auth):
        r = requests.get(f"{API}/subscriptions/me", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─── super admin ───
class TestSuperAdmin:
    def test_analytics_structure(self, admin_auth):
        r = requests.get(f"{API}/admin/analytics", headers=_h(admin_auth["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("total_donations_inr", "mrr_inr", "top_deities", "top_temples", "recent_donations", "counts"):
            assert k in d
        assert "deities" in d["counts"] and "temples" in d["counts"] and "donors" in d["counts"]

    def test_analytics_forbidden_for_donor(self, donor_auth):
        r = requests.get(f"{API}/admin/analytics", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 403

    def test_admin_donations_forbidden_for_donor(self, donor_auth):
        r = requests.get(f"{API}/admin/donations", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 403


# ─── temple admin ───
class TestTempleAdmin:
    def test_overview(self, temple_admin_auth):
        r = requests.get(f"{API}/temple-admin/overview", headers=_h(temple_admin_auth["token"]), timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "temple" in d and d["temple"]
        assert "donations" in d and isinstance(d["donations"], list)
        assert "total_received_inr" in d

    def test_overview_forbidden_for_donor(self, donor_auth):
        r = requests.get(f"{API}/temple-admin/overview", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 403


# ─── AI deity creation ───
class TestAIDeity:
    def test_create_deity_with_ai(self, admin_auth):
        payload = {
            "name": "Test Ambika Devi",
            "tradition_slug": "shaktism",
            "use_ai": True,
            "featured": False,
        }
        r = requests.post(f"{API}/admin/deities", json=payload,
                          headers=_h(admin_auth["token"]), timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["name"] == "Test Ambika Devi"
        # Fallback strings present in code:
        fallback_long = f"Test Ambika Devi is venerated across the tradition of Shaktism."
        fallback_myth = f"Test Ambika Devi is worshipped in countless temples with rich rituals and mantras."
        # If AI worked, fields should differ from fallback
        assert d["long_desc"] and d["mythology"] and d["mantra"]
        ai_used = (d["long_desc"] != fallback_long) or (d["mythology"] != fallback_myth) or (d["mantra"] != "Om")
        assert ai_used, f"AI generation appears to have used fallback. Got: {d}"

    def test_admin_deity_forbidden_for_donor(self, donor_auth):
        r = requests.post(f"{API}/admin/deities",
                          json={"name": "X", "tradition_slug": "shaktism", "use_ai": False},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 403
