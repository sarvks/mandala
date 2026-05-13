"""Mandala - The Financial Layer of Indic Religions.

One Deity. One Payment Link. Split Donations across associated temples.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt as pyjwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# ────────── Config ──────────
MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXP_HOURS = int(os.environ.get('JWT_EXP_HOURS', '168'))
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="Mandala API")
api_router = APIRouter(prefix="/api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# ────────── Utilities ──────────
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.isoformat()

def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except Exception:
        return False

def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": now_utc() + timedelta(hours=JWT_EXP_HOURS),
        "iat": now_utc(),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(*roles):
    async def checker(user=Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail=f"Requires role: {roles}")
        return user
    return checker

# ────────── Models ──────────
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: str
    role: str
    temple_id: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    user: UserPublic

class Tradition(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    accent: str

class Deity(BaseModel):
    id: str
    name: str
    tradition_slug: str
    short_desc: str
    long_desc: str
    mythology: str
    mantra: Optional[str] = None
    image_url: str
    featured: bool = False

class DeityCreate(BaseModel):
    name: str
    tradition_slug: str
    short_desc: Optional[str] = None
    image_url: Optional[str] = None
    featured: bool = False
    use_ai: bool = True

class Temple(BaseModel):
    id: str
    name: str
    location: str
    city: str
    state: str
    deity_ids: List[str]
    admin_user_id: Optional[str] = None
    image_url: str
    description: str
    established: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class TempleCreate(BaseModel):
    name: str
    location: str
    city: str
    state: str
    deity_ids: List[str]
    image_url: Optional[str] = None
    description: Optional[str] = None
    established: Optional[str] = None
    admin_email: Optional[str] = None

class SplitItem(BaseModel):
    temple_id: str
    percentage: float
    amount: float

class DonationCreate(BaseModel):
    deity_id: str
    total_amount: float
    splits: List[SplitItem]
    donor_note: Optional[str] = None

class Donation(BaseModel):
    id: str
    donor_id: Optional[str]
    donor_name: str
    donor_email: str
    deity_id: str
    deity_name: str
    total_amount: float
    splits: List[SplitItem]
    status: str
    payment_ref: str
    donor_note: Optional[str] = None
    created_at: str

class SubscriptionCreate(BaseModel):
    deity_id: str
    kind: Literal["monthly", "tier"]
    amount: Optional[float] = None
    tier: Optional[Literal["bronze", "silver", "gold"]] = None
    splits: List[SplitItem]

class Subscription(BaseModel):
    id: str
    donor_id: str
    deity_id: str
    deity_name: str
    kind: str
    amount: float
    tier: Optional[str] = None
    splits: List[SplitItem]
    status: str
    next_charge_at: str
    created_at: str

PATRON_TIERS = {
    "bronze": {"name": "Bronze", "amount": 501, "perks": ["Monthly newsletter", "Digital blessing card"]},
    "silver": {"name": "Silver", "amount": 1501, "perks": ["All Bronze perks", "Name engraved on digital wall", "Quarterly prasad parcel"]},
    "gold": {"name": "Gold", "amount": 5001, "perks": ["All Silver perks", "Priority darshan invites", "Annual temple yatra discount", "Personalised sankalp"]},
}

# ────────── Auth Routes ──────────
@api_router.post("/auth/signup", response_model=AuthResponse)
async def signup(payload: UserSignup):
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": payload.name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "role": "donor",
        "temple_id": None,
        "created_at": iso(now_utc()),
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, "donor")
    return {"token": token, "user": {k: v for k, v in user_doc.items() if k != "password_hash"}}

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(payload: UserLogin):
    user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["id"], user["role"])
    user.pop("password_hash", None)
    return {"token": token, "user": user}

@api_router.get("/auth/me", response_model=UserPublic)
async def me(user=Depends(get_current_user)):
    return user

# ────────── Public Content ──────────
@api_router.get("/traditions", response_model=List[Tradition])
async def list_traditions():
    items = await db.traditions.find({}, {"_id": 0}).to_list(50)
    return items

@api_router.get("/deities", response_model=List[Deity])
async def list_deities(tradition: Optional[str] = None, featured: Optional[bool] = None):
    q = {}
    if tradition and tradition != "all":
        q["tradition_slug"] = tradition
    if featured is not None:
        q["featured"] = featured
    items = await db.deities.find(q, {"_id": 0}).to_list(200)
    return items

@api_router.get("/deities/{deity_id}", response_model=Deity)
async def get_deity(deity_id: str):
    d = await db.deities.find_one({"id": deity_id}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Deity not found")
    return d

@api_router.get("/deities/{deity_id}/temples", response_model=List[Temple])
async def deity_temples(deity_id: str):
    items = await db.temples.find({"deity_ids": deity_id}, {"_id": 0}).to_list(200)
    return items

@api_router.get("/temples", response_model=List[Temple])
async def list_temples():
    items = await db.temples.find({}, {"_id": 0}).to_list(500)
    return items

@api_router.get("/patron-tiers")
async def get_patron_tiers():
    return PATRON_TIERS

# ────────── AI Content Generation ──────────
async def generate_deity_content(name: str, tradition: str) -> dict:
    """Use Claude Sonnet 4.5 via Emergent Universal Key."""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        system = (
            "You are a respectful scholar of Indic religious traditions. Produce concise, "
            "reverent, accurate content about deities. Never fabricate scripture. Use plain prose, "
            "no markdown, no emojis."
        )
        prompt = (
            f"Deity: {name}\nTradition: {tradition}\n\nReturn a JSON object with EXACTLY these keys:\n"
            "short_desc (1 sentence, <=120 chars),\n"
            "long_desc (2-3 sentences describing the deity's essence and role),\n"
            "mythology (one short paragraph, 3-5 sentences, culturally accurate),\n"
            "mantra (a traditional short mantra in transliteration).\n"
            "Respond ONLY with valid JSON, nothing else."
        )
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"mandala-deity-{uuid.uuid4()}",
            system_message=system,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        resp = await chat.send_message(UserMessage(text=prompt))
        import json as _json, re
        txt = resp.strip()
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            txt = m.group(0)
        data = _json.loads(txt)
        return {
            "short_desc": data.get("short_desc", "")[:220],
            "long_desc": data.get("long_desc", ""),
            "mythology": data.get("mythology", ""),
            "mantra": data.get("mantra", ""),
        }
    except Exception:
        logging.exception("AI generation failed; using fallback")
        return {
            "short_desc": f"A revered form of the divine in {tradition}.",
            "long_desc": f"{name} is venerated across the tradition of {tradition}.",
            "mythology": f"{name} is worshipped in countless temples with rich rituals and mantras.",
            "mantra": "Om",
        }

@api_router.post("/admin/deities", response_model=Deity)
async def create_deity(payload: DeityCreate, user=Depends(require_role("super_admin"))):
    tradition = await db.traditions.find_one({"slug": payload.tradition_slug}, {"_id": 0})
    if not tradition:
        raise HTTPException(400, "Invalid tradition")
    content = {}
    if payload.use_ai:
        content = await generate_deity_content(payload.name, tradition["name"])
    deity = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "tradition_slug": payload.tradition_slug,
        "short_desc": payload.short_desc or content.get("short_desc", ""),
        "long_desc": content.get("long_desc", ""),
        "mythology": content.get("mythology", ""),
        "mantra": content.get("mantra", ""),
        "image_url": payload.image_url or "https://images.unsplash.com/photo-1634180288740-45c848ef031d?w=1200",
        "featured": payload.featured,
    }
    await db.deities.insert_one(deity.copy())
    deity.pop("_id", None)
    return deity

@api_router.post("/admin/temples", response_model=Temple)
async def create_temple(payload: TempleCreate, user=Depends(require_role("super_admin"))):
    admin_user_id = None
    if payload.admin_email:
        existing = await db.users.find_one({"email": payload.admin_email.lower()})
        if existing:
            admin_user_id = existing["id"]
        else:
            admin_user_id = str(uuid.uuid4())
            await db.users.insert_one({
                "id": admin_user_id,
                "name": f"Admin - {payload.name}",
                "email": payload.admin_email.lower(),
                "password_hash": hash_password("templeadmin123"),
                "role": "temple_admin",
                "temple_id": None,
                "created_at": iso(now_utc()),
            })
    temple = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "location": payload.location,
        "city": payload.city,
        "state": payload.state,
        "deity_ids": payload.deity_ids,
        "admin_user_id": admin_user_id,
        "image_url": payload.image_url or "https://images.unsplash.com/photo-1634180288740-45c848ef031d?w=1200",
        "description": payload.description or "",
        "established": payload.established,
    }
    await db.temples.insert_one(temple.copy())
    if admin_user_id:
        await db.users.update_one({"id": admin_user_id}, {"$set": {"temple_id": temple["id"]}})
    temple.pop("_id", None)
    return temple

# ────────── Donations ──────────
def _validate_splits(total: float, splits: List[SplitItem]):
    for s in splits:
        if s.percentage < 0 or s.amount < 0:
            raise HTTPException(400, "Split percentages and amounts must be non-negative")
        if s.percentage > 100:
            raise HTTPException(400, "A single split cannot exceed 100%")
    pct = sum(s.percentage for s in splits)
    if abs(pct - 100) > 0.5:
        raise HTTPException(400, f"Splits must sum to 100% (got {pct:.2f})")
    amt = sum(s.amount for s in splits)
    if abs(amt - total) > 1.5:
        raise HTTPException(400, f"Split amounts must sum to total ({amt} vs {total})")

@api_router.post("/donations", response_model=Donation)
async def create_donation(payload: DonationCreate, user=Depends(get_current_user)):
    if payload.total_amount < 11:
        raise HTTPException(400, "Minimum donation is 11")
    deity = await db.deities.find_one({"id": payload.deity_id}, {"_id": 0})
    if not deity:
        raise HTTPException(404, "Deity not found")
    for s in payload.splits:
        t = await db.temples.find_one({"id": s.temple_id}, {"_id": 0})
        if not t or payload.deity_id not in t.get("deity_ids", []):
            raise HTTPException(400, f"Temple {s.temple_id} is not associated with this deity")
    _validate_splits(payload.total_amount, payload.splits)

    donation_id = str(uuid.uuid4())
    payment_ref = f"mock_rzp_{uuid.uuid4().hex[:16]}"
    donation = {
        "id": donation_id,
        "donor_id": user["id"],
        "donor_name": user["name"],
        "donor_email": user["email"],
        "deity_id": payload.deity_id,
        "deity_name": deity["name"],
        "total_amount": payload.total_amount,
        "splits": [s.model_dump() for s in payload.splits],
        "status": "pending",
        "payment_ref": payment_ref,
        "donor_note": payload.donor_note,
        "created_at": iso(now_utc()),
    }
    await db.donations.insert_one(donation.copy())
    donation.pop("_id", None)
    return donation

@api_router.post("/donations/{donation_id}/confirm", response_model=Donation)
async def confirm_donation(donation_id: str, user=Depends(get_current_user)):
    donation = await db.donations.find_one({"id": donation_id, "donor_id": user["id"]}, {"_id": 0})
    if not donation:
        raise HTTPException(404, "Donation not found")
    if donation["status"] == "succeeded":
        return donation
    await db.donations.update_one(
        {"id": donation_id},
        {"$set": {"status": "succeeded", "confirmed_at": iso(now_utc())}},
    )
    donation["status"] = "succeeded"
    return donation

@api_router.get("/donations/me", response_model=List[Donation])
async def my_donations(user=Depends(get_current_user)):
    items = await db.donations.find({"donor_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items

# ────────── Subscriptions ──────────
@api_router.post("/subscriptions", response_model=Subscription)
async def create_subscription(payload: SubscriptionCreate, user=Depends(get_current_user)):
    deity = await db.deities.find_one({"id": payload.deity_id}, {"_id": 0})
    if not deity:
        raise HTTPException(404, "Deity not found")
    if payload.kind == "monthly":
        if not payload.amount or payload.amount < 51:
            raise HTTPException(400, "Monthly amount must be at least 51")
        amount = payload.amount
        tier = None
    else:
        if not payload.tier or payload.tier not in PATRON_TIERS:
            raise HTTPException(400, "Invalid tier")
        amount = PATRON_TIERS[payload.tier]["amount"]
        tier = payload.tier
    _validate_splits(amount, payload.splits)
    sub_id = str(uuid.uuid4())
    sub = {
        "id": sub_id,
        "donor_id": user["id"],
        "deity_id": payload.deity_id,
        "deity_name": deity["name"],
        "kind": payload.kind,
        "amount": amount,
        "tier": tier,
        "splits": [s.model_dump() for s in payload.splits],
        "status": "active",
        "next_charge_at": iso(now_utc() + timedelta(days=30)),
        "created_at": iso(now_utc()),
    }
    await db.subscriptions.insert_one(sub.copy())
    sub.pop("_id", None)
    return sub

@api_router.get("/subscriptions/me", response_model=List[Subscription])
async def my_subscriptions(user=Depends(get_current_user)):
    items = await db.subscriptions.find({"donor_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return items

@api_router.post("/subscriptions/{sub_id}/cancel", response_model=Subscription)
async def cancel_subscription(sub_id: str, user=Depends(get_current_user)):
    sub = await db.subscriptions.find_one({"id": sub_id, "donor_id": user["id"]}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Subscription not found")
    await db.subscriptions.update_one({"id": sub_id}, {"$set": {"status": "cancelled"}})
    sub["status"] = "cancelled"
    return sub

# ────────── Super Admin ──────────
@api_router.get("/admin/analytics")
async def admin_analytics(user=Depends(require_role("super_admin"))):
    total_donations_cur = db.donations.aggregate([
        {"$match": {"status": "succeeded"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}},
    ])
    total_agg = await total_donations_cur.to_list(1)
    total = total_agg[0] if total_agg else {"total": 0, "count": 0}

    mrr_cur = db.subscriptions.aggregate([
        {"$match": {"status": "active"}},
        {"$group": {"_id": None, "mrr": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ])
    mrr_agg = await mrr_cur.to_list(1)
    mrr = mrr_agg[0] if mrr_agg else {"mrr": 0, "count": 0}

    by_deity_cur = db.donations.aggregate([
        {"$match": {"status": "succeeded"}},
        {"$group": {"_id": "$deity_name", "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ])
    top_deities = await by_deity_cur.to_list(10)

    pipeline = [
        {"$match": {"status": "succeeded"}},
        {"$unwind": "$splits"},
        {"$group": {"_id": "$splits.temple_id", "total": {"$sum": "$splits.amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]
    temple_totals = await db.donations.aggregate(pipeline).to_list(10)
    temple_map = {}
    ids = [t["_id"] for t in temple_totals]
    async for t in db.temples.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "name": 1}):
        temple_map[t["id"]] = t["name"]
    for row in temple_totals:
        row["name"] = temple_map.get(row["_id"], "Unknown")

    recent = await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(20)

    counts = {
        "deities": await db.deities.count_documents({}),
        "temples": await db.temples.count_documents({}),
        "donors": await db.users.count_documents({"role": "donor"}),
    }

    return {
        "total_donations_inr": total.get("total", 0),
        "total_donation_count": total.get("count", 0),
        "active_subscriptions": mrr.get("count", 0),
        "mrr_inr": mrr.get("mrr", 0),
        "top_deities": [{"name": d["_id"], "total": d["total"], "count": d["count"]} for d in top_deities],
        "top_temples": [{"name": r.get("name"), "total": r["total"], "count": r["count"]} for r in temple_totals],
        "recent_donations": recent,
        "counts": counts,
    }

@api_router.get("/admin/donations", response_model=List[Donation])
async def admin_all_donations(user=Depends(require_role("super_admin"))):
    items = await db.donations.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return items

# ────────── Temple Admin ──────────
@api_router.get("/temple-admin/overview")
async def temple_overview(user=Depends(require_role("temple_admin"))):
    temple_id = user.get("temple_id")
    if not temple_id:
        raise HTTPException(400, "Temple admin has no associated temple")
    temple = await db.temples.find_one({"id": temple_id}, {"_id": 0})
    pipeline = [
        {"$match": {"status": "succeeded", "splits.temple_id": temple_id}},
        {"$unwind": "$splits"},
        {"$match": {"splits.temple_id": temple_id}},
        {"$group": {"_id": None, "total": {"$sum": "$splits.amount"}, "count": {"$sum": 1}}},
    ]
    agg = await db.donations.aggregate(pipeline).to_list(1)
    totals = agg[0] if agg else {"total": 0, "count": 0}
    donations = await db.donations.find(
        {"splits.temple_id": temple_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(200)
    results = []
    for d in donations:
        share = next((s for s in d.get("splits", []) if s["temple_id"] == temple_id), None)
        if share:
            results.append({
                "donation_id": d["id"],
                "donor_name": d["donor_name"],
                "deity_name": d["deity_name"],
                "share_amount": share["amount"],
                "share_percentage": share["percentage"],
                "total_amount": d["total_amount"],
                "status": d["status"],
                "created_at": d["created_at"],
            })
    return {
        "temple": temple,
        "total_received_inr": totals.get("total", 0),
        "donation_count": totals.get("count", 0),
        "donations": results,
    }

# ────────── Seed ──────────
SEED_TRADITIONS = [
    {"slug": "shaktism", "name": "Shaktism", "description": "Worship of the Divine Mother — Shakti, the primordial cosmic energy.", "accent": "#7C191E"},
    {"slug": "shaivism", "name": "Shaivism", "description": "The tradition centred on Shiva as the supreme reality.", "accent": "#1A2436"},
    {"slug": "lakshmi", "name": "Lakshmi Tradition", "description": "Devotion to Goddess Lakshmi — abundance, auspiciousness and grace.", "accent": "#D4AF37"},
    {"slug": "buddhism", "name": "Buddhism", "description": "The path of awakening taught by the Buddha.", "accent": "#8B5E3C"},
    {"slug": "jainism", "name": "Jainism", "description": "Ahimsa, anekantavada and the path of the Tirthankaras.", "accent": "#B45309"},
    {"slug": "sikhism", "name": "Sikhism", "description": "The path of the Gurus, one God, seva and sangat.", "accent": "#0E7490"},
]

SEED_DEITIES = [
    {"name": "Goddess Durga", "tradition_slug": "shaktism", "featured": True,
     "short_desc": "The fierce protector, slayer of Mahishasura, embodiment of Shakti.",
     "long_desc": "Durga is the supreme warrior goddess of Shakta traditions — radiant, riding a lion, wielding every weapon, yet boundlessly compassionate. She is Shakti in her most resplendent form.",
     "mythology": "When the demon Mahishasura could not be defeated by any god alone, the collective tejas of the devas coalesced into Durga. Armed by each deity, she vanquished the buffalo-demon over nine nights, the origin of Navaratri.",
     "mantra": "Ya Devi Sarvabhuteshu Shakti Rupena Samsthita",
     "image_url": "https://images.unsplash.com/photo-1580100586938-02822d99c4a8?w=1200"},
    {"name": "Goddess Kali", "tradition_slug": "shaktism", "featured": False,
     "short_desc": "The dark mother who severs illusion and grants liberation.",
     "long_desc": "Kali is the ferocious, liberating form of the Divine Mother, dark as the night sky, garlanded with time itself, dancing on stillness.",
     "mythology": "Born from Durga's brow to slay Raktabija, whose every drop of blood spawned a clone, Kali drank the demon's blood and danced in victory until Shiva lay beneath her feet to still her.",
     "mantra": "Om Krim Kalikayai Namah",
     "image_url": "https://images.unsplash.com/photo-1565353818444-bd1156ef4fa4?w=1200"},
    {"name": "Lord Shiva", "tradition_slug": "shaivism", "featured": True,
     "short_desc": "The auspicious destroyer — Mahadeva, Nataraja, the eternal yogi.",
     "long_desc": "Shiva is the still centre of the cosmos and its dancer — ascetic and householder, destroyer of illusion and source of grace.",
     "mythology": "Seated on Kailasa, smeared with sacred ash, Shiva swallowed the halahala poison to save creation, holding it in his blue throat as Neelakantha.",
     "mantra": "Om Namah Shivaya",
     "image_url": "https://images.unsplash.com/photo-1582650625119-3a31f8fa2699?w=1200"},
    {"name": "Goddess Lakshmi", "tradition_slug": "lakshmi", "featured": True,
     "short_desc": "Bestower of abundance, prosperity and auspicious fortune.",
     "long_desc": "Lakshmi is the goddess of material and spiritual wealth, seated on a blooming lotus, flanked by elephants, gold coins cascading from her palm.",
     "mythology": "Rising from the churning of the cosmic ocean, Lakshmi chose Vishnu as her consort and has since blessed devotees who cultivate dharma, diligence and generosity.",
     "mantra": "Om Shreem Mahalakshmyai Namah",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200"},
    {"name": "Shakyamuni Buddha", "tradition_slug": "buddhism", "featured": True,
     "short_desc": "The awakened one — teacher of the middle way.",
     "long_desc": "Siddhartha Gautama renounced a princely life, discovered the path between asceticism and indulgence, and awoke beneath the Bodhi tree.",
     "mythology": "After six years of austerity, beneath the Bodhi tree in Bodh Gaya, he vowed not to rise until awakened. By dawn he had seen the nature of suffering and its cessation.",
     "mantra": "Om Muni Muni Maha Muni Shakyamuni Svaha",
     "image_url": "https://images.pexels.com/photos/33466763/pexels-photo-33466763.jpeg?auto=compress&w=1200"},
    {"name": "Avalokiteshvara", "tradition_slug": "buddhism", "featured": False,
     "short_desc": "Bodhisattva of infinite compassion.",
     "long_desc": "Avalokiteshvara hears the cries of all beings and, vowing not to enter nirvana until all are free, extends a thousand arms of aid.",
     "mythology": "When the bodhisattva's head shattered upon witnessing the suffering of the world, Amitabha reassembled him with a thousand arms and eleven heads to see and save all beings.",
     "mantra": "Om Mani Padme Hum",
     "image_url": "https://images.unsplash.com/photo-1606293459310-6c9d53e3a1c3?w=1200"},
    {"name": "Tirthankara Mahavira", "tradition_slug": "jainism", "featured": True,
     "short_desc": "The 24th ford-maker — teacher of ahimsa and anekantavada.",
     "long_desc": "Mahavira taught radical non-violence, many-sided truth and the liberation of the soul through right conduct.",
     "mythology": "After twelve years of intense austerity, Mahavira attained kevala jnana, omniscience, and taught the fourfold sangha the path to moksha.",
     "mantra": "Namo Arihantanam",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200"},
    {"name": "Guru Nanak Dev Ji", "tradition_slug": "sikhism", "featured": True,
     "short_desc": "Founder of Sikhi — Ik Onkar, one universal creator.",
     "long_desc": "Guru Nanak travelled across the subcontinent teaching Naam Japna, Kirat Karni and Vand Chhakna — remembrance, honest work and sharing.",
     "mythology": "Emerging from the river after three days in deep communion with the divine, Guru Nanak declared there is neither Hindu nor Muslim, only the one formless creator.",
     "mantra": "Ik Onkar Satnam Karta Purakh",
     "image_url": "https://images.unsplash.com/photo-1609254819260-4baa6ac4e394?w=1200"},
]

SEED_TEMPLES = [
    {"name": "Vaishno Devi Shrine", "city": "Katra", "state": "Jammu & Kashmir", "deity_name": "Goddess Durga",
     "lat": 32.9911, "lng": 74.9314,
     "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?w=1200",
     "description": "Ancient cave shrine nestled in the Trikuta mountains, visited by millions of pilgrims.", "established": "c. 700 CE"},
    {"name": "Dakshineswar Kali Temple", "city": "Kolkata", "state": "West Bengal", "deity_name": "Goddess Durga",
     "lat": 22.6552, "lng": 88.3577,
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "Riverside Bhavatarini temple where Sri Ramakrishna worshipped the Mother.", "established": "1855"},
    {"name": "Kamakhya Temple", "city": "Guwahati", "state": "Assam", "deity_name": "Goddess Durga",
     "lat": 26.1664, "lng": 91.7055,
     "image_url": "https://images.unsplash.com/photo-1580100586938-02822d99c4a8?w=1200",
     "description": "Revered shakti peetha atop Nilachal Hill, one of the most sacred sites of the Mother.", "established": "c. 8th century"},
    {"name": "Chamundeshwari Temple", "city": "Mysuru", "state": "Karnataka", "deity_name": "Goddess Durga",
     "lat": 12.2725, "lng": 76.6705,
     "image_url": "https://images.unsplash.com/photo-1567367806137-842e61e5f21b?w=1200",
     "description": "Hilltop temple dedicated to Chamundeshwari, patron deity of the Wodeyars.", "established": "12th century"},
    {"name": "Kalighat Kali Temple", "city": "Kolkata", "state": "West Bengal", "deity_name": "Goddess Kali",
     "lat": 22.5200, "lng": 88.3420,
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "One of 51 Shakti Peethas, among India's oldest Kali shrines.", "established": "1809"},
    {"name": "Tarapith Temple", "city": "Birbhum", "state": "West Bengal", "deity_name": "Goddess Kali",
     "lat": 23.8916, "lng": 87.7892,
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "Tantric shrine of Tara, closely tied to the saint Bamakhepa.", "established": "c. 1225"},
    {"name": "Kashi Vishwanath", "city": "Varanasi", "state": "Uttar Pradesh", "deity_name": "Lord Shiva",
     "lat": 25.3109, "lng": 83.0107,
     "image_url": "https://images.unsplash.com/photo-1561361398-a8d1ecf5d85b?w=1200",
     "description": "Jyotirlinga on the ghats of the Ganga, heart of Kashi.", "established": "ancient"},
    {"name": "Brihadeeswarar Temple", "city": "Thanjavur", "state": "Tamil Nadu", "deity_name": "Lord Shiva",
     "lat": 10.7828, "lng": 79.1318,
     "image_url": "https://images.unsplash.com/photo-1582650625119-3a31f8fa2699?w=1200",
     "description": "UNESCO-listed Chola masterpiece, granite grandeur unrivalled.", "established": "1010 CE"},
    {"name": "Kedarnath Temple", "city": "Rudraprayag", "state": "Uttarakhand", "deity_name": "Lord Shiva",
     "lat": 30.7346, "lng": 79.0669,
     "image_url": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1200",
     "description": "Himalayan jyotirlinga accessible only half the year, a pilgrimage of the soul.", "established": "ancient"},
    {"name": "Mahalakshmi Temple Mumbai", "city": "Mumbai", "state": "Maharashtra", "deity_name": "Goddess Lakshmi",
     "lat": 18.9730, "lng": 72.8090,
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Seaside temple of Mahalakshmi, Mahasaraswati and Mahakali.", "established": "1831"},
    {"name": "Padmavathi Temple", "city": "Tiruchanur", "state": "Andhra Pradesh", "deity_name": "Goddess Lakshmi",
     "lat": 13.6170, "lng": 79.3950,
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Consort shrine of Tirupati, revered as Alamelu Mangamma.", "established": "ancient"},
    {"name": "Kolhapur Mahalakshmi", "city": "Kolhapur", "state": "Maharashtra", "deity_name": "Goddess Lakshmi",
     "lat": 16.6917, "lng": 74.2325,
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "One of the Shakti Peethas, the Ambabai of Kolhapur.", "established": "7th century"},
    {"name": "Mahabodhi Temple", "city": "Bodh Gaya", "state": "Bihar", "deity_name": "Shakyamuni Buddha",
     "lat": 24.6961, "lng": 84.9915,
     "image_url": "https://images.pexels.com/photos/33466763/pexels-photo-33466763.jpeg?auto=compress&w=1200",
     "description": "UNESCO site at the place of the Buddha's awakening.", "established": "3rd century BCE"},
    {"name": "Sarnath Mulagandha Kuti Vihar", "city": "Sarnath", "state": "Uttar Pradesh", "deity_name": "Shakyamuni Buddha",
     "lat": 25.3820, "lng": 83.0245,
     "image_url": "https://images.pexels.com/photos/33466763/pexels-photo-33466763.jpeg?auto=compress&w=1200",
     "description": "Where the Buddha first turned the wheel of Dharma.", "established": "ancient"},
    {"name": "Rumtek Monastery", "city": "Gangtok", "state": "Sikkim", "deity_name": "Avalokiteshvara",
     "lat": 27.2898, "lng": 88.5619,
     "image_url": "https://images.unsplash.com/photo-1606293459310-6c9d53e3a1c3?w=1200",
     "description": "Seat of the Karmapa lineage, nestled in the eastern Himalayas.", "established": "1966"},
    {"name": "Tawang Monastery", "city": "Tawang", "state": "Arunachal Pradesh", "deity_name": "Avalokiteshvara",
     "lat": 27.5864, "lng": 91.8594,
     "image_url": "https://images.unsplash.com/photo-1606293459310-6c9d53e3a1c3?w=1200",
     "description": "Largest monastery in India, perched at 3000 m.", "established": "1680"},
    {"name": "Dilwara Temples", "city": "Mount Abu", "state": "Rajasthan", "deity_name": "Tirthankara Mahavira",
     "lat": 24.6098, "lng": 72.7197,
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Marble masterwork of Jain devotion, built 11th to 13th centuries.", "established": "1031"},
    {"name": "Palitana Temples", "city": "Palitana", "state": "Gujarat", "deity_name": "Tirthankara Mahavira",
     "lat": 21.5222, "lng": 71.8330,
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Hundreds of shrines crowning Shatrunjaya Hill, Jainism's holiest peak.", "established": "ancient"},
    {"name": "Sri Harmandir Sahib Golden Temple", "city": "Amritsar", "state": "Punjab", "deity_name": "Guru Nanak Dev Ji",
     "lat": 31.6200, "lng": 74.8765,
     "image_url": "https://images.unsplash.com/photo-1609254819260-4baa6ac4e394?w=1200",
     "description": "Spiritual centre of Sikhi, gilded sanctum set within the Amrit Sarovar.", "established": "1604"},
    {"name": "Gurudwara Bangla Sahib", "city": "New Delhi", "state": "Delhi", "deity_name": "Guru Nanak Dev Ji",
     "lat": 28.6255, "lng": 77.2090,
     "image_url": "https://images.unsplash.com/photo-1609254819260-4baa6ac4e394?w=1200",
     "description": "Historic gurudwara associated with Guru Har Krishan.", "established": "1783"},
]


async def seed_database():
    if await db.traditions.count_documents({}) == 0:
        trads = [{"id": str(uuid.uuid4()), **t} for t in SEED_TRADITIONS]
        await db.traditions.insert_many([t.copy() for t in trads])
        logging.info("Seeded %d traditions", len(trads))

    if await db.deities.count_documents({}) == 0:
        deities = [{"id": str(uuid.uuid4()), **d} for d in SEED_DEITIES]
        await db.deities.insert_many([d.copy() for d in deities])
        logging.info("Seeded %d deities", len(deities))

    if await db.temples.count_documents({}) == 0:
        deity_map = {}
        async for d in db.deities.find({}, {"_id": 0, "id": 1, "name": 1}):
            deity_map[d["name"]] = d["id"]
        temples = []
        for t in SEED_TEMPLES:
            deity_id = deity_map.get(t["deity_name"])
            if not deity_id:
                continue
            safe = "".join(ch for ch in t["name"].lower() if ch.isalnum())[:24]
            admin_email = f"temple.{safe}@mandala.in"
            admin_id = str(uuid.uuid4())
            await db.users.insert_one({
                "id": admin_id,
                "name": f"Admin - {t['name']}",
                "email": admin_email,
                "password_hash": hash_password("temple123"),
                "role": "temple_admin",
                "temple_id": None,
                "created_at": iso(now_utc()),
            })
            temple_id = str(uuid.uuid4())
            temples.append({
                "id": temple_id,
                "name": t["name"],
                "location": f"{t['city']}, {t['state']}",
                "city": t["city"],
                "state": t["state"],
                "deity_ids": [deity_id],
                "admin_user_id": admin_id,
                "image_url": t["image_url"],
                "description": t["description"],
                "established": t.get("established"),
                "lat": t.get("lat"),
                "lng": t.get("lng"),
            })
            await db.users.update_one({"id": admin_id}, {"$set": {"temple_id": temple_id}})
        if temples:
            await db.temples.insert_many([tt.copy() for tt in temples])
            logging.info("Seeded %d temples", len(temples))

    # Migration: backfill coords on existing temples seeded before the map feature
    coord_map = {t["name"]: (t["lat"], t["lng"]) for t in SEED_TEMPLES if "lat" in t}
    async for t in db.temples.find({"$or": [{"lat": {"$exists": False}}, {"lat": None}]}, {"_id": 0, "id": 1, "name": 1}):
        c = coord_map.get(t["name"])
        if c:
            await db.temples.update_one({"id": t["id"]}, {"$set": {"lat": c[0], "lng": c[1]}})

    if not await db.users.find_one({"role": "super_admin"}):
        admin_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": admin_id,
            "name": "Mandala Admin",
            "email": "admin@mandala.in",
            "password_hash": hash_password("mandala123"),
            "role": "super_admin",
            "temple_id": None,
            "created_at": iso(now_utc()),
        })
        logging.info("Seeded super admin: admin@mandala.in / mandala123")

    if not await db.users.find_one({"email": "devotee@mandala.in"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "name": "Arjun Devotee",
            "email": "devotee@mandala.in",
            "password_hash": hash_password("devotee123"),
            "role": "donor",
            "temple_id": None,
            "created_at": iso(now_utc()),
        })

# ────────── Favourites & Festivals ──────────
# Festivals are static and resolved by tradition_slug OR deity_name.
# Dates use the current/next year for the preview — real deployment would
# pull from a lunar-calendar service.
FESTIVALS = [
    {"name": "Navratri (Sharad)", "date": "2026-10-12", "tradition_slug": "shaktism", "deity_name": None,
     "description": "Nine nights of the Mother — the high festival of Shaktism."},
    {"name": "Durga Puja", "date": "2026-10-16", "tradition_slug": None, "deity_name": "Goddess Durga",
     "description": "Mahashashthi to Vijayadashami — five days of darshan."},
    {"name": "Kali Puja", "date": "2026-11-08", "tradition_slug": None, "deity_name": "Goddess Kali",
     "description": "New moon night of Kartika — worship of the dark mother."},
    {"name": "Mahashivratri", "date": "2026-02-15", "tradition_slug": "shaivism", "deity_name": None,
     "description": "The great night of Shiva — an all-night vigil of chanting."},
    {"name": "Shravan Somvar", "date": "2026-07-27", "tradition_slug": "shaivism", "deity_name": None,
     "description": "Mondays of Shravan, especially sacred to Shiva."},
    {"name": "Diwali · Lakshmi Puja", "date": "2026-11-08", "tradition_slug": "lakshmi", "deity_name": None,
     "description": "The festival of lights and the welcoming of Mahalakshmi."},
    {"name": "Varalakshmi Vratam", "date": "2026-08-07", "tradition_slug": None, "deity_name": "Goddess Lakshmi",
     "description": "Friday vrat invoking Lakshmi for the welfare of the family."},
    {"name": "Buddha Purnima", "date": "2026-05-01", "tradition_slug": "buddhism", "deity_name": None,
     "description": "The day of the Buddha's birth, awakening and mahaparinirvana."},
    {"name": "Kathina Chivara Dana", "date": "2026-10-26", "tradition_slug": "buddhism", "deity_name": None,
     "description": "End of the monsoon retreat — offering robes to the sangha."},
    {"name": "Paryushana Parva", "date": "2026-08-27", "tradition_slug": "jainism", "deity_name": None,
     "description": "Eight days of reflection, fasting and pratikramana."},
    {"name": "Mahavir Jayanti", "date": "2026-04-09", "tradition_slug": "jainism", "deity_name": None,
     "description": "Birth anniversary of the 24th Tirthankara."},
    {"name": "Guru Nanak Jayanti", "date": "2026-11-24", "tradition_slug": "sikhism", "deity_name": None,
     "description": "Gurpurab honouring the birth of Guru Nanak Dev Ji."},
    {"name": "Baisakhi", "date": "2026-04-13", "tradition_slug": "sikhism", "deity_name": None,
     "description": "Harvest festival and the birth of the Khalsa."},
]


@api_router.get("/favourites/me")
async def list_favourites(user=Depends(get_current_user)):
    fav_ids = user.get("favourite_temple_ids", []) or []
    if not fav_ids:
        return {"temple_ids": [], "temples": []}
    temples = await db.temples.find({"id": {"$in": fav_ids}}, {"_id": 0}).to_list(500)
    # preserve insertion order
    order = {tid: i for i, tid in enumerate(fav_ids)}
    temples.sort(key=lambda t: order.get(t["id"], 1e9))
    return {"temple_ids": fav_ids, "temples": temples}


@api_router.post("/favourites/{temple_id}/toggle")
async def toggle_favourite(temple_id: str, user=Depends(get_current_user)):
    temple = await db.temples.find_one({"id": temple_id}, {"_id": 0, "id": 1})
    if not temple:
        raise HTTPException(404, "Temple not found")
    fav_ids = user.get("favourite_temple_ids", []) or []
    favourited = temple_id in fav_ids
    if favourited:
        fav_ids = [t for t in fav_ids if t != temple_id]
    else:
        fav_ids = fav_ids + [temple_id]
    await db.users.update_one({"id": user["id"]}, {"$set": {"favourite_temple_ids": fav_ids}})
    return {"favourited": not favourited, "temple_ids": fav_ids}


@api_router.get("/notifications/me")
async def notifications_me(user=Depends(get_current_user)):
    """Upcoming festivals at the donor's favourite temples (next 12 months)."""
    fav_ids = user.get("favourite_temple_ids", []) or []
    if not fav_ids:
        return {"notifications": []}
    temples = await db.temples.find({"id": {"$in": fav_ids}}, {"_id": 0}).to_list(500)
    deity_ids = list({did for t in temples for did in t.get("deity_ids", [])})
    deities = await db.deities.find({"id": {"$in": deity_ids}}, {"_id": 0}).to_list(500)
    deity_by_id = {d["id"]: d for d in deities}

    today = now_utc().date()
    # Build map: festival_name -> { festival_fields, temples: [...] }
    grouped: dict[str, dict] = {}
    for t in temples:
        for did in t.get("deity_ids", []):
            d = deity_by_id.get(did)
            if not d:
                continue
            for f in FESTIVALS:
                matches = False
                if f["deity_name"] and f["deity_name"] == d["name"]:
                    matches = True
                elif f["tradition_slug"] and f["tradition_slug"] == d["tradition_slug"]:
                    matches = True
                if not matches:
                    continue
                try:
                    fdate = datetime.fromisoformat(f["date"]).date()
                except Exception:
                    continue
                if fdate < today:
                    continue
                days_until = (fdate - today).days
                if days_until > 400:
                    continue
                entry = grouped.setdefault(f["name"], {
                    "festival": f["name"],
                    "date": f["date"],
                    "days_until": days_until,
                    "description": f["description"],
                    "temples": [],
                })
                if not any(tp["temple_id"] == t["id"] for tp in entry["temples"]):
                    entry["temples"].append({
                        "temple_id": t["id"],
                        "temple_name": t["name"],
                        "temple_city": t["city"],
                    })
    results = sorted(grouped.values(), key=lambda r: r["days_until"])
    return {"notifications": results}


