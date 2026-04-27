# Mandala — Product Requirements Document

## Original Problem Statement
Build Mandala — "One Deity. One Payment Link. Split Donations to all the Temples associated with the deity." Dedicated to Goddess Durga across Shaktism, Shaivism, Lakshmi, Buddhism, Jainism, and Sikhism. The Financial Layer of Indic Religions.

## User Choices
- Full platform: landing + donation flow + admin + multi-tenant temple admin
- Razorpay integration: **MOCKED** (real keys to be swapped later)
- Donation split: **donor-chooses custom percentages** (sliders, lockable)
- Deity/temple data: **AI-generated** via Claude Sonnet 4.5 (Emergent Universal Key)
- Auth: email/password JWT
- Subscriptions: **both** recurring monthly + tiered patron plans (Bronze/Silver/Gold)

## Architecture
- Backend: FastAPI + motor (MongoDB). JWT (PyJWT + bcrypt). emergentintegrations for Claude.
- Frontend: React + React Router v7 + Tailwind + shadcn/ui + recharts + sonner toasts.
- Seed: 6 traditions, 8 deities, 20 temples, 1 super admin, 20 temple admins, 1 demo donor.

## Implemented (Feb 27, 2026)
### Backend
- `/api/auth/signup`, `/auth/login`, `/auth/me` — JWT flow with donor role
- `/api/traditions`, `/api/deities` (filter by tradition/featured), `/api/deities/{id}`, `/api/deities/{id}/temples`, `/api/temples`
- `/api/donations` (pending -> `/confirm` succeeded, mock Razorpay ref), `/api/donations/me`
- `/api/subscriptions` (monthly + tier), `/api/subscriptions/me`, cancel
- `/api/patron-tiers` (Bronze ₹501 / Silver ₹1501 / Gold ₹5001)
- `/api/admin/deities` (AI-generated via Claude Sonnet 4.5), `/api/admin/temples`
- `/api/admin/analytics` (total donations, MRR, top deities/temples, recent list, counts)
- `/api/admin/donations` — all donations
- `/api/temple-admin/overview` — temple-scoped donations with per-donation share
- Split validation (sum=100%, non-negative, amounts match total)
- Role guards: `require_role("super_admin" | "temple_admin")`

### Frontend
- `/` Landing: hero (mandala motif SVG), how-it-works 3-step, featured deities, traditions, patron tiers, CTA
- `/deities` — tradition filter chips, masonry grid
- `/deities/:id` — deity detail (mythology, mantra), temple cards
- `/donate/:deityId` — amount presets + custom, linked slider `SplitAllocator` (lockable rows, re-balancing), optional note, mock Razorpay 2-step confirm, success screen with transaction ref
- `/subscribe/:deityId` — toggle monthly vs tier, tier cards with perks, split allocator
- `/patron` — tier marketing + deity picker
- `/traditions` — six tradition cards with nested deity chips
- `/login`, `/signup`
- `/dashboard` — donor's donations table + subscriptions cards (cancel)
- `/admin` — Control-Room grid, 4 stat cards, BarChart (top deities), PieChart (top temples), recent donations table
- `/temple-admin` — temple detail, share totals, donation list

## Testing Status
- **Backend**: 23/23 pytest (auth, donations, subs, analytics, AI Claude, role guards) — 100%
- **Frontend**: all flows tested end-to-end — 100%
- **Payments**: MOCKED (Razorpay)

## Test Credentials
See `/app/memory/test_credentials.md`.

## Backlog / Next Actions
### P0 (user-ready)
- Swap mock Razorpay for live keys when user provides them (single env-var change; playbook routing already in place).
- Hardening: rate-limiting on `/auth/login` and `/donations`; rotate `JWT_SECRET`.

### P1 (enhancements)
- PDF 80G receipt email (via Resend/SMTP) on donation success.
- Cron-based subscription auto-charge (celery/APScheduler) — currently manual next_charge_at only.
- Donor-level anonymization toggle (offerings anonymous vs. on wall).
- Super admin deity/temple CRUD UI (endpoints exist; UI not built).
- Map view of temples by state.

### P2 (reach)
- Shareable offering cards (social proof / conversion loop).
- Patron-only content: monthly aartis, livestreams.
- Hindi / regional language toggle.
- Temple-admin payout reconciliation & UPI/bank settlement module.

## Known Gaps
- Razorpay is mocked; real money flow not live.
- AI-generated deity content cached once; no manual override UI yet for super admin.
- Subscription billing loop is simulated (single first charge recorded; no recurring job).
