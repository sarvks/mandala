import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer
      data-testid="main-footer"
      className="mt-32 border-t border-stone-200/70 bg-[#1A2436] text-[#F9F6F0]"
    >
      <div className="mx-auto grid max-w-7xl gap-12 px-6 py-16 md:grid-cols-4 md:px-10">
        <div className="md:col-span-2">
          <div className="flex items-center gap-3">
            <svg width="28" height="28" viewBox="0 0 32 32">
              <g fill="none" stroke="#D4AF37" strokeWidth="1.2">
                <circle cx="16" cy="16" r="14" />
                <circle cx="16" cy="16" r="9" />
                <circle cx="16" cy="16" r="4" />
              </g>
            </svg>
            <span className="font-serif text-2xl">Mandala</span>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/70">
            The financial layer of Indic religions. One deity. One payment link.
            Split donations to all associated temples — transparently, devotionally.
          </p>
          <p className="mt-6 text-xs uppercase tracking-[0.28em] text-white/40">
            Shaktism · Shaivism · Lakshmi · Buddhism · Jainism · Sikhism
          </p>
        </div>
        <div>
          <div className="label-small mb-4 text-white/50">Discover</div>
          <ul className="space-y-2 text-sm text-white/75">
            <li><Link to="/deities" className="hover:text-[#D4AF37]">Deities</Link></li>
            <li><Link to="/traditions" className="hover:text-[#D4AF37]">Traditions</Link></li>
            <li><Link to="/patron" className="hover:text-[#D4AF37]">Patron plans</Link></li>
          </ul>
        </div>
        <div>
          <div className="label-small mb-4 text-white/50">Account</div>
          <ul className="space-y-2 text-sm text-white/75">
            <li><Link to="/login" className="hover:text-[#D4AF37]">Login</Link></li>
            <li><Link to="/signup" className="hover:text-[#D4AF37]">Create account</Link></li>
            <li><Link to="/dashboard" className="hover:text-[#D4AF37]">My donations</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-6 py-6 text-xs text-white/45 md:flex-row md:px-10">
          <span>© {new Date().getFullYear()} Mandala Sacred Systems</span>
          <span>Payments: Razorpay (test · mock)</span>
        </div>
      </div>
    </footer>
  );
}
