import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { MapPin, ArrowRight, Repeat, HeartHandshake } from "lucide-react";
import FavouriteButton from "../components/FavouriteButton";

export default function DeityDetail() {
  const { id } = useParams();
  const [deity, setDeity] = useState(null);
  const [temples, setTemples] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/deities/${id}`),
      api.get(`/deities/${id}/temples`),
    ]).then(([d, t]) => {
      setDeity(d.data);
      setTemples(t.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="py-24 text-center text-[#475569]">Loading…</div>;
  if (!deity) return <div className="py-24 text-center text-[#475569]">Deity not found.</div>;

  return (
    <div data-testid="deity-detail-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <div className="grid gap-12 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="relative aspect-[3/4] overflow-hidden rounded-3xl border border-stone-200">
            <img src={deity.image_url} alt={deity.name} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
            <div className="absolute bottom-6 left-6 right-6">
              <div className="label-small rounded-full bg-white/90 px-3 py-1 text-center text-[#1A2436]" style={{ width: "max-content" }}>
                {deity.tradition_slug}
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-7">
          <p className="label-small text-[#7C191E]">Darshan</p>
          <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
            {deity.name}
          </h1>
          <p className="mt-6 text-lg text-[#1A2436]">{deity.short_desc}</p>
          <p className="mt-5 text-[#475569]">{deity.long_desc}</p>

          {deity.mantra && (
            <div className="mt-8 rounded-2xl border border-[#D4AF37]/40 bg-[#fdf7e4] p-6">
              <div className="label-small text-[#7C191E]">Mantra</div>
              <div className="mt-3 font-serif text-2xl italic text-[#1A2436]">“{deity.mantra}”</div>
            </div>
          )}

          {deity.mythology && (
            <div className="mt-8">
              <div className="label-small text-[#7C191E]">Mythology</div>
              <p className="mt-3 leading-relaxed text-[#475569]">{deity.mythology}</p>
            </div>
          )}

          <div className="mt-10 flex flex-wrap gap-4">
            <Link to={`/donate/${deity.id}`} data-testid="deity-donate-btn" className="btn-crimson inline-flex items-center gap-2">
              <HeartHandshake className="h-4 w-4" strokeWidth={1.5} /> Donate now
            </Link>
            <Link to={`/subscribe/${deity.id}`} data-testid="deity-subscribe-btn" className="btn-ghost-gold inline-flex items-center gap-2">
              <Repeat className="h-4 w-4" strokeWidth={1.5} /> Monthly subscription
            </Link>
          </div>
        </div>
      </div>

      <section className="mt-24">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <p className="label-small text-[#7C191E]">Associated sanctums</p>
            <h2 className="mt-3 font-serif text-4xl text-[#1A2436]">
              {temples.length} {temples.length === 1 ? "temple" : "temples"} carry this flame.
            </h2>
          </div>
          <Link to={`/donate/${deity.id}`} data-testid="deity-split-cta" className="hidden text-sm uppercase tracking-[0.2em] text-[#7C191E] hover:underline md:inline">
            Split your offering →
          </Link>
        </div>

        <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {temples.map((t) => (
            <article
              key={t.id}
              data-testid={`temple-card-${t.id}`}
              className="card-surface overflow-hidden"
            >
              <div className="relative h-44 overflow-hidden">
                <img src={t.image_url} alt={t.name} className="h-full w-full object-cover" />
                <div className="absolute right-3 top-3">
                  <FavouriteButton templeId={t.id} size="sm" />
                </div>
              </div>
              <div className="p-6">
                <h3 className="font-serif text-xl text-[#1A2436]">{t.name}</h3>
                <div className="mt-2 flex items-center gap-2 text-sm text-[#475569]">
                  <MapPin className="h-4 w-4" strokeWidth={1.5} />
                  {t.city}, {t.state}
                </div>
                <p className="mt-3 line-clamp-2 text-sm text-[#475569]">{t.description}</p>
                {t.established && (
                  <div className="label-small mt-4 text-[#D4AF37]">Est. {t.established}</div>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
