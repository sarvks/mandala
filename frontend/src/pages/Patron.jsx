import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Check } from "lucide-react";

export default function Patron() {
  const [tiers, setTiers] = useState(null);
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    api.get("/patron-tiers").then((r) => setTiers(r.data));
    api.get("/deities", { params: { featured: true } }).then((r) => setFeatured(r.data));
  }, []);

  return (
    <div data-testid="patron-page" className="mx-auto max-w-6xl px-6 py-16 md:px-10">
      <header className="max-w-2xl">
        <p className="label-small text-[#7C191E]">Become a patron</p>
        <h1 className="mt-3 font-serif text-5xl leading-tight text-[#1A2436] sm:text-6xl">
          Sustain the temples. Month after month.
        </h1>
        <p className="mt-5 text-[#475569]">
          Choose a tier and an associated deity. Your monthly sankalp will be
          split automatically across every temple that carries its flame.
        </p>
      </header>

      {tiers && (
        <div className="mt-14 grid gap-6 sm:grid-cols-3">
          {Object.entries(tiers).map(([k, v]) => (
            <div
              key={k}
              data-testid={`patron-tier-${k}`}
              className="relative rounded-3xl border border-stone-200 bg-white p-8"
            >
              <div className="label-small text-[#D4AF37]">{v.name}</div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="font-serif text-5xl text-[#1A2436]">₹{v.amount.toLocaleString("en-IN")}</span>
                <span className="text-sm text-[#475569]">/ month</span>
              </div>
              <ul className="mt-6 space-y-3 text-sm text-[#1A2436]">
                {v.perks.map((p) => (
                  <li key={p} className="flex items-start gap-2">
                    <Check className="mt-0.5 h-4 w-4 text-[#7C191E]" strokeWidth={2} />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="mt-20">
        <p className="label-small text-[#7C191E]">Choose a deity to support</p>
        <h2 className="mt-3 font-serif text-3xl text-[#1A2436]">
          Pick a form of the divine and begin your monthly sankalp.
        </h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {featured.map((d) => (
            <Link
              key={d.id}
              to={`/subscribe/${d.id}`}
              data-testid={`patron-deity-${d.id}`}
              className="group flex items-center gap-4 rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-[#7C191E]"
            >
              <img src={d.image_url} alt={d.name} className="h-16 w-16 rounded-xl object-cover" />
              <div>
                <div className="font-serif text-lg text-[#1A2436]">{d.name}</div>
                <div className="label-small mt-1 text-[#7C191E] group-hover:underline">Subscribe →</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
