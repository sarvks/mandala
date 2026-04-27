import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { MapPin, Search, ArrowUpRight, X } from "lucide-react";

export default function Temples() {
  const [temples, setTemples] = useState([]);
  const [deities, setDeities] = useState([]);
  const [traditions, setTraditions] = useState([]);
  const [loading, setLoading] = useState(true);

  const [query, setQuery] = useState("");
  const [stateFilter, setStateFilter] = useState("all");
  const [deityFilter, setDeityFilter] = useState("all");
  const [traditionFilter, setTraditionFilter] = useState("all");

  useEffect(() => {
    Promise.all([
      api.get("/temples"),
      api.get("/deities"),
      api.get("/traditions"),
    ]).then(([t, d, tr]) => {
      setTemples(t.data);
      setDeities(d.data);
      setTraditions(tr.data);
      setLoading(false);
    });
  }, []);

  const deityMap = useMemo(() => {
    const m = {};
    deities.forEach((d) => (m[d.id] = d));
    return m;
  }, [deities]);

  const states = useMemo(() => {
    const s = Array.from(new Set(temples.map((t) => t.state))).sort();
    return s;
  }, [temples]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return temples.filter((t) => {
      if (stateFilter !== "all" && t.state !== stateFilter) return false;
      if (deityFilter !== "all" && !t.deity_ids.includes(deityFilter)) return false;
      if (traditionFilter !== "all") {
        const match = t.deity_ids.some(
          (id) => deityMap[id]?.tradition_slug === traditionFilter
        );
        if (!match) return false;
      }
      if (q) {
        const hay = `${t.name} ${t.city} ${t.state} ${t.description} ${t.deity_ids
          .map((id) => deityMap[id]?.name || "")
          .join(" ")}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [temples, query, stateFilter, deityFilter, traditionFilter, deityMap]);

  const clearAll = () => {
    setQuery("");
    setStateFilter("all");
    setDeityFilter("all");
    setTraditionFilter("all");
  };

  const activeFilterCount =
    (stateFilter !== "all" ? 1 : 0) +
    (deityFilter !== "all" ? 1 : 0) +
    (traditionFilter !== "all" ? 1 : 0) +
    (query.trim() ? 1 : 0);

  return (
    <div data-testid="temples-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <header className="mb-12 max-w-2xl">
        <p className="label-small text-[#7C191E]">Sacred atlas</p>
        <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
          Every temple on Mandala.
        </h1>
        <p className="mt-5 text-[#475569]">
          Browse all {temples.length} sanctums by state, by deity or by
          tradition. Every temple on this list receives its fair share of every
          offering made to its deity.
        </p>
      </header>

      <div className="mb-6 grid gap-3 rounded-2xl border border-stone-200 bg-white p-5 md:grid-cols-12">
        <div className="relative md:col-span-4">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" strokeWidth={1.5} />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            data-testid="temples-search-input"
            placeholder="Search by name, city, deity…"
            className="w-full rounded-xl border border-stone-200 bg-white py-3 pl-10 pr-3 text-sm outline-none transition focus:border-[#7C191E]"
          />
        </div>
        <select
          value={traditionFilter}
          onChange={(e) => setTraditionFilter(e.target.value)}
          data-testid="temples-filter-tradition"
          className="rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm outline-none focus:border-[#7C191E] md:col-span-3"
        >
          <option value="all">All traditions</option>
          {traditions.map((t) => (
            <option key={t.slug} value={t.slug}>{t.name}</option>
          ))}
        </select>
        <select
          value={deityFilter}
          onChange={(e) => setDeityFilter(e.target.value)}
          data-testid="temples-filter-deity"
          className="rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm outline-none focus:border-[#7C191E] md:col-span-3"
        >
          <option value="all">All deities</option>
          {deities.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
        <select
          value={stateFilter}
          onChange={(e) => setStateFilter(e.target.value)}
          data-testid="temples-filter-state"
          className="rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm outline-none focus:border-[#7C191E] md:col-span-2"
        >
          <option value="all">All states</option>
          {states.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="mb-8 flex items-center justify-between text-sm text-[#475569]">
        <div data-testid="temples-result-count">
          Showing <span className="font-medium text-[#1A2436]">{filtered.length}</span> of {temples.length} temples
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={clearAll}
            data-testid="temples-clear-filters"
            className="inline-flex items-center gap-2 text-[#7C191E] hover:underline"
          >
            <X className="h-3.5 w-3.5" strokeWidth={1.5} /> Clear {activeFilterCount} filter{activeFilterCount > 1 ? "s" : ""}
          </button>
        )}
      </div>

      {loading ? (
        <div className="py-24 text-center text-[#475569]">Loading sanctums…</div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-stone-200 bg-white p-16 text-center">
          <div className="font-serif text-2xl text-[#1A2436]">No temples match your filters.</div>
          <p className="mt-2 text-sm text-[#475569]">Try clearing a filter or searching for a different city or deity.</p>
          <button
            onClick={clearAll}
            data-testid="temples-clear-filters-empty"
            className="btn-ghost-gold mt-6"
          >
            Reset filters
          </button>
        </div>
      ) : (
        <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((t) => {
            const primaryDeity = deityMap[t.deity_ids[0]];
            return (
              <article
                key={t.id}
                data-testid={`temple-list-card-${t.id}`}
                className="card-surface overflow-hidden"
              >
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={t.image_url}
                    alt={t.name}
                    loading="lazy"
                    className="h-full w-full object-cover transition-transform duration-[900ms] ease-out hover:scale-105"
                  />
                  <div className="absolute left-3 top-3 rounded-full bg-white/90 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-[#1A2436]">
                    {t.state}
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="font-serif text-xl leading-snug text-[#1A2436]">{t.name}</h3>
                  <div className="mt-2 flex items-center gap-2 text-sm text-[#475569]">
                    <MapPin className="h-4 w-4" strokeWidth={1.5} />
                    {t.city}, {t.state}
                  </div>
                  <p className="mt-3 line-clamp-2 text-sm text-[#475569]">{t.description}</p>

                  <div className="mt-5 flex items-center justify-between">
                    {primaryDeity ? (
                      <Link
                        to={`/deities/${primaryDeity.id}`}
                        data-testid={`temple-list-deity-${t.id}`}
                        className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-[#7C191E] hover:underline"
                      >
                        {primaryDeity.name}
                        <ArrowUpRight className="h-3.5 w-3.5" strokeWidth={1.5} />
                      </Link>
                    ) : (
                      <span />
                    )}
                    {t.established && (
                      <span className="label-small text-[#D4AF37]">Est. {t.established}</span>
                    )}
                  </div>

                  {primaryDeity && (
                    <Link
                      to={`/donate/${primaryDeity.id}`}
                      data-testid={`temple-list-donate-${t.id}`}
                      className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full border border-[#7C191E] px-5 py-2.5 text-sm font-medium text-[#7C191E] transition hover:bg-[#7C191E] hover:text-white"
                    >
                      Offer to {primaryDeity.name}
                    </Link>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
