import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import DeityCard from "../components/DeityCard";
import CauseCard from "../components/CauseCard";
import MandalaMotif from "../components/MandalaMotif";
import SplitDiagram from "../components/SplitDiagram";
import {
  ArrowRight,
  ArrowUpRight,
  ShieldCheck,
  Leaf,
  PawPrint,
  HeartPulse,
  Sparkles,
  Quote,
  Building2,
  Globe,
} from "lucide-react";

const CATEGORIES = [
  { slug: "religion", label: "Religions", to: "/deities", Icon: Sparkles, color: "#7C191E",
    sub: "Deities · Temples", body: "Goddess Durga, Shiva, Lakshmi, Buddha, Mahavira, Guru Nanak." },
  { slug: "earth", label: "Earth", to: "/causes/category/earth", Icon: Leaf, color: "#15803D",
    sub: "Forests · Climate · Water", body: "SankalpTaru, Project Tiger, SELCO, Ganga Action." },
  { slug: "animal", label: "Animals", to: "/causes/category/animal", Icon: PawPrint, color: "#B45309",
    sub: "Strays · Wildlife · Marine", body: "Wildlife SOS, Friendicoes, BSPCA, Jivdaya Trust." },
  { slug: "human", label: "Humans", to: "/causes/category/human", Icon: HeartPulse, color: "#0E7490",
    sub: "Education · Health · Hunger", body: "Pratham, Akshaya Patra, SEWA, Robin Hood Army." },
];

const VOICES = [
  { quote: "I always wanted to give to every Kali Peetha. Mandala finally lets me do it in one breath.", who: "Anaita S.", role: "Donor · Mumbai" },
  { quote: "We received our first split share within minutes of the offering — fully transparent.", who: "SankalpTaru Foundation", role: "Earth partner" },
  { quote: "Navratri sankalp across four Durga shrines in a single payment — the way devotion was meant to scale.", who: "Devdutt B.", role: "Patron · Pune" },
];

function Counter({ value, suffix = "", duration = 1400 }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (!value) return;
    const start = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min(1, (t - start) / duration);
      setV(Math.floor(p * value));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return <span>{v.toLocaleString("en-IN")}{suffix}</span>;
}

