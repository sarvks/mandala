import { useEffect, useState } from "react";
import { api } from "../lib/api";
import DeityCard from "../components/DeityCard";

export default function Deities() {
  const [deities, setDeities] = useState([]);
  const [traditions, setTraditions] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get("/traditions"), api.get("/deities")]).then(
      ([t, d]) => {
        setTraditions(t.data);
        setDeities(d.data);
        setLoading(false);
      }
    );
  }, []);

  const filtered = filter === "all" ? deities : deities.filter((d) => d.tradition_slug === filter);
  const tradName = (slug) => traditions.find((t) => t.slug === slug)?.name || slug;

  return (
    <div data-testid="deities-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <header className="mb-12 max-w-2xl">
        <p className="label-small text-[#7C191E]">The pantheon</p>
        <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
          Every form of the divine.
        </h1>
        <p className="mt-5 text-[#475569]">
          Explore deities across Shaktism, Shaivism, the Lakshmi tradition,
          Buddhism, Jainism and Sikhism. Choose one to offer to every temple that carries its flame.
        </p>
      </header>

      <div className="mb-10 flex flex-wrap gap-2" data-testid="tradition-filter-bar">
        <button
          onClick={() => setFilter("all")}
          data-testid="filter-all"
          className={`rounded-full border px-5 py-2 text-sm transition ${
            filter === "all"
              ? "border-[#7C191E] bg-[#7C191E] text-white"
              : "border-stone-300 bg-white text-[#1A2436] hover:border-[#7C191E]"
          }`}
        >
          All
        </button>
        {traditions.map((t) => (
          <button
            key={t.slug}
            onClick={() => setFilter(t.slug)}
            data-testid={`filter-${t.slug}`}
            className={`rounded-full border px-5 py-2 text-sm transition ${
              filter === t.slug
                ? "border-[#7C191E] bg-[#7C191E] text-white"
                : "border-stone-300 bg-white text-[#1A2436] hover:border-[#7C191E]"
            }`}
          >
            {t.name}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="py-24 text-center text-[#475569]">Gathering deities…</div>
      ) : (
        <div className="stagger grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {filtered.map((d) => (
            <DeityCard key={d.id} deity={d} tradition={tradName(d.tradition_slug)} />
          ))}
        </div>
      )}
    </div>
  );
}
