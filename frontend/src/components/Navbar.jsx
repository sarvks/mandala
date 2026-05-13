import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LogOut, Menu, X } from "lucide-react";
import { useState } from "react";

const navItem = ({ isActive }) =>
  `relative text-sm tracking-wide transition-colors ${
    isActive
      ? "text-[#7C191E]"
      : "text-[#1A2436]/80 hover:text-[#7C191E]"
  }`;

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const onLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header
      data-testid="main-navbar"
      className="sticky top-0 z-50 border-b border-stone-200/60 bg-white/70 backdrop-blur-xl"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-10">
        <Link
          to="/"
          data-testid="nav-logo"
          className="flex items-center gap-3"
        >
          <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
            <g fill="none" stroke="#7C191E" strokeWidth="1.2">
              <circle cx="16" cy="16" r="14" />
              <circle cx="16" cy="16" r="9" />
              <circle cx="16" cy="16" r="4" />
              {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => {
                const a = (i * Math.PI) / 4;
                return (
                  <line
                    key={i}
                    x1={16 + Math.cos(a) * 4}
                    y1={16 + Math.sin(a) * 4}
                    x2={16 + Math.cos(a) * 14}
                    y2={16 + Math.sin(a) * 14}
                  />
                );
              })}
            </g>
          </svg>
          <span className="font-serif text-2xl tracking-tight text-[#1A2436]">
            Mandala
          </span>
        </Link>

        <nav className="hidden items-center gap-9 md:flex">
          <NavLink to="/deities" data-testid="nav-deities" className={navItem}>
            Deities
          </NavLink>
          <NavLink to="/temples" data-testid="nav-temples" className={navItem}>
            Temples
          </NavLink>
          <NavLink to="/causes" data-testid="nav-causes" className={navItem}>
            Causes
          </NavLink>
          <NavLink to="/traditions" data-testid="nav-traditions" className={navItem}>
            Traditions
          </NavLink>
          <NavLink to="/patron" data-testid="nav-patron" className={navItem}>
            Become a Patron
          </NavLink>
          {user?.role === "super_admin" && (
            <NavLink to="/admin" data-testid="nav-admin" className={navItem}>
              Admin
            </NavLink>
          )}
          {user?.role === "temple_admin" && (
            <NavLink to="/partner" data-testid="nav-temple-admin" className={navItem}>
              Temple Desk
            </NavLink>
          )}
          {user?.role === "partner" && (
            <NavLink to="/partner" data-testid="nav-partner" className={navItem}>
              Partner Desk
            </NavLink>
          )}
          {user?.role === "donor" && (
            <NavLink to="/dashboard" data-testid="nav-dashboard" className={navItem}>
              My Dashboard
            </NavLink>
          )}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          {user ? (
            <>
              <span
                data-testid="nav-user-name"
                className="text-sm text-[#1A2436]/70"
              >
                {user.name}
              </span>
              <button
                onClick={onLogout}
                data-testid="nav-logout-btn"
                className="inline-flex items-center gap-2 rounded-full border border-[#1A2436]/20 px-4 py-2 text-sm transition hover:border-[#7C191E] hover:text-[#7C191E]"
              >
                <LogOut className="h-4 w-4" strokeWidth={1.5} /> Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                data-testid="nav-login-btn"
                className="text-sm text-[#1A2436]/80 hover:text-[#7C191E]"
              >
                Login
              </Link>
              <Link
                to="/signup"
                data-testid="nav-signup-btn"
                className="btn-crimson text-sm"
              >
                Create Account
              </Link>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen(!open)}
          data-testid="nav-menu-toggle"
          className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-stone-200 md:hidden"
        >
          {open ? (
            <X className="h-5 w-5" strokeWidth={1.5} />
          ) : (
            <Menu className="h-5 w-5" strokeWidth={1.5} />
          )}
        </button>
      </div>

      {open && (
        <div className="border-t border-stone-200 bg-white/95 px-6 py-6 md:hidden">
          <div className="flex flex-col gap-4">
            <Link to="/deities" data-testid="mobile-nav-deities" onClick={() => setOpen(false)}>
              Deities
            </Link>
            <Link to="/temples" data-testid="mobile-nav-temples" onClick={() => setOpen(false)}>
              Temples
            </Link>
            <Link to="/causes" data-testid="mobile-nav-causes" onClick={() => setOpen(false)}>
              Causes
            </Link>
            <Link to="/traditions" data-testid="mobile-nav-traditions" onClick={() => setOpen(false)}>
              Traditions
            </Link>
            <Link to="/patron" data-testid="mobile-nav-patron" onClick={() => setOpen(false)}>
              Become a Patron
            </Link>
            {user?.role === "donor" && (
              <Link to="/dashboard" data-testid="mobile-nav-dashboard" onClick={() => setOpen(false)}>
                My Dashboard
              </Link>
            )}
            {user?.role === "super_admin" && (
              <Link to="/admin" data-testid="mobile-nav-admin" onClick={() => setOpen(false)}>
                Admin
              </Link>
            )}
            {user?.role === "temple_admin" && (
              <Link to="/partner" data-testid="mobile-nav-temple-admin" onClick={() => setOpen(false)}>
                Temple Desk
              </Link>
            )}
            {user?.role === "partner" && (
              <Link to="/partner" data-testid="mobile-nav-partner" onClick={() => setOpen(false)}>
                Partner Desk
              </Link>
            )}
            {user ? (
              <button onClick={onLogout} data-testid="mobile-nav-logout" className="text-left text-[#7C191E]">
                Logout
              </button>
            ) : (
              <>
                <Link to="/login" data-testid="mobile-nav-login" onClick={() => setOpen(false)}>
                  Login
                </Link>
                <Link to="/signup" data-testid="mobile-nav-signup" onClick={() => setOpen(false)}>
                  Create Account
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