export default function Landing() {
  const [featuredDeities, setFeaturedDeities] = useState([]);
  const [featuredCauses, setFeaturedCauses] = useState([]);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get("/deities", { params: { featured: true } }).then((r) => setFeaturedDeities(r.data));
    api.get("/causes", { params: { featured: true } }).then((r) => setFeaturedCauses(r.data));
    api.get("/stats/public").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  const featured = [...featuredDeities, ...featuredCauses].slice(0, 6);

  return (
    <div data-testid="landing-page">
      {/* ─────────── HERO ─────────── */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -right-44 -top-24 opacity-90">
          <MandalaMotif size={760} opacity={0.18} />
        </div>
        <div className="pointer-events-none absolute -left-32 top-[640px] opacity-70">
          <MandalaMotif size={420} stroke="#7C191E" opacity={0.13} />
        </div>

        <div className="mx-auto max-w-7xl px-6 pt-16 md:px-10 md:pt-24">
          {/* Eyebrow */}
          <div className="anim-fade-up flex items-center gap-3">
            <span className="h-px w-10 bg-[#D4AF37]" />
            <span className="label-small text-[#7C191E]">The Financial Layer of Indic Religions · and beyond</span>
          </div>

          {/* Headline */}
          <div className="anim-fade-up mt-7 grid items-end gap-10 lg:grid-cols-12">
            <h1 className="font-serif leading-[0.9] tracking-tight text-[#1A2436] lg:col-span-9 text-[60px] sm:text-[88px] lg:text-[120px]">
              One <em className="not-italic text-[#7C191E]">offering.</em>
              <br />
              Many <em className="text-[#7C191E]">sanctuaries.</em>
            </h1>
            <p className="text-lg leading-relaxed text-[#475569] lg:col-span-3">
              Mandala routes a single sankalp to every temple of a deity — and the same model to every Earth, animal and human foundation that needs it.
            </p>
          </div>

          {/* CTAs + Diagram */}
          <div className="mt-12 grid items-center gap-10 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <div className="flex flex-wrap items-center gap-4">
                <Link to="/deities" data-testid="hero-explore-btn" className="btn-crimson inline-flex items-center gap-2">
                  Offer to a deity <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
                </Link>
                <Link to="/causes" data-testid="hero-causes-btn" className="btn-ghost-gold inline-flex items-center gap-2">
                  Browse all causes
                </Link>
                <Link to="/login" data-testid="hero-demo-btn"
                  className="inline-flex items-center gap-2 text-sm uppercase tracking-[0.18em] text-[#1A2436] underline-offset-4 hover:underline">
                  Try the demo accounts →
                </Link>
              </div>

              {/* Live counter band */}
              <div className="mt-12 grid grid-cols-2 gap-y-8 border-t border-stone-200 pt-8 sm:grid-cols-4">
                <Stat label="Offerings routed" value={stats?.total_offerings ?? 0} />
                <Stat label="Temples" value={stats?.temples ?? 0} />
                <Stat label="Partner NGOs" value={stats?.beneficiaries ?? 0} />
                <Stat label="Traditions + causes" value={(stats?.deities ?? 0) + (stats?.causes ?? 0)} />
              </div>
            </div>

            <div className="hidden lg:col-span-5 lg:flex lg:justify-center">
              <SplitDiagram size={420} />
            </div>
          </div>
        </div>
      </section>

      {/* ─────────── MARQUEE — partner mentions ─────────── */}
      <section className="mt-24 border-y border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-8 px-6 py-6 md:px-10">
          <span className="label-small shrink-0 text-[#7C191E]">Routing offerings across</span>
          <div className="relative flex-1 overflow-hidden [mask-image:linear-gradient(to_right,transparent,#000_8%,#000_92%,transparent)]">
            <div className="flex animate-[scroll_38s_linear_infinite] gap-12 whitespace-nowrap pr-12 text-sm tracking-wide text-[#475569]">
              {[
                "Vaishno Devi", "Kashi Vishwanath", "Dakshineswar", "Kamakhya", "Kedarnath",
                "Mahalakshmi Mumbai", "Mahabodhi", "Golden Temple", "Tawang Monastery",
                "SankalpTaru", "Wildlife SOS", "Pratham", "Akshaya Patra", "SEWA",
                "Robin Hood Army", "SELCO", "Ganga Action", "Jivdaya Trust",
                "Friendicoes", "Goonj", "HelpAge India",
              ].concat([
                "Vaishno Devi", "Kashi Vishwanath", "Dakshineswar", "Kamakhya", "Kedarnath",
                "Mahalakshmi Mumbai", "Mahabodhi", "Golden Temple", "Tawang Monastery",
              ]).map((name, i) => (
                <span key={i} className="font-serif text-lg italic text-[#1A2436]">
                  {name}<span className="ml-12 text-[#D4AF37]">◆</span>
                </span>
              ))}
            </div>
          </div>
        </div>
        <style>{`@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}`}</style>
      </section>

      {/* ─────────── CATEGORIES HUB ─────────── */}
      <section className="relative" data-testid="landing-categories">
        <div className="mx-auto max-w-7xl px-6 py-28 md:px-10">
          <div className="mb-14 grid items-end gap-8 md:grid-cols-12">
            <div className="md:col-span-7">
              <p className="label-small text-[#7C191E]">Four currents · one mechanism</p>
              <h2 className="mt-4 font-serif text-5xl leading-[0.95] text-[#1A2436] sm:text-6xl">
                Religions. Earth.<br /> Animals. Humans.
              </h2>
            </div>
            <p className="text-[#475569] md:col-span-5">
              Pick the cause closest to your heart. Mandala handles the rest —
              splitting your offering across every partner that keeps the flame alive.
            </p>
          </div>

          <div className="stagger grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {CATEGORIES.map(({ slug, label, to, Icon, color, sub, body }) => (
              <Link
                key={slug}
                to={to}
                data-testid={`landing-category-${slug}`}
                className="group relative overflow-hidden rounded-3xl border border-stone-200 bg-white p-7 transition hover:-translate-y-1 hover:border-[#7C191E]"
              >
                <div
                  className="absolute -right-12 -top-12 h-44 w-44 rounded-full opacity-15 blur-2xl transition-opacity group-hover:opacity-30"
                  style={{ background: color }}
                />
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full"
                    style={{ background: `${color}1A`, color }}>
                    <Icon className="h-5 w-5" strokeWidth={1.6} />
                  </div>
                  <ArrowUpRight className="h-5 w-5 text-stone-300 transition-colors group-hover:text-[#7C191E]" strokeWidth={1.5} />
                </div>
                <div className="mt-6 label-small text-[#7C191E]">{sub}</div>
                <h3 className="mt-1 font-serif text-3xl text-[#1A2436]">{label}</h3>
                <p className="mt-3 text-sm leading-relaxed text-[#475569]">{body}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────── HOW THE SPLIT WORKS ─────────── */}
      <section className="border-y border-stone-200 bg-[#F1EDE5]">
        <div className="mx-auto max-w-7xl px-6 py-28 md:px-10">
          <div className="grid items-center gap-16 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <p className="label-small text-[#7C191E]">The mechanism</p>
              <h2 className="mt-4 font-serif text-5xl leading-tight text-[#1A2436]">
                One link · many sanctums.
              </h2>
              <p className="mt-6 text-[#475569]">
                Pick a deity or a cause. Set your amount. Drag the sliders to choose
                exactly how your offering splits — lock the ones you care about,
                let the rest re-balance automatically.
              </p>
              <ul className="mt-8 space-y-4 text-sm text-[#1A2436]">
                {[
                  ["01", "Choose any of 8 deities or 9 causes — across 4 currents."],
                  ["02", "Slide custom percentages across the associated temples / NGOs."],
                  ["03", "Pay once, securely. Every partner gets their share — instantly."],
                  ["04", "Track every rupee from your dashboard. Festival reminders included."],
                ].map(([n, t]) => (
                  <li key={n} className="flex items-start gap-4 rounded-2xl border border-stone-200 bg-white p-4">
                    <span className="font-mono text-xs text-[#7C191E]">{n}</span>
                    <span className="flex-1">{t}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="lg:col-span-7">
              <div className="relative flex h-[460px] items-center justify-center overflow-hidden rounded-3xl border border-stone-200 bg-white">
                <div className="absolute inset-0 opacity-30">
                  <MandalaMotif size={460} opacity={0.4} />
                </div>
                <SplitDiagram size={460} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────── FEATURED ROW ─────────── */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 py-28 md:px-10">
          <div className="mb-12 flex items-end justify-between gap-6">
            <div>
              <p className="label-small text-[#7C191E]">Featured darshan & missions</p>
              <h2 className="mt-3 font-serif text-5xl text-[#1A2436]">Begin with what calls you.</h2>
            </div>
            <div className="hidden gap-3 md:flex">
              <Link to="/deities" data-testid="landing-all-deities" className="text-sm uppercase tracking-[0.2em] text-[#7C191E] hover:underline">Deities →</Link>
              <Link to="/causes" data-testid="landing-all-causes" className="text-sm uppercase tracking-[0.2em] text-[#7C191E] hover:underline">Causes →</Link>
            </div>
          </div>
          <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {featured.slice(0, 3).map((d) => (
              <DeityCard key={d.id} deity={d} tradition={d.tradition_slug} />
            ))}
            {featuredCauses.slice(0, 3).map((c) => (
              <CauseCard key={c.id} cause={c} />
            ))}
          </div>
        </div>
      </section>

      {/* ─────────── TRUST · VOICES ─────────── */}
      <section className="bg-[#1A2436] text-white">
        <div className="mx-auto max-w-7xl px-6 py-28 md:px-10">
          <div className="grid items-center gap-12 lg:grid-cols-12">
            <div className="lg:col-span-4">
              <p className="label-small text-[#D4AF37]">Voices</p>
              <h2 className="mt-3 font-serif text-5xl leading-tight">
                Devotion at scale, dignity intact.
              </h2>
              <p className="mt-5 text-white/65">
                Donors, temples and NGOs from across the country, on what the Mandala mechanism unlocks.
              </p>
            </div>
            <div className="lg:col-span-8">
              <div className="grid gap-6 md:grid-cols-3">
                {VOICES.map((v, i) => (
                  <figure key={i} className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur">
                    <Quote className="h-5 w-5 text-[#D4AF37]" strokeWidth={1.5} />
                    <blockquote className="mt-4 font-serif text-xl italic leading-snug text-white">
                      “{v.quote}”
                    </blockquote>
                    <figcaption className="mt-6 border-t border-white/10 pt-4 text-sm">
                      <div className="text-white">{v.who}</div>
                      <div className="text-white/55">{v.role}</div>
                    </figcaption>
                  </figure>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────── PATRON / SUBSCRIPTION ─────────── */}
      <section>
        <div className="mx-auto max-w-7xl px-6 py-28 md:px-10">
          <div className="grid items-end gap-12 md:grid-cols-12">
            <div className="md:col-span-5">
              <p className="label-small text-[#7C191E]">Become a patron</p>
              <h2 className="mt-4 font-serif text-5xl leading-tight text-[#1A2436]">
                A monthly seva — to the divine, or the deserving.
              </h2>
              <p className="mt-6 text-[#475569]">
                Set a monthly sankalp that recurs automatically. Or pick a
                Bronze, Silver or Gold tier with prasad parcels, name-on-wall
                engraving and priority darshan invites.
              </p>
              <Link to="/patron" data-testid="landing-become-patron-btn" className="btn-crimson mt-8 inline-flex items-center gap-2">
                See patron plans <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
              </Link>
            </div>
            <div className="md:col-span-7">
              <div className="grid gap-4 sm:grid-cols-3">
                {[
                  { tier: "Bronze", amt: 501, perks: ["Monthly newsletter", "Digital blessing"] },
                  { tier: "Silver", amt: 1501, perks: ["+ Quarterly prasad", "Name on wall"] },
                  { tier: "Gold", amt: 5001, perks: ["+ Priority darshan", "Personal sankalp"] },
                ].map(({ tier, amt, perks }) => (
                  <div key={tier} className="card-surface p-6">
                    <div className="label-small text-[#D4AF37]">{tier}</div>
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="font-serif text-4xl text-[#1A2436]">₹{amt.toLocaleString("en-IN")}</span>
                      <span className="text-sm text-[#475569]">/ mo</span>
                    </div>
                    <ul className="mt-5 space-y-2 text-xs text-[#475569]">
                      {perks.map((p) => <li key={p}>· {p}</li>)}
                    </ul>
                    <div className="mt-6 flex items-center gap-2 text-xs text-[#475569]">
                      <Building2 className="h-3.5 w-3.5" strokeWidth={1.5} />
                      Splits monthly across associated partners
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────── TRUST BAND ─────────── */}
      <section className="border-y border-stone-200 bg-[#F9F6F0]">
        <div className="mx-auto grid max-w-7xl items-center gap-6 px-6 py-10 text-sm text-[#475569] md:grid-cols-3 md:px-10">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-[#7C191E]" strokeWidth={1.5} />
            Razorpay-secured · PCI compliant · UPI / Cards / Netbanking
          </div>
          <div className="flex items-center gap-3">
            <Globe className="h-5 w-5 text-[#7C191E]" strokeWidth={1.5} />
            36 partner NGOs · 20 temples · 6 Indic traditions
          </div>
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-[#7C191E]" strokeWidth={1.5} />
            80G receipts on the way · transparent splits, instant reconciliation
          </div>
        </div>
      </section>

      {/* ─────────── FINAL CTA ─────────── */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 flex justify-center opacity-50">
          <MandalaMotif size={520} opacity={0.4} />
        </div>
        <div className="mx-auto max-w-4xl px-6 py-32 text-center md:px-10">
          <p className="label-small text-[#7C191E]">A single sankalp · a thousand sanctums</p>
          <h2 className="mt-6 font-serif text-6xl leading-[0.92] text-[#1A2436] sm:text-7xl">
            Offer once.
            <br />
            <em className="not-italic text-[#7C191E]">Reach everywhere.</em>
          </h2>
          <p className="mx-auto mt-7 max-w-xl text-[#475569]">
            Whether you give to Goddess Durga, to a Himalayan forest, to a stray hospital or to a child in school — Mandala makes it one click, one link, one act.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link to="/deities" data-testid="landing-final-cta" className="btn-crimson inline-flex items-center gap-2">
              Begin with a deity <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
            </Link>
            <Link to="/causes" data-testid="landing-final-cta-causes" className="btn-ghost-gold inline-flex items-center gap-2">
              Begin with a cause
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div>
      <div className="font-serif text-3xl text-[#7C191E] sm:text-4xl">
        <Counter value={Number(value) || 0} />
      </div>
      <div className="mt-1 text-xs uppercase tracking-[0.22em] text-[#475569]">{label}</div>
    </div>
  );
}
