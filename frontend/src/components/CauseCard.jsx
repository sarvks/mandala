import { Link } from "react-router-dom";
import { ArrowUpRight, Leaf, PawPrint, HeartPulse } from "lucide-react";

const CATEGORY_META = {
  earth: { label: "Earth", color: "#15803D", Icon: Leaf },
  animal: { label: "Animals", color: "#B45309", Icon: PawPrint },
  human: { label: "Humans", color: "#0E7490", Icon: HeartPulse },
};

export default function CauseCard({ cause }) {
  const meta = CATEGORY_META[cause.category] || { label: cause.category, color: "#7C191E" };
  const Icon = meta.Icon;
  return (
    <Link
      to={`/causes/${cause.id}`}
      data-testid={`cause-card-${cause.id}`}
      className="group relative block overflow-hidden rounded-2xl border border-stone-200 bg-white transition-transform duration-500 hover:-translate-y-1"
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-stone-100">
        <img src={cause.image_url} alt={cause.name} loading="lazy"
          className="h-full w-full object-cover transition-transform duration-[1200ms] ease-out group-hover:scale-105" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-transparent" />
        <div className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full bg-white/95 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-[#1A2436]">
          {Icon && <Icon className="h-3 w-3" strokeWidth={1.6} style={{ color: meta.color }} />}
          {meta.label}
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-5 text-white">
          <div className="flex items-end justify-between">
            <h3 className="font-serif text-2xl leading-tight md:text-3xl">{cause.name}</h3>
            <ArrowUpRight className="h-5 w-5 translate-y-2 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100" strokeWidth={1.5} />
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-white/80">{cause.short_desc}</p>
          {cause.impact_metric && (
            <div className="mt-3 text-xs uppercase tracking-[0.18em] text-[#E9D48B]">
              {cause.impact_metric}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}

export { CATEGORY_META };
