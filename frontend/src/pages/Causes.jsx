import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../lib/api";
import CauseCard, { CATEGORY_META } from "../components/CauseCard";
import { Leaf, PawPrint, HeartPulse } from "lucide-react";

const CATEGORIES = [
  { slug: "all", label: "All", color: "#7C191E" },
  { slug: "earth", label: "Earth", color: "#15803D", Icon: Leaf },
  { slug: "animal", label: "Animals", color: "#B45309", Icon: PawPrint },
  { slug: "human", label: "Humans", color: "#0E7490", Icon: HeartPulse },
];

export default function Causes() {
  const { category: urlCat } = useParams();
  const [causes, setCauses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState(urlCat || "all");

  useEffect(() => {
    api.get("/causes").then((r) => {
      setCauses(r.data);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (urlCat && CATEGORIES.some((c) => c.slug === urlCat)) setFilter(urlCat);
  }, [urlCat]);

  const filtered = useMemo(
    () => (filter === "all" ? causes : causes.filter((c) => c.category === filter)),
    [filter, causes]
  );

  return (
    <div data-testid="causes-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <header className="mb-12 max-w-2xl">
        <p className="label-small text-[#7C191E]">Beyond the temple</p>
        <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
          One link. <span className="italic text-[#7C191E]">Many causes.</span>
        </h1>
        <p className="mt-5 text-[#475569]">
          The same Mandala model — one payment link, split fairly across all
          partners — extended to Earth, Animal and Human-centric foundations
          across India.
        </p>
      </header>

      <div className="mb-10 flex flex-wrap gap-2" data-testid="cause-filter-bar">
        {CATEGORIES.map((c) => {
          const Icon = c.Icon;
          const active = filter === c.slug;
          return (
            <button
              key={c.slug}
              onClick={() => setFilter(c.slug)}
              data-testid={`cause-filter-${c.slug}`}
              className={`inline-flex items-center gap-2 rounded-full border px-5 py-2 text-sm transition ${
                active
                  ? "border-[#7C191E] bg-[#7C191E] text-white"
                  : "border-stone-300 bg-white text-[#1A2436] hover:border-[#7C191E]"
              }`}
            >
              {Icon && <Icon className="h-3.5 w-3.5" strokeWidth={1.6} style={{ color: active ? "#fff" : c.color }} />}
              {c.label}
            </button>
          );
        })}
      </div>

      {loading ? (
        <div className="py-24 text-center text-[#475569]">Gathering causes…</div>
      ) : (
        <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((c) => (
            <CauseCard key={c.id} cause={c} />
          ))}
        </div>
      )}

      <div className="mt-16 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <strong>Demo data:</strong> partner names shown above are real Indian
        non-profits we admire, included here as illustrative beneficiaries for
        the preview. Real disbursement will only begin once formal partnerships
        are signed and Razorpay routes are live.
      </div>
    </div>
  );
}
