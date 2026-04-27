import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import DeityCard from "../components/DeityCard";
import MandalaMotif from "../components/MandalaMotif";
import { ArrowRight, ShieldCheck, Split, Repeat, Sparkles, Building2 } from "lucide-react";

export default function Landing() {
  const [featured, setFeatured] = useState([]);
  const [traditions, setTraditions] = useState([]);

  useEffect(() => {
    api.get("/deities", { params: { featured: true } }).then((r) => setFeatured(r.data));
    api.get("/traditions").then((r) => setTraditions(r.data));
  }, []);

  return (
    <div data-testid="landing-page">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute -right-32 -top-24 opacity-70">
          <MandalaMotif size={560} opacity={0.22} />
        </div>
        <div className="pointer-events-none absolute -left-40 top-80 opacity-50">
          <MandalaMotif size={360} stroke="#7C191E" opacity={0.18} />
        </div>
        <div className="mx-auto max-w-7xl px-6 pb-24 pt-20 md:px-10 md:pt-28">
          <div className="anim-fade-up grid gap-12 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <p className="label-small mb-6 flex items-center gap-3 text-[#7C191E]">
                <span className="h-px w-10 bg-[#D4AF37]" /> The Financial Layer of Indic Religions
              </p>
              <h1 className="font-serif text-5xl leading-[0.95] tracking-tight text-[#1A2436] sm:text-6xl lg:text-7xl">
                One Deity.
                <br />
                One Payment Link.
                <br />
                <span className="italic text-[#7C191E]">Many temples.</span>
              </h1>
              <p className="mt-8 max-w-xl text-lg leading-relaxed text-[#475569]">
                Mandala lets devotees give once to a deity and have the offering
                flow to every associated temple — from Vaishno Devi to
                Kamakhya, from Kashi to Kedarnath — in a split you decide.
              </p>

              <div className="mt-10 flex flex-wrap items-center gap-4">
                <Link to="/deities" data-testid="hero-explore-btn" className="btn-crimson inline-flex items-center gap-2">
                  Explore deities <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
                </Link>
                <Link to="/patron" data-testid="hero-patron-btn" className="btn-ghost-gold inline-flex items-center gap-2">
                  Become a patron
                </Link>
              </div>

              <div className="mt-14 grid max-w-lg grid-cols-3 gap-6 text-sm">
                <div>
                  <div className="font-serif text-3xl text-[#7C191E]">6</div>
                  <div className="label-small mt-1">Traditions</div>
                </div>
                <div>
                  <div className="font-serif text-3xl text-[#7C191E]">20+</div>
                  <div className="label-small mt-1">Temples</div>
                </div>
                <div>
                  <div className="font-serif text-3xl text-[#7C191E]">100%</div>
                  <div className="label-small mt-1">Transparent split</div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="relative h-[520px] overflow-hidden rounded-[28px] border border-stone-200 bg-white">
                <img
                  src="https://static.prod-images.emergentagent.com/jobs/b7b3f7f1-c01f-44f4-b4d4-194659322e25/images/fcbc44d487d0405f32e35926c635c9251f42774a936a7435ffb900085c3a6a2a.png"
                  alt="Sacred geometry"
                  className="absolute inset-0 h-full w-full object-cover"
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-white via-white/70 to-transparent p-8">
                  <div className="label-small text-[#7C191E]">Featured Darshan</div>
                  <div className="mt-2 font-serif text-3xl text-[#1A2436]">
                    Goddess Durga
                  </div>
                  <p className="mt-2 text-sm text-[#475569]">
                    Navaratri is coming — split your offering across four sacred Durga peethas in a single payment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section data-testid="how-it-works" className="border-y border-stone-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-24 md:px-10">
          <div className="mb-14 grid items-end gap-8 md:grid-cols-12">
            <div className="md:col-span-7">
              <p className="label-small text-[#7C191E]">How Mandala works</p>
              <h2 className="mt-4 font-serif text-4xl leading-tight text-[#1A2436] sm:text-5xl">
                A single sankalp, distributed across many sanctums.
              </h2>
            </div>
            <p className="text-[#475569] md:col-span-5">
              No donor should have to hunt for twenty temple websites. Choose a
              deity, choose your amount, choose how it splits — we route, reconcile and report.
            </p>
          </div>

          <div className="stagger grid gap-6 md:grid-cols-3">
            {[
              { icon: Sparkles, title: "Choose a deity", body: "Durga, Shiva, Lakshmi, Buddha, Mahavira, Guru Nanak and many more across six Indic traditions." },
              { icon: Split, title: "Set your split", body: "Slide across all temples associated with that deity. Lock the ones you want fixed, the rest re-balance automatically." },
              { icon: ShieldCheck, title: "Pay once, reach many", body: "One secure payment. Transparent reporting. A share statement for every rupee, every temple." },
            ].map(({ icon: Icon, title, body }, i) => (
              <div key={i} className="rounded-2xl border border-stone-200 bg-[#F9F6F0] p-8">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#7C191E]/10 text-[#7C191E]">
                  <Icon className="h-5 w-5" strokeWidth={1.5} />
                </div>
                <h3 className="mt-6 font-serif text-2xl text-[#1A2436]">{title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-[#475569]">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURED DEITIES */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 py-24 md:px-10">
          <div className="mb-12 flex items-end justify-between gap-6">
            <div>
              <p className="label-small text-[#7C191E]">Featured darshan</p>
              <h2 className="mt-3 font-serif text-4xl text-[#1A2436] sm:text-5xl">
                Begin with a form of the divine.
              </h2>
            </div>
            <Link to="/deities" data-testid="landing-view-all-deities" className="hidden text-sm uppercase tracking-[0.2em] text-[#7C191E] hover:underline md:inline">
              View all →
            </Link>
          </div>
          <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {featured.slice(0, 4).map((d) => (
              <DeityCard key={d.id} deity={d} tradition={d.tradition_slug} />
            ))}
          </div>
        </div>
      </section>

      {/* TRADITIONS */}
      <section className="bg-[#1A2436] text-white">
        <div className="mx-auto max-w-7xl px-6 py-24 md:px-10">
          <div className="grid gap-10 md:grid-cols-12">
            <div className="md:col-span-5">
              <p className="label-small text-[#D4AF37]">Six sacred currents</p>
              <h2 className="mt-4 font-serif text-4xl leading-tight sm:text-5xl">
                One financial layer, for every Indic tradition.
              </h2>
              <p className="mt-6 max-w-md text-white/70">
                Whether you worship Shakti or Shiva, chant mantras or recite
                banis, Mandala lets your offering reach the lineage you love.
              </p>
            </div>
            <div className="md:col-span-7">
              <div className="grid gap-4 sm:grid-cols-2">
                {traditions.map((t) => (
                  <div key={t.id} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6 transition hover:border-[#D4AF37]/40">
                    <div className="flex items-center gap-3">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: t.accent }}
                      />
                      <div className="font-serif text-xl">{t.name}</div>
                    </div>
                    <p className="mt-3 text-sm text-white/65">{t.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SUBSCRIPTION */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 py-24 md:px-10">
          <div className="grid items-center gap-12 md:grid-cols-12">
            <div className="md:col-span-5">
              <p className="label-small text-[#7C191E]">Become a patron</p>
              <h2 className="mt-3 font-serif text-4xl text-[#1A2436] sm:text-5xl">
                A monthly seva to the divine.
              </h2>
              <p className="mt-6 text-[#475569]">
                Set a monthly sankalp that recurs automatically — or choose a
                Bronze, Silver or Gold patron tier with special perks like
                prasad parcels, priority darshan invites and name-on-wall engraving.
              </p>
              <Link to="/patron" data-testid="landing-become-patron-btn" className="mt-8 inline-flex btn-crimson items-center gap-2">
                <Repeat className="h-4 w-4" strokeWidth={1.5} /> See patron plans
              </Link>
            </div>

            <div className="md:col-span-7">
              <div className="grid gap-4 sm:grid-cols-3">
                {[
                  { tier: "Bronze", amt: 501 },
                  { tier: "Silver", amt: 1501 },
                  { tier: "Gold", amt: 5001 },
                ].map(({ tier, amt }) => (
                  <div key={tier} className="card-surface p-6">
                    <div className="label-small text-[#D4AF37]">{tier}</div>
                    <div className="mt-3 flex items-baseline gap-2">
                      <span className="font-serif text-4xl text-[#1A2436]">₹{amt.toLocaleString("en-IN")}</span>
                      <span className="text-sm text-[#475569]">/ month</span>
                    </div>
                    <div className="mt-5 flex items-center gap-2 text-sm text-[#475569]">
                      <Building2 className="h-4 w-4" strokeWidth={1.5} />
                      Split across associated temples
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="border-t border-stone-200">
        <div className="mx-auto max-w-5xl px-6 py-24 text-center md:px-10">
          <MandalaMotif size={140} className="mx-auto opacity-70" />
          <h2 className="mt-8 font-serif text-4xl text-[#1A2436] sm:text-5xl">
            Offer with clarity. Give with reach.
          </h2>
          <p className="mt-6 text-[#475569]">
            One deity. One link. Every temple that keeps the flame lit.
          </p>
          <Link to="/deities" data-testid="landing-final-cta" className="btn-crimson mt-10 inline-flex items-center gap-2">
            Begin your offering <ArrowRight className="h-4 w-4" strokeWidth={1.5} />
          </Link>
        </div>
      </section>
    </div>
  );
}
