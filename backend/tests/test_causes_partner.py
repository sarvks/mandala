"""Backend tests for Mandala — Causes, Beneficiaries, Cause Donations,
Cause Subscriptions, Partner Portal & Demo Accounts (iteration 3 features).
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://temple-unified.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login {email} failed: {r.status_code} {r.text}"
    return r.json()


# ─── fixtures ───
@pytest.fixture(scope="session")
def donor_auth():
    return _login("devotee@mandala.in", "devotee123")


@pytest.fixture(scope="session")
def admin_auth():
    return _login("admin@mandala.in", "mandala123")


@pytest.fixture(scope="session")
def temple_admin_auth():
    return _login("temple.vaishnodevishrine@mandala.in", "temple123")


@pytest.fixture(scope="session")
def partner_earth_auth():
    return _login("partner.sankalptarufoundation@mandala.in", "partner123")


@pytest.fixture(scope="session")
def partner_animals_auth():
    return _login("partner.wildlifesos@mandala.in", "partner123")


@pytest.fixture(scope="session")
def partner_humans_auth():
    return _login("partner.prathameducationfoundati@mandala.in", "partner123")


# ─── Causes ───
class TestCauses:
    def test_list_returns_nine(self):
        r = requests.get(f"{API}/causes", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 9, f"expected 9 causes, got {len(data)}"
        cats = {c["category"] for c in data}
        assert {"earth", "animal", "human"}.issubset(cats)

    @pytest.mark.parametrize("cat", ["earth", "animal", "human"])
    def test_category_filter(self, cat):
        r = requests.get(f"{API}/causes", params={"category": cat}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 3, f"expected 3 {cat} causes, got {len(data)}"
        assert all(c["category"] == cat for c in data)

    def test_featured_filter(self):
        r = requests.get(f"{API}/causes", params={"featured": "true"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert all(c.get("featured") is True for c in data)

    def test_get_cause_and_beneficiaries(self):
        all_causes = requests.get(f"{API}/causes", timeout=30).json()
        c = all_causes[0]
        d = requests.get(f"{API}/causes/{c['id']}", timeout=30)
        assert d.status_code == 200
        assert d.json()["id"] == c["id"]

        b = requests.get(f"{API}/causes/{c['id']}/beneficiaries", timeout=30)
        assert b.status_code == 200
        bens = b.json()
        assert len(bens) == 4, f"expected 4 beneficiaries for cause {c['slug']}, got {len(bens)}"

    def test_get_cause_not_found(self):
        r = requests.get(f"{API}/causes/nonexistent-id", timeout=30)
        assert r.status_code == 404


# ─── Beneficiaries ───
class TestBeneficiaries:
    def test_list_returns_thirtysix(self):
        r = requests.get(f"{API}/beneficiaries", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 36, f"expected 36 beneficiaries, got {len(data)}"

    def test_category_filter_earth(self):
        r = requests.get(f"{API}/beneficiaries", params={"category": "earth"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 12, f"expected 12 earth beneficiaries, got {len(data)}"
        assert all(b["category"] == "earth" for b in data)


# ─── Demo accounts ───
class TestDemoAccounts:
    def test_returns_six_records(self):
        r = requests.get(f"{API}/demo-accounts", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 6
        for rec in data:
            for k in ("role", "email", "password", "tagline"):
                assert k in rec, f"missing key {k} in demo-account record: {rec}"

    def test_all_six_authenticate(self):
        accs = requests.get(f"{API}/demo-accounts", timeout=30).json()
        for a in accs:
            r = requests.post(f"{API}/auth/login",
                              json={"email": a["email"], "password": a["password"]},
                              timeout=30)
            assert r.status_code == 200, f"demo login failed for {a['email']}: {r.text}"


# ─── Cause donations ───
class TestCauseDonations:
    def _earth_cause_and_4_beneficiaries(self):
        earth_causes = requests.get(f"{API}/causes", params={"category": "earth"}, timeout=30).json()
        c = earth_causes[0]
        bens = requests.get(f"{API}/causes/{c['id']}/beneficiaries", timeout=30).json()
        assert len(bens) == 4
        return c, bens

    def test_create_and_confirm(self, donor_auth):
        c, bens = self._earth_cause_and_4_beneficiaries()
        total = 1000.0
        splits = [
            {"temple_id": bens[0]["id"], "percentage": 40.0, "amount": 400.0},
            {"temple_id": bens[1]["id"], "percentage": 30.0, "amount": 300.0},
            {"temple_id": bens[2]["id"], "percentage": 20.0, "amount": 200.0},
            {"temple_id": bens[3]["id"], "percentage": 10.0, "amount": 100.0},
        ]
        r = requests.post(f"{API}/cause-donations",
                          json={"cause_id": c["id"], "total_amount": total, "splits": splits,
                                "donor_note": "For Mother Earth"},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "pending"
        assert d["payment_ref"].startswith("mock_rzp_")
        assert d["total_amount"] == total

        cr = requests.post(f"{API}/cause-donations/{d['id']}/confirm",
                           headers=_h(donor_auth["token"]), timeout=30)
        assert cr.status_code == 200
        assert cr.json()["status"] == "succeeded"

    def test_invalid_percentage_rejected(self, donor_auth):
        c, bens = self._earth_cause_and_4_beneficiaries()
        splits = [{"temple_id": bens[0]["id"], "percentage": 50.0, "amount": 500.0}]
        r = requests.post(f"{API}/cause-donations",
                          json={"cause_id": c["id"], "total_amount": 1000.0, "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 400

    def test_beneficiary_not_in_cause_rejected(self, donor_auth):
        # Pick an earth cause and an animal beneficiary not in it.
        earth_causes = requests.get(f"{API}/causes", params={"category": "earth"}, timeout=30).json()
        animal_bens = requests.get(f"{API}/beneficiaries", params={"category": "animal"}, timeout=30).json()
        c = earth_causes[0]
        bad_id = animal_bens[0]["id"]
        splits = [{"temple_id": bad_id, "percentage": 100.0, "amount": 100.0}]
        r = requests.post(f"{API}/cause-donations",
                          json={"cause_id": c["id"], "total_amount": 100.0, "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 400

    def test_my_donations(self, donor_auth):
        r = requests.get(f"{API}/cause-donations/me", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1


# ─── Cause subscriptions ───
class TestCauseSubscriptions:
    def _cause_and_bens(self):
        earth_causes = requests.get(f"{API}/causes", params={"category": "earth"}, timeout=30).json()
        c = earth_causes[0]
        bens = requests.get(f"{API}/causes/{c['id']}/beneficiaries", timeout=30).json()
        return c, bens

    def test_monthly(self, donor_auth):
        c, bens = self._cause_and_bens()
        amount = 501.0
        splits = [{"temple_id": bens[0]["id"], "percentage": 100.0, "amount": amount}]
        r = requests.post(f"{API}/cause-subscriptions",
                          json={"cause_id": c["id"], "kind": "monthly",
                                "amount": amount, "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["amount"] == amount and s["kind"] == "monthly" and s["status"] == "active"

    def test_tier_silver_and_cancel(self, donor_auth):
        c, bens = self._cause_and_bens()
        splits = [{"temple_id": bens[0]["id"], "percentage": 100.0, "amount": 1501.0}]
        r = requests.post(f"{API}/cause-subscriptions",
                          json={"cause_id": c["id"], "kind": "tier", "tier": "silver",
                                "splits": splits},
                          headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        s = r.json()
        assert s["amount"] == 1501 and s["tier"] == "silver"

        cr = requests.post(f"{API}/cause-subscriptions/{s['id']}/cancel",
                           headers=_h(donor_auth["token"]), timeout=30)
        assert cr.status_code == 200
        assert cr.json()["status"] == "cancelled"

    def test_my_subs(self, donor_auth):
        r = requests.get(f"{API}/cause-subscriptions/me", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ─── Partner Portal ───
class TestPartnerOverview:
    def test_temple_admin_view(self, temple_admin_auth):
        r = requests.get(f"{API}/partner/overview", headers=_h(temple_admin_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("kind") == "temple"
        assert "entity" in d and d["entity"]
        assert "total_received_inr" in d
        assert "donations" in d and isinstance(d["donations"], list)

    def test_partner_earth_view(self, partner_earth_auth):
        r = requests.get(f"{API}/partner/overview", headers=_h(partner_earth_auth["token"]), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("kind") == "beneficiary"
        assert d["entity"]["name"]
        assert "total_received_inr" in d
        assert isinstance(d.get("donations"), list)

    def test_partner_animals_view(self, partner_animals_auth):
        r = requests.get(f"{API}/partner/overview", headers=_h(partner_animals_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["kind"] == "beneficiary"

    def test_partner_humans_view(self, partner_humans_auth):
        r = requests.get(f"{API}/partner/overview", headers=_h(partner_humans_auth["token"]), timeout=30)
        assert r.status_code == 200
        assert r.json()["kind"] == "beneficiary"

    def test_donor_forbidden(self, donor_auth):
        r = requests.get(f"{API}/partner/overview", headers=_h(donor_auth["token"]), timeout=30)
        assert r.status_code == 403


# ─── End-to-end: confirmed cause donation reflects in partner overview ───
class TestPartnerShareAggregation:
    def test_share_appears_after_confirm(self, donor_auth, partner_earth_auth):
        # Find sankalptaru beneficiary id
        bens = requests.get(f"{API}/beneficiaries", params={"category": "earth"}, timeout=30).json()
        sankalp = next((b for b in bens if "sankalp" in b["name"].lower()), None)
        assert sankalp, "SankalpTaru beneficiary not found"
        # Pick a cause it belongs to
        cause_id = sankalp["cause_ids"][0]

        # Read baseline
        base = requests.get(f"{API}/partner/overview",
                            headers=_h(partner_earth_auth["token"]), timeout=30).json()
        baseline = base.get("total_received_inr", 0)

        # Donate 1000 with 100% to sankalp
        splits = [{"temple_id": sankalp["id"], "percentage": 100.0, "amount": 1000.0}]
        cd = requests.post(f"{API}/cause-donations",
                           json={"cause_id": cause_id, "total_amount": 1000.0, "splits": splits},
                           headers=_h(donor_auth["token"]), timeout=30).json()
        requests.post(f"{API}/cause-donations/{cd['id']}/confirm",
                      headers=_h(donor_auth["token"]), timeout=30)

        after = requests.get(f"{API}/partner/overview",
                             headers=_h(partner_earth_auth["token"]), timeout=30).json()
        assert after["total_received_inr"] >= baseline + 1000.0 - 0.01, \
            f"share did not increase by 1000: baseline={baseline}, after={after['total_received_inr']}"
