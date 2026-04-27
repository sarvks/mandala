import { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function Traditions() {
  const [traditions, setTraditions] = useState([]);
  const [deities, setDeities] = useState([]);

  useEffect(() => {
    Promise.all([api.get("/traditions"), api.get("/deities")]).then(([t, d]) => {
      setTraditions(t.data);
      setDeities(d.data);
    });
  }, []);

  return (
    <div data-testid="traditions-page" className="mx-auto max-w-6xl px-6 py-16 md:px-10">
      <header className="max-w-2xl">
        <p className="label-small text-[#7C191E]">Six sacred currents</p>
        <h1 className="mt-3 font-serif text-5xl text-[#1A2436] sm:text-6xl">
          The traditions Mandala serves.
        </h1>
      </header>
      <div className="mt-14 space-y-10">
        {traditions.map((t) => {
          const ds = deities.filter((d) => d.tradition_slug === t.slug);
          return (
            <section
              key={t.id}
              data-testid={`tradition-section-${t.slug}`}
              className="grid gap-8 rounded-3xl border border-stone-200 bg-white p-8 md:grid-cols-12"
            >
              <div className="md:col-span-4">
                <div className="flex items-center gap-3">
                  <span className="h-2 w-8 rounded-full" style={{ background: t.accent }} />
                  <div className="label-small text-[#7C191E]">{t.name}</div>
                </div>
                <h2 className="mt-3 font-serif text-3xl text-[#1A2436]">{t.name}</h2>
                <p className="mt-3 text-[#475569]">{t.description}</p>
              </div>
              <div className="md:col-span-8">
                <div className="grid gap-3 sm:grid-cols-2">
                  {ds.map((d) => (
                    <a
                      key={d.id}
                      href={`/deities/${d.id}`}
                      className="flex items-center gap-3 rounded-xl border border-stone-200 p-3 transition hover:border-[#7C191E]"
                    >
                      <img src={d.image_url} alt={d.name} className="h-12 w-12 rounded-lg object-cover" />
                      <div>
                        <div className="font-medium text-[#1A2436]">{d.name}</div>
                        <div className="text-xs text-[#475569] line-clamp-1">{d.short_desc}</div>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
