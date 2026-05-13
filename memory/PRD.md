# Mandala — Product Requirements Document

## Original Problem Statement
Build Mandala — "One Deity. One Payment Link. Split donations to all temples associated with the deity." The Financial Layer of Indic Religions.

## Implemented (Feb–May 2026)

### Phase 1 (MVP, Feb 2026)
- Deities (8) + Temples (20) seeded across 6 Indic traditions
- Donor JWT auth + signup/login
- Donation flow with custom-percentage SplitAllocator (lockable + re-balancing sliders)
- Subscriptions: monthly + Bronze/Silver/Gold patron tiers
- Donor dashboard, Super-admin analytics (recharts), Temple-admin desk
- Razorpay MOCK (creates pending → /confirm → succeeded)
- Claude Sonnet 4.5 (Emergent Universal Key) for AI deity content

### Phase 2 (Apr 2026)
- `/temples` directory + Grid/Map view toggle (Leaflet via CDN, per-state clustered markers)
- Favourite/heart button + Donor "My Temples" tab
- Festival notifications (13 seeded festivals matched via deity/tradition)
- Branding cleanup (Mandala title, badge removed from index.html)
- "Mahakali Tribunal" copyright

### Phase 3 (May 2026) — "Beyond the Temple"
- **Causes & Beneficiaries** — same one-link → many-recipients model extended to:
  - **Earth** (3 causes × 4 NGOs: SankalpTaru, Project Tiger Fund, SELCO, Ganga Action, etc.)
  - **Animals** (3 causes × 4 NGOs: Friendicoes, Wildlife SOS, BSPCA, Jivdaya, etc.)
  - **Humans** (3 causes × 4 NGOs: Pratham, Akshaya Patra, SEWA, Robin Hood Army, etc.)
- 9 Causes, 36 Beneficiaries, 36 Partner-admin accounts seeded
- New endpoints: `/api/causes`, `/api/causes/:id/beneficiaries`, `/api/cause-donations`, `/api/cause-subscriptions`
- **Unified Partner Portal** `/partner` — auto-detects role (`temple_admin` OR `partner`) and shows the right scope
- **Demo Accounts Panel** on `/login` — one-click sign-in for 6 demo roles
- Public endpoint `GET /api/demo-accounts` (will be feature-flagged before prod)
- Landing teaser section "Beyond the Temple" surfacing the three new categories

## Architecture
- Backend: FastAPI + motor (MongoDB). JWT + bcrypt. emergentintegrations for Claude.
- Frontend: React 19 + Tailwind + shadcn/ui + recharts + sonner + Leaflet (CDN).
- Seed: 6 traditions, 8 deities, 20 temples, 20 temple admins, 9 causes, 36 beneficiaries, 36 partner admins, 1 super admin, 1 demo donor.

## Test Credentials
See `/app/memory/test_credentials.md`. All 6 demo accounts authenticate. /api/demo-accounts returns them publicly.

## Testing Status
- 57 backend tests passing (23 MVP + 10 favourites + 24 causes/partner)
- All frontend flows verified end-to-end across 3 testing iterations

## Backlog
### P0 — production-readiness
- Swap mock Razorpay for real keys (single env switch)
- Feature-flag `/api/demo-accounts` (currently public — convenient for preview, must be removed for prod)
- Rotate JWT_SECRET; rate-limit /auth/login; harden CORS_ORIGINS
- Split server.py (~1565 lines) into routers: deity_router, cause_router, partner_router, seed.py

### P1 — feature
- DRY refactor: extract _aggregate_share() helper in /partner/overview; rename SplitItem.temple_id → recipient_id; extract <DonationReceipt/> shared component
- PDF 80G receipt email on donation success (Resend/SMTP)
- Cron-based subscription auto-charge (APScheduler) — currently only first charge logged
- Live lunar calendar for festivals
- Super-admin CRUD UI for causes/beneficiaries (endpoints exist; UI not built)
- Partners can edit their listing + upload payout proof

### P2 — growth
- Shareable offering cards (WhatsApp/Instagram export) after every donation
- Hindi / regional language toggle
- Map view for beneficiaries (we already have lat/lng)
- Festival-eve "double impact" auspiciousness banner
- Bank settlement & UPI payout reconciliation for partners
- Anonymous-vs-public donor wall

## Known Gaps / Caveats
- Razorpay is mocked; no real money flows
- /api/demo-accounts exposes credentials publicly (intentional for preview)
- 36 beneficiary names are real Indian NGOs included as illustrative DEMO partners — disclaimer banner shown on /causes page
- The "Made with Emergent" badge that appears in the live preview is platform-injected at request time; codebase contains no traces (verified via grep)