# ────────── Causes (Earth · Animal · Human) ──────────
class Cause(BaseModel):
    id: str
    category: Literal["earth", "animal", "human"]
    name: str
    slug: str
    short_desc: str
    long_desc: str
    image_url: str
    featured: bool = False
    impact_metric: Optional[str] = None  # e.g. "1.2M trees planted"


class Beneficiary(BaseModel):
    id: str
    category: Literal["earth", "animal", "human"]
    name: str
    type: str  # "foundation" | "hospital" | "ngo"
    cause_ids: List[str]
    admin_user_id: Optional[str] = None
    city: str
    state: str
    country: str = "India"
    description: str
    image_url: str
    established: Optional[str] = None
    website: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class CauseDonationCreate(BaseModel):
    cause_id: str
    total_amount: float
    splits: List[SplitItem]  # split_item.temple_id is used to carry beneficiary_id
    donor_note: Optional[str] = None


class CauseDonation(BaseModel):
    id: str
    donor_id: Optional[str]
    donor_name: str
    donor_email: str
    cause_id: str
    cause_name: str
    category: str
    total_amount: float
    splits: List[SplitItem]
    status: str
    payment_ref: str
    donor_note: Optional[str] = None
    created_at: str


class CauseSubscriptionCreate(BaseModel):
    cause_id: str
    kind: Literal["monthly", "tier"]
    amount: Optional[float] = None
    tier: Optional[Literal["bronze", "silver", "gold"]] = None
    splits: List[SplitItem]


