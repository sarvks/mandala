import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

export default function DeityCard({ deity, tradition }) {
  return (
    <Link
      to={`/deities/${deity.id}`}
      data-testid={`deity-card-${deity.id}`}
      className="group relative block overflow-hidden rounded-2xl border border-stone-200 bg-white transition-transform duration-500 hover:-translate-y-1"
    >
      <div className="relative aspect-[3/4] overflow-hidden bg-stone-100">
        <img
          src={deity.image_url}
          alt={deity.name}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-[1200ms] ease-out group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
        <div className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-[#1A2436]">
          {tradition || deity.tradition_slug}
        </div>
        <div className="absolute bottom-0 left-0 right-0 p-5 text-white">
          <div className="flex items-end justify-between">
            <h3 className="font-serif text-2xl leading-tight md:text-3xl">
              {deity.name}
            </h3>
            <ArrowUpRight
              className="h-5 w-5 translate-y-2 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100"
              strokeWidth={1.5}
            />
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-white/80">
            {deity.short_desc}
          </p>
        </div>
      </div>
    </Link>
  );
}
