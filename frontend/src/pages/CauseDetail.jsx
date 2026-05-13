import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import { MapPin, Repeat, HeartHandshake, ArrowUpRight, Globe } from "lucide-react";
import { CATEGORY_META } from "../components/CauseCard";
import FavouriteButton from "../components/FavouriteButton";

export default function CauseDetail() {
  const { id } = useParams();
  const [cause, setCause] = useState(null);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/causes/${id}`),
      api.get(`/causes/${id}/beneficiaries`),
    ]).then(([c, b]) => {
      setCause(c.data);
      setBeneficiaries(b.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="py-24 text-center text-[#475569]">Loading…</div>;
  if (!cause) return <div className="py-24 text-center text-[#475569]">Cause not found.</div>;
  const meta = CATEGORY_META[cause.category] || {};

  return (
    <div data-testid="cause-detail-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <div className="grid gap-12 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="relative aspect-[3/4] overflow-hidden rounded-3xl border border-stone-200">
            <img src={cause.image_url} alt={cause.name} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
            <div className="absolute left-6 top-6 inline-flex items-center gap-2 rounded-full bg-white/95 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-[#1A2436]">
              {meta.label || cause.category}
            </div>
          </div>
        </div>

        <div className="lg:col-span-7">
          <p className="label-small text-[#7C191E]">Mission</p>
          <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
            {cause.name}
          </h1>
          <p className="mt-6 text-lg text-[#1A2436]">{cause.short_desc}</p>
          <p className="mt-5 text-[#475569]">{cause.long_desc}</p>
          {cause.impact_metric && (
            <div className="mt-6 inline-block rounded-full bg-[#fdf7e4] px-4 py-2 text-sm text-[#7C191E]">
              <span className="font-medium">{cause.impact_metric}</span>
            </div>
          )}
          <div className="mt-10 flex flex-wrap gap-4">
            <Link to={`/cause-donate/${cause.id}`} data-testid="cause-donate-btn" className="btn-crimson inline-flex items-center gap-2">
              <HeartHandshake className="h-4 w-4" strokeWidth={1.5} /> Donate now
            </Link>
            <Link to={`/cause-subscribe/${cause.id}`} data-testid="cause-subscribe-btn" className="btn-ghost-gold inline-flex items-center gap-2">
              <Repeat className="h-4 w-4" strokeWidth={1.5} /> Monthly subscription
            </Link>
          </div>
        </div>
      </div>

      <section className="mt-24">
        <div className="mb-10 flex items-end justify-between">
          <div>
            <p className="label-small text-[#7C191E]">Partners receiving your offering</p>
            <h2 className="mt-3 font-serif text-4xl text-[#1A2436]">
              {beneficiaries.length} {beneficiaries.length === 1 ? "partner" : "partners"} on this mission.
            </h2>
          </div>
        </div>

        <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-2">
          {beneficiaries.map((b) => (
            <article key={b.id} data-testid={`beneficiary-card-${b.id}`} className="card-surface overflow-hidden">
              <div className="grid sm:grid-cols-5">
                <div className="relative h-44 sm:col-span-2 sm:h-full">
                  <img src={b.image_url} alt={b.name} className="h-full w-full object-cover" />
                  <div className="absolute right-3 top-3">
                    <FavouriteButton templeId={b.id} size="sm" />
                  </div>
                </div>
                <div className="p-6 sm:col-span-3">
                  <div className="label-small text-[#D4AF37]">{b.type}</div>
                  <h3 className="mt-1 font-serif text-xl text-[#1A2436]">{b.name}</h3>
                  <div className="mt-2 flex items-center gap-2 text-xs text-[#475569]">
                    <MapPin className="h-3.5 w-3.5" strokeWidth={1.5} />
                    {b.city}, {b.state}
                  </div>
                  <p className="mt-3 line-clamp-3 text-sm text-[#475569]">{b.description}</p>
                  <div className="mt-4 flex items-center justify-between">
                    {b.website && (
                      <a href={`https://${b.website.replace(/^https?:\/\//, "")}`} target="_blank" rel="noreferrer"
                         className="inline-flex items-center gap-1 text-xs uppercase tracking-[0.18em] text-[#7C191E] hover:underline">
                        <Globe className="h-3 w-3" strokeWidth={1.5} /> {b.website}
                      </a>
                    )}
                    {b.established && <span className="label-small text-[#D4AF37]">Est. {b.established}</span>}
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
