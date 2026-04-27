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
     "image_url": "https://images.unsplash.com/photo-1596402184320-417e7178b2cd?w=1200",
     "description": "Ancient cave shrine nestled in the Trikuta mountains, visited by millions of pilgrims.", "established": "c. 700 CE"},
    {"name": "Dakshineswar Kali Temple", "city": "Kolkata", "state": "West Bengal", "deity_name": "Goddess Durga",
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "Riverside Bhavatarini temple where Sri Ramakrishna worshipped the Mother.", "established": "1855"},
    {"name": "Kamakhya Temple", "city": "Guwahati", "state": "Assam", "deity_name": "Goddess Durga",
     "image_url": "https://images.unsplash.com/photo-1580100586938-02822d99c4a8?w=1200",
     "description": "Revered shakti peetha atop Nilachal Hill, one of the most sacred sites of the Mother.", "established": "c. 8th century"},
    {"name": "Chamundeshwari Temple", "city": "Mysuru", "state": "Karnataka", "deity_name": "Goddess Durga",
     "image_url": "https://images.unsplash.com/photo-1567367806137-842e61e5f21b?w=1200",
     "description": "Hilltop temple dedicated to Chamundeshwari, patron deity of the Wodeyars.", "established": "12th century"},
    {"name": "Kalighat Kali Temple", "city": "Kolkata", "state": "West Bengal", "deity_name": "Goddess Kali",
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "One of 51 Shakti Peethas, among India's oldest Kali shrines.", "established": "1809"},
    {"name": "Tarapith Temple", "city": "Birbhum", "state": "West Bengal", "deity_name": "Goddess Kali",
     "image_url": "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=1200",
     "description": "Tantric shrine of Tara, closely tied to the saint Bamakhepa.", "established": "c. 1225"},
    {"name": "Kashi Vishwanath", "city": "Varanasi", "state": "Uttar Pradesh", "deity_name": "Lord Shiva",
     "image_url": "https://images.unsplash.com/photo-1561361398-a8d1ecf5d85b?w=1200",
     "description": "Jyotirlinga on the ghats of the Ganga, heart of Kashi.", "established": "ancient"},
    {"name": "Brihadeeswarar Temple", "city": "Thanjavur", "state": "Tamil Nadu", "deity_name": "Lord Shiva",
     "image_url": "https://images.unsplash.com/photo-1582650625119-3a31f8fa2699?w=1200",
     "description": "UNESCO-listed Chola masterpiece, granite grandeur unrivalled.", "established": "1010 CE"},
    {"name": "Kedarnath Temple", "city": "Rudraprayag", "state": "Uttarakhand", "deity_name": "Lord Shiva",
     "image_url": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1200",
     "description": "Himalayan jyotirlinga accessible only half the year, a pilgrimage of the soul.", "established": "ancient"},
    {"name": "Mahalakshmi Temple Mumbai", "city": "Mumbai", "state": "Maharashtra", "deity_name": "Goddess Lakshmi",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Seaside temple of Mahalakshmi, Mahasaraswati and Mahakali.", "established": "1831"},
    {"name": "Padmavathi Temple", "city": "Tiruchanur", "state": "Andhra Pradesh", "deity_name": "Goddess Lakshmi",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Consort shrine of Tirupati, revered as Alamelu Mangamma.", "established": "ancient"},
    {"name": "Kolhapur Mahalakshmi", "city": "Kolhapur", "state": "Maharashtra", "deity_name": "Goddess Lakshmi",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "One of the Shakti Peethas, the Ambabai of Kolhapur.", "established": "7th century"},
    {"name": "Mahabodhi Temple", "city": "Bodh Gaya", "state": "Bihar", "deity_name": "Shakyamuni Buddha",
     "image_url": "https://images.pexels.com/photos/33466763/pexels-photo-33466763.jpeg?auto=compress&w=1200",
     "description": "UNESCO site at the place of the Buddha's awakening.", "established": "3rd century BCE"},
    {"name": "Sarnath Mulagandha Kuti Vihar", "city": "Sarnath", "state": "Uttar Pradesh", "deity_name": "Shakyamuni Buddha",
     "image_url": "https://images.pexels.com/photos/33466763/pexels-photo-33466763.jpeg?auto=compress&w=1200",
     "description": "Where the Buddha first turned the wheel of Dharma.", "established": "ancient"},
    {"name": "Rumtek Monastery", "city": "Gangtok", "state": "Sikkim", "deity_name": "Avalokiteshvara",
     "image_url": "https://images.unsplash.com/photo-1606293459310-6c9d53e3a1c3?w=1200",
     "description": "Seat of the Karmapa lineage, nestled in the eastern Himalayas.", "established": "1966"},
    {"name": "Tawang Monastery", "city": "Tawang", "state": "Arunachal Pradesh", "deity_name": "Avalokiteshvara",
     "image_url": "https://images.unsplash.com/photo-1606293459310-6c9d53e3a1c3?w=1200",
     "description": "Largest monastery in India, perched at 3000 m.", "established": "1680"},
    {"name": "Dilwara Temples", "city": "Mount Abu", "state": "Rajasthan", "deity_name": "Tirthankara Mahavira",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Marble masterwork of Jain devotion, built 11th to 13th centuries.", "established": "1031"},
    {"name": "Palitana Temples", "city": "Palitana", "state": "Gujarat", "deity_name": "Tirthankara Mahavira",
     "image_url": "https://images.unsplash.com/photo-1604608672516-f1b9b1d1c0c4?w=1200",
     "description": "Hundreds of shrines crowning Shatrunjaya Hill, Jainism's holiest peak.", "established": "ancient"},
    {"name": "Sri Harmandir Sahib Golden Temple", "city": "Amritsar", "state": "Punjab", "deity_name": "Guru Nanak Dev Ji",
     "image_url": "https://images.unsplash.com/photo-1609254819260-4baa6ac4e394?w=1200",
     "description": "Spiritual centre of Sikhi, gilded sanctum set within the Amrit Sarovar.", "established": "1604"},
    {"name": "Gurudwara Bangla Sahib", "city": "New Delhi", "state": "Delhi", "deity_name": "Guru Nanak Dev Ji",
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
            })
            await db.users.update_one({"id": admin_id}, {"$set": {"temple_id": temple_id}})
        if temples:
            await db.temples.insert_many([tt.copy() for tt in temples])
            logging.info("Seeded %d temples", len(temples))

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
    except Exception:
        logger.exception("Seeding failed")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