class CauseSubscription(BaseModel):
    id: str
    donor_id: str
    cause_id: str
    cause_name: str
    category: str
    kind: str
    amount: float
    tier: Optional[str] = None
    splits: List[SplitItem]
    status: str
    next_charge_at: str
    created_at: str


@api_router.get("/causes", response_model=List[Cause])
async def list_causes(category: Optional[str] = None, featured: Optional[bool] = None):
    q = {}
    if category and category != "all":
        q["category"] = category
    if featured is not None:
        q["featured"] = featured
    items = await db.causes.find(q, {"_id": 0}).to_list(200)
    return items


@api_router.get("/causes/{cause_id}", response_model=Cause)
async def get_cause(cause_id: str):
    c = await db.causes.find_one({"id": cause_id}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Cause not found")
    return c


@api_router.get("/causes/{cause_id}/beneficiaries", response_model=List[Beneficiary])
async def cause_beneficiaries(cause_id: str):
    items = await db.beneficiaries.find({"cause_ids": cause_id}, {"_id": 0}).to_list(200)
    return items


@api_router.get("/beneficiaries", response_model=List[Beneficiary])
async def list_beneficiaries(category: Optional[str] = None):
    q = {}
    if category and category != "all":
        q["category"] = category
    items = await db.beneficiaries.find(q, {"_id": 0}).to_list(500)
    return items


# Cause donations
@api_router.post("/cause-donations", response_model=CauseDonation)
async def create_cause_donation(payload: CauseDonationCreate, user=Depends(get_current_user)):
    if payload.total_amount < 11:
        raise HTTPException(400, "Minimum donation is 11")
    cause = await db.causes.find_one({"id": payload.cause_id}, {"_id": 0})
    if not cause:
        raise HTTPException(404, "Cause not found")
    for s in payload.splits:
        b = await db.beneficiaries.find_one({"id": s.temple_id}, {"_id": 0})
        if not b or payload.cause_id not in b.get("cause_ids", []):
            raise HTTPException(400, f"Beneficiary {s.temple_id} not associated with this cause")
    _validate_splits(payload.total_amount, payload.splits)
    donation_id = str(uuid.uuid4())
    payment_ref = f"mock_rzp_{uuid.uuid4().hex[:16]}"
    doc = {
        "id": donation_id,
        "donor_id": user["id"],
        "donor_name": user["name"],
        "donor_email": user["email"],
        "cause_id": payload.cause_id,
        "cause_name": cause["name"],
        "category": cause["category"],
        "total_amount": payload.total_amount,
        "splits": [s.model_dump() for s in payload.splits],
        "status": "pending",
        "payment_ref": payment_ref,
        "donor_note": payload.donor_note,
        "created_at": iso(now_utc()),
    }
    await db.cause_donations.insert_one(doc.copy())
    doc.pop("_id", None)
    return doc


@api_router.post("/cause-donations/{donation_id}/confirm", response_model=CauseDonation)
async def confirm_cause_donation(donation_id: str, user=Depends(get_current_user)):
    d = await db.cause_donations.find_one({"id": donation_id, "donor_id": user["id"]}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Cause donation not found")
    if d["status"] == "succeeded":
        return d
    await db.cause_donations.update_one(
        {"id": donation_id},
        {"$set": {"status": "succeeded", "confirmed_at": iso(now_utc())}},
    )
    d["status"] = "succeeded"
    return d


@api_router.get("/cause-donations/me", response_model=List[CauseDonation])
async def my_cause_donations(user=Depends(get_current_user)):
    items = await db.cause_donations.find({"donor_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items


@api_router.post("/cause-subscriptions", response_model=CauseSubscription)
async def create_cause_subscription(payload: CauseSubscriptionCreate, user=Depends(get_current_user)):
    cause = await db.causes.find_one({"id": payload.cause_id}, {"_id": 0})
    if not cause:
        raise HTTPException(404, "Cause not found")
    if payload.kind == "monthly":
        if not payload.amount or payload.amount < 51:
            raise HTTPException(400, "Monthly amount must be at least 51")
        amount = payload.amount
        tier = None
    else:
        if not payload.tier or payload.tier not in PATRON_TIERS:
            raise HTTPException(400, "Invalid tier")
        amount = PATRON_TIERS[payload.tier]["amount"]
        tier = payload.tier
    _validate_splits(amount, payload.splits)
    sub_id = str(uuid.uuid4())
    doc = {
        "id": sub_id,
        "donor_id": user["id"],
        "cause_id": payload.cause_id,
        "cause_name": cause["name"],
        "category": cause["category"],
        "kind": payload.kind,
        "amount": amount,
        "tier": tier,
        "splits": [s.model_dump() for s in payload.splits],
        "status": "active",
        "next_charge_at": iso(now_utc() + timedelta(days=30)),
        "created_at": iso(now_utc()),
    }
    await db.cause_subscriptions.insert_one(doc.copy())
    doc.pop("_id", None)
    return doc


@api_router.get("/cause-subscriptions/me", response_model=List[CauseSubscription])
async def my_cause_subscriptions(user=Depends(get_current_user)):
    items = await db.cause_subscriptions.find({"donor_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return items


@api_router.post("/cause-subscriptions/{sub_id}/cancel", response_model=CauseSubscription)
async def cancel_cause_subscription(sub_id: str, user=Depends(get_current_user)):
    sub = await db.cause_subscriptions.find_one({"id": sub_id, "donor_id": user["id"]}, {"_id": 0})
    if not sub:
        raise HTTPException(404, "Subscription not found")
    await db.cause_subscriptions.update_one({"id": sub_id}, {"$set": {"status": "cancelled"}})
    sub["status"] = "cancelled"
    return sub


# ────────── Unified Partner Portal ──────────
# Works for temple_admin (legacy) AND partner (new beneficiaries).
@api_router.get("/partner/overview")
async def partner_overview(user=Depends(get_current_user)):
    role = user.get("role")
    if role == "temple_admin":
        temple_id = user.get("temple_id")
        if not temple_id:
            raise HTTPException(400, "No associated temple")
        temple = await db.temples.find_one({"id": temple_id}, {"_id": 0})
        pipeline = [
            {"$match": {"status": "succeeded", "splits.temple_id": temple_id}},
            {"$unwind": "$splits"},
            {"$match": {"splits.temple_id": temple_id}},
            {"$group": {"_id": None, "total": {"$sum": "$splits.amount"}, "count": {"$sum": 1}}},
        ]
        agg = await db.donations.aggregate(pipeline).to_list(1)
        totals = agg[0] if agg else {"total": 0, "count": 0}
        donations = await db.donations.find(
            {"splits.temple_id": temple_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(200)
        rows = []
        for d in donations:
            share = next((s for s in d.get("splits", []) if s["temple_id"] == temple_id), None)
            if share:
                rows.append({
                    "donation_id": d["id"],
                    "donor_name": d["donor_name"],
                    "context_name": d["deity_name"],
                    "share_amount": share["amount"],
                    "share_percentage": share["percentage"],
                    "total_amount": d["total_amount"],
                    "status": d["status"],
                    "created_at": d["created_at"],
                })
        return {
            "role": "temple_admin",
            "kind": "temple",
            "entity": temple,
            "total_received_inr": totals.get("total", 0),
            "donation_count": totals.get("count", 0),
            "donations": rows,
        }
    if role == "partner":
        ben_id = user.get("beneficiary_id")
        if not ben_id:
            raise HTTPException(400, "No associated beneficiary")
        beneficiary = await db.beneficiaries.find_one({"id": ben_id}, {"_id": 0})
        pipeline = [
            {"$match": {"status": "succeeded", "splits.temple_id": ben_id}},
            {"$unwind": "$splits"},
            {"$match": {"splits.temple_id": ben_id}},
            {"$group": {"_id": None, "total": {"$sum": "$splits.amount"}, "count": {"$sum": 1}}},
        ]
        agg = await db.cause_donations.aggregate(pipeline).to_list(1)
        totals = agg[0] if agg else {"total": 0, "count": 0}
        donations = await db.cause_donations.find(
            {"splits.temple_id": ben_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(200)
        rows = []
        for d in donations:
            share = next((s for s in d.get("splits", []) if s["temple_id"] == ben_id), None)
            if share:
                rows.append({
                    "donation_id": d["id"],
                    "donor_name": d["donor_name"],
                    "context_name": d["cause_name"],
                    "share_amount": share["amount"],
                    "share_percentage": share["percentage"],
                    "total_amount": d["total_amount"],
                    "status": d["status"],
                    "created_at": d["created_at"],
                })
        return {
            "role": "partner",
            "kind": "beneficiary",
            "entity": beneficiary,
            "total_received_inr": totals.get("total", 0),
            "donation_count": totals.get("count", 0),
            "donations": rows,
        }
    raise HTTPException(403, "Only temple admins or partners can view this")


@api_router.get("/demo-accounts")
async def demo_accounts():
    """Public — returns one-click login credentials for the preview."""
    return [
        {"role": "Super Admin", "email": "admin@mandala.in", "password": "mandala123",
         "tagline": "Full control room: deities, temples, causes, partners and analytics."},
        {"role": "Donor", "email": "devotee@mandala.in", "password": "devotee123",
         "tagline": "Make offerings, manage subscriptions, track favourites."},
        {"role": "Temple Admin", "email": "temple.vaishnodevishrine@mandala.in", "password": "temple123",
         "tagline": "View incoming offerings at Vaishno Devi Shrine."},
        {"role": "Partner · Earth", "email": "partner.sankalptarufoundation@mandala.in", "password": "partner123",
         "tagline": "View incoming donations at SankalpTaru Foundation."},
        {"role": "Partner · Animals", "email": "partner.wildlifesos@mandala.in", "password": "partner123",
         "tagline": "View incoming donations at Wildlife SOS."},
        {"role": "Partner · Humans", "email": "partner.prathameducationfoundati@mandala.in", "password": "partner123",
         "tagline": "View incoming donations at Pratham Education."},
    ]


# ────────── Seed Causes ──────────
SEED_CAUSES = [
    # ── Earth ──
    {"category": "earth", "slug": "forest-wildlife", "name": "Forest & Wildlife Restoration", "featured": True,
     "short_desc": "Plant native forests, restore wildlife corridors, protect endangered species.",
     "long_desc": "From the Western Ghats to the Eastern Himalayas, restoration projects need consistent funding to plant native forest cover, fund patrols against poaching, and rewild degraded land. Your offering reaches all four partners simultaneously.",
     "image_url": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200",
     "impact_metric": "1.2M+ trees planted by partner network"},
    {"category": "earth", "slug": "climate-action", "name": "Climate Action & Clean Energy", "featured": True,
     "short_desc": "Solar electrification, carbon offset and climate literacy across rural India.",
     "long_desc": "Tackling climate change at the village level — solar microgrids, energy access for the poor, and large-scale carbon offset programmes via verified partners.",
     "image_url": "https://images.unsplash.com/photo-1466611653911-95081537e5b7?w=1200",
     "impact_metric": "120K rural homes solar-powered"},
    {"category": "earth", "slug": "clean-water", "name": "Clean Rivers & Oceans", "featured": False,
     "short_desc": "River clean-ups, coastal protection and sustainable waste management.",
     "long_desc": "From the Ganga and Yamuna to India's 7,500 km coastline, restoration partners need fuel for the long-haul work of recovering our waters.",
     "image_url": "https://images.unsplash.com/photo-1583212292454-1fe6229603b7?w=1200",
     "impact_metric": "8,400 tonnes of plastic recovered"},
    # ── Animal ──
    {"category": "animal", "slug": "stray-care", "name": "Stray Care & Sterilisation", "featured": True,
     "short_desc": "Sterilisation, vaccination and shelter for India's stray dogs and cats.",
     "long_desc": "Compassionate ABC (animal birth control) campaigns and round-the-clock shelters that turn the tide on stray suffering.",
     "image_url": "https://images.unsplash.com/photo-1583511655802-41700a4e1953?w=1200",
     "impact_metric": "90K animals sterilised annually"},
    {"category": "animal", "slug": "wildlife-rescue", "name": "Wildlife Rescue & Rehabilitation", "featured": True,
     "short_desc": "Rescue elephants, bears, leopards and reptiles — rehabilitate, release where possible.",
     "long_desc": "Specialised teams across India that respond to wildlife crises — from rescuing dancing bears to relocating leopards out of urban India.",
     "image_url": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1200",
     "impact_metric": "2,300+ animals rescued"},
    {"category": "animal", "slug": "avian-marine", "name": "Avian & Marine Sanctuary", "featured": False,
     "short_desc": "Bird hospitals, sea turtle conservation and reef protection.",
     "long_desc": "Vulnerable creatures — Olive Ridley turtles, urban birds, coral reefs of the Andamans — protected by dedicated, under-funded teams.",
     "image_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=1200",
     "impact_metric": "44K turtle hatchlings released"},
    # ── Human ──
    {"category": "human", "slug": "education-for-all", "name": "Education for Every Child", "featured": True,
     "short_desc": "Mid-day meals, foundational literacy and teacher training across underserved schools.",
     "long_desc": "Programmes that put a hot meal, a competent teacher and an early reading start in front of every Indian child — the surest path out of poverty.",
     "image_url": "https://images.unsplash.com/photo-1497486751825-1233686d5d80?w=1200",
     "impact_metric": "5M+ children supported each year"},
    {"category": "human", "slug": "womens-health", "name": "Women's Health & Livelihood", "featured": True,
     "short_desc": "Menstrual hygiene, women's shelters and self-employed livelihoods.",
     "long_desc": "Anchored in self-help groups and shelters, these programmes restore dignity and economic independence to women across rural and urban India.",
     "image_url": "https://images.unsplash.com/photo-1573497019418-b400bb3ab074?w=1200",
     "impact_metric": "1.8M women in self-help groups"},
    {"category": "human", "slug": "hunger-relief", "name": "Hunger Relief & Elder Care", "featured": False,
     "short_desc": "Community kitchens, food banking and care for the elderly.",
     "long_desc": "Direct, dignified hunger relief — including India's most loved volunteer-run kitchens and food banks — and care for our forgotten elderly.",
     "image_url": "https://images.unsplash.com/photo-1593113598332-cd288d649433?w=1200",
     "impact_metric": "12M meals served yearly"},
]

# slug → list of 4 beneficiaries
SEED_BENEFICIARIES = {
    "forest-wildlife": [
        {"name": "SankalpTaru Foundation", "type": "ngo", "city": "Haridwar", "state": "Uttarakhand", "lat": 29.9457, "lng": 78.1642,
         "description": "Plants native tree species across 27 states with geotagged tracking.", "established": "2013",
         "website": "sankalptaru.org",
         "image_url": "https://images.unsplash.com/photo-1444930694458-01babe71870e?w=1000"},
        {"name": "Project Tiger Fund", "type": "foundation", "city": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882,
         "description": "Patrols, anti-poaching units and habitat work across Tiger Reserves.", "established": "1973",
         "website": "ntca.gov.in",
         "image_url": "https://images.unsplash.com/photo-1561731216-c3a4d99437d5?w=1000"},
        {"name": "Wildlife Trust of India", "type": "ngo", "city": "Noida", "state": "Uttar Pradesh", "lat": 28.5355, "lng": 77.3910,
         "description": "Rescues displaced wildlife and runs elephant corridors.", "established": "1998",
         "website": "wti.org.in",
         "image_url": "https://images.unsplash.com/photo-1564349683136-77e08dba1ef7?w=1000"},
        {"name": "Junglescapes", "type": "ngo", "city": "Bandipur", "state": "Karnataka", "lat": 11.6717, "lng": 76.6286,
         "description": "Restores degraded forest corridors at the edges of Bandipur & Nagarhole.", "established": "2010",
         "website": "junglescapes.org",
         "image_url": "https://images.unsplash.com/photo-1511497584788-876760111969?w=1000"},
    ],
    "climate-action": [
        {"name": "SELCO Foundation", "type": "foundation", "city": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946,
         "description": "Solar electrification for the rural poor — schools, clinics, livelihoods.", "established": "2010",
         "website": "selcofoundation.org",
         "image_url": "https://images.unsplash.com/photo-1509391366360-2e959784a276?w=1000"},
        {"name": "Centre for Sustainable Development", "type": "foundation", "city": "Bengaluru", "state": "Karnataka", "lat": 12.9352, "lng": 77.6245,
         "description": "Designs solar villages and trains rural women as energy entrepreneurs.", "established": "2008",
         "website": "csd.org.in",
         "image_url": "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=1000"},
        {"name": "Plan B Earth Initiative", "type": "ngo", "city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567,
         "description": "Carbon offset via verified urban afforestation and waste-to-energy.", "established": "2017",
         "website": "planbearth.in",
         "image_url": "https://images.unsplash.com/photo-1532601224476-15c79f2f7a51?w=1000"},
        {"name": "Climate Reality Project India", "type": "ngo", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090,
         "description": "Trains thousands of climate leaders across India each year.", "established": "2017",
         "website": "climaterealityindia.org",
         "image_url": "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=1000"},
    ],
    "clean-water": [
        {"name": "Ganga Action Foundation", "type": "foundation", "city": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lng": 82.9739,
         "description": "Riverbank clean-ups, awareness yatras and effluent monitoring along the Ganga.", "established": "2013",
         "website": "gangaaction.org",
         "image_url": "https://images.unsplash.com/photo-1545048702-79362596cdc9?w=1000"},
        {"name": "Hasiru Dala", "type": "ngo", "city": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946,
         "description": "Waste-pickers' cooperative — formalising livelihoods, recycling 1,000+ tonnes/month.", "established": "2010",
         "website": "hasirudala.in",
         "image_url": "https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?w=1000"},
        {"name": "The Indian Coastal Trust", "type": "ngo", "city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707,
         "description": "Coastal clean-ups and mangrove restoration along India's east coast.", "established": "2015",
         "website": "coastalindia.org",
         "image_url": "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?w=1000"},
        {"name": "Yamuna Mission", "type": "ngo", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2810,
         "description": "Citizen-led monitoring, drain interception and restoration along the Yamuna.", "established": "2019",
         "website": "yamunamission.in",
         "image_url": "https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=1000"},
    ],
    "stray-care": [
        {"name": "Friendicoes SECA", "type": "hospital", "city": "New Delhi", "state": "Delhi", "lat": 28.5535, "lng": 77.2588,
         "description": "Shelter, hospital and ambulance for street animals — runs since 1979.", "established": "1979",
         "website": "friendicoes.org",
         "image_url": "https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=1000"},
        {"name": "PFA Hyderabad", "type": "hospital", "city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867,
         "description": "ABC sterilisation centre and 24/7 animal ambulance for Hyderabad's strays.", "established": "1996",
         "website": "pfahyderabad.com",
         "image_url": "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=1000"},
        {"name": "CUPA — Compassion Unlimited Plus Action", "type": "ngo", "city": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946,
         "description": "Rehab centre, second-chance adoption and ABC across Bengaluru.", "established": "1991",
         "website": "cupabangalore.org",
         "image_url": "https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=1000"},
        {"name": "Welfare of Stray Dogs (WSD)", "type": "ngo", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777,
         "description": "Pioneered the ABC model in Mumbai — over 100K sterilisations to date.", "established": "1989",
         "website": "wsdindia.org",
         "image_url": "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=1000"},
    ],
    "wildlife-rescue": [
        {"name": "Wildlife SOS", "type": "ngo", "city": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lng": 78.0081,
         "description": "Rescued every dancing bear in India; now runs the world's largest elephant rehab.", "established": "1995",
         "website": "wildlifesos.org",
         "image_url": "https://images.unsplash.com/photo-1466721591366-2d5fba72006d?w=1000"},
        {"name": "Madras Crocodile Bank Trust", "type": "ngo", "city": "Chennai", "state": "Tamil Nadu", "lat": 12.7990, "lng": 80.2502,
         "description": "Reptile conservation, research and the world's largest crocodile breeding centre.", "established": "1976",
         "website": "madrascrocodilebank.org",
         "image_url": "https://images.unsplash.com/photo-1583511666372-62fc211f8377?w=1000"},
        {"name": "BSPCA Mumbai", "type": "hospital", "city": "Mumbai", "state": "Maharashtra", "lat": 18.9750, "lng": 72.8258,
         "description": "Bombay Society for Prevention of Cruelty to Animals — full-service hospital since 1874.", "established": "1874",
         "website": "thebspca.org",
         "image_url": "https://images.unsplash.com/photo-1583336663277-620dc1996580?w=1000"},
        {"name": "Wildlife Conservation Trust", "type": "foundation", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777,
         "description": "Tiger landscape conservation and forest staff welfare across 23 reserves.", "established": "2002",
         "website": "wildlifeconservationtrust.org",
         "image_url": "https://images.unsplash.com/photo-1551244072-5d12893278ab?w=1000"},
    ],
    "avian-marine": [
        {"name": "Jivdaya Charitable Trust", "type": "hospital", "city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714,
         "description": "Jain-run sanctuary and hospital — handles 60K+ injured birds yearly.", "established": "1995",
         "website": "jivdayatrust.org",
         "image_url": "https://images.unsplash.com/photo-1444930694458-01babe71870e?w=1000"},
        {"name": "Olive Ridley Conservation Project", "type": "ngo", "city": "Puri", "state": "Odisha", "lat": 19.8135, "lng": 85.8312,
         "description": "Patrols the Gahirmatha beach, India's largest Olive Ridley turtle rookery.", "established": "2003",
         "website": "oliveridleyproject.org",
         "image_url": "https://images.unsplash.com/photo-1573865526739-10c1d24aef3f?w=1000"},
        {"name": "Charity Birds Hospital Delhi", "type": "hospital", "city": "New Delhi", "state": "Delhi", "lat": 28.6519, "lng": 77.2315,
         "description": "Jain-run avian hospital at Digambar Jain Lal Mandir, treating ~15K birds a year.", "established": "1956",
         "website": "charitybirdshospital.org",
         "image_url": "https://images.unsplash.com/photo-1444930694458-01babe71870e?w=1000"},
        {"name": "ReefWatch Marine Conservation", "type": "ngo", "city": "Port Blair", "state": "Andaman & Nicobar", "lat": 11.6234, "lng": 92.7265,
         "description": "Coral reef restoration in the Andamans — first coral nursery in India.", "established": "1993",
         "website": "reefwatchindia.org",
         "image_url": "https://images.unsplash.com/photo-1535930891776-0c2dfb7fda1a?w=1000"},
    ],
    "education-for-all": [
        {"name": "Pratham Education Foundation", "type": "foundation", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777,
         "description": "India's largest learning programme — ASER report and foundational literacy.", "established": "1995",
         "website": "pratham.org",
         "image_url": "https://images.unsplash.com/photo-1497486751825-1233686d5d80?w=1000"},
        {"name": "Akshaya Patra Foundation", "type": "foundation", "city": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946,
         "description": "World's largest mid-day meal NGO — serves 2M+ school children daily.", "established": "2000",
         "website": "akshayapatra.org",
         "image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=1000"},
        {"name": "Teach For India", "type": "ngo", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777,
         "description": "Two-year teaching fellowship in low-income classrooms across 8 cities.", "established": "2008",
         "website": "teachforindia.org",
         "image_url": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1000"},
        {"name": "CRY — Child Rights and You", "type": "foundation", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090,
         "description": "Restoring childhoods — fights child labour, child marriage, supports education.", "established": "1979",
         "website": "cry.org",
         "image_url": "https://images.unsplash.com/photo-1497375638960-ca368c7231e4?w=1000"},
    ],
    "womens-health": [
        {"name": "SEWA — Self-Employed Women's Association", "type": "foundation", "city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714,
         "description": "Trade union of 2M+ self-employed women workers across India.", "established": "1972",
         "website": "sewa.org",
         "image_url": "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=1000"},
        {"name": "Goonj", "type": "ngo", "city": "New Delhi", "state": "Delhi", "lat": 28.5450, "lng": 77.1928,
         "description": "Dignity-driven dispatch — clothes, menstrual hygiene kits, disaster relief.", "established": "1999",
         "website": "goonj.org",
         "image_url": "https://images.unsplash.com/photo-1532629345422-7515f3d16bb6?w=1000"},
        {"name": "Snehalaya", "type": "ngo", "city": "Ahmednagar", "state": "Maharashtra", "lat": 19.0948, "lng": 74.7480,
         "description": "Rehabilitation for women & children rescued from human trafficking.", "established": "1989",
         "website": "snehalaya.org",
         "image_url": "https://images.unsplash.com/photo-1559027615-cd4628902d4a?w=1000"},
        {"name": "Sangini Trust", "type": "ngo", "city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777,
         "description": "Maternal health and adolescent girls' wellbeing in urban slums.", "established": "2002",
         "website": "saheli-women.org",
         "image_url": "https://images.unsplash.com/photo-1573497019418-b400bb3ab074?w=1000"},
    ],
    "hunger-relief": [
        {"name": "Robin Hood Army", "type": "ngo", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090,
         "description": "Zero-funds volunteer army that redistributes surplus food in 400+ cities.", "established": "2014",
         "website": "robinhoodarmy.com",
         "image_url": "https://images.unsplash.com/photo-1593113598332-cd288d649433?w=1000"},
        {"name": "India Food Banking Network", "type": "foundation", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090,
         "description": "National food banking network — rescues and redistributes food to NGOs.", "established": "2012",
         "website": "indiafoodbanking.org",
         "image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=1000"},
        {"name": "HelpAge India", "type": "foundation", "city": "New Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090,
         "description": "Elder care: helplines, mobile healthcare units and elder homes.", "established": "1978",
         "website": "helpageindia.org",
         "image_url": "https://images.unsplash.com/photo-1518398046578-8cca57782e17?w=1000"},
        {"name": "Goonj Disaster Aid", "type": "ngo", "city": "New Delhi", "state": "Delhi", "lat": 28.5450, "lng": 77.1928,
         "description": "Rapid disaster aid — Kerala, Sikkim, Uttarakhand and beyond.", "established": "1999",
         "website": "goonj.org",
         "image_url": "https://images.unsplash.com/photo-1525373698358-041e3a460346?w=1000"},
    ],
}


async def seed_causes_and_beneficiaries():
    if await db.causes.count_documents({}) > 0:
        return
    cause_docs = []
    cause_id_by_slug = {}
    for c in SEED_CAUSES:
        cid = str(uuid.uuid4())
        cause_id_by_slug[c["slug"]] = cid
        cause_docs.append({"id": cid, **c})
    await db.causes.insert_many([c.copy() for c in cause_docs])
    logging.info("Seeded %d causes", len(cause_docs))

    ben_docs = []
    for slug, items in SEED_BENEFICIARIES.items():
        cid = cause_id_by_slug.get(slug)
        cat = next((c["category"] for c in SEED_CAUSES if c["slug"] == slug), None)
        if not cid or not cat:
            continue
        for b in items:
            ben_id = str(uuid.uuid4())
            safe = "".join(ch for ch in b["name"].lower() if ch.isalnum())[:24]
            partner_email = f"partner.{safe}@mandala.in"
            partner_id = str(uuid.uuid4())
            await db.users.insert_one({
                "id": partner_id,
                "name": f"Partner - {b['name']}",
                "email": partner_email,
                "password_hash": hash_password("partner123"),
                "role": "partner",
                "beneficiary_id": None,
                "created_at": iso(now_utc()),
            })
            ben_docs.append({
                "id": ben_id,
                "category": cat,
                "name": b["name"],
                "type": b["type"],
                "cause_ids": [cid],
                "admin_user_id": partner_id,
                "city": b["city"],
                "state": b["state"],
                "country": b.get("country", "India"),
                "description": b["description"],
                "image_url": b["image_url"],
                "established": b.get("established"),
                "website": b.get("website"),
                "lat": b.get("lat"),
                "lng": b.get("lng"),
            })
            await db.users.update_one({"id": partner_id}, {"$set": {"beneficiary_id": ben_id}})
    if ben_docs:
        await db.beneficiaries.insert_many([b.copy() for b in ben_docs])
        logging.info("Seeded %d beneficiaries", len(ben_docs))


# ────────── App wiring ──────────
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    try:
        await seed_database()
        await seed_causes_and_beneficiaries()
    except Exception:
        logger.exception("Seeding failed")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
