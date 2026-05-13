import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";

export default function DemoAccountsPanel() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/demo-accounts").then((r) => setAccounts(r.data));
  }, []);

  const oneClick = async (a) => {
    setLoading(a.email);
    try {
      const user = await login(a.email, a.password);
      toast.success(`Signed in as ${user.name}`);
      if (user.role === "super_admin") navigate("/admin");
      else if (user.role === "temple_admin" || user.role === "partner") navigate("/partner");
      else navigate("/dashboard");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not sign in");
    } finally {
      setLoading(null);
    }
  };

  if (!accounts.length) return null;
  return (
    <div data-testid="demo-accounts-panel" className="mt-10 rounded-2xl border border-[#D4AF37]/40 bg-[#fdf7e4] p-6">
      <div className="label-small text-[#7C191E]">Try Mandala instantly</div>
      <h3 className="mt-1 font-serif text-2xl text-[#1A2436]">Demo accounts · one click</h3>
      <p className="mt-2 text-sm text-[#475569]">
        Sign in as any role to explore the full product. All data is mock; nothing is charged.
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {accounts.map((a) => (
          <button
            key={a.email}
            onClick={() => oneClick(a)}
            disabled={loading === a.email}
            data-testid={`demo-login-${a.email}`}
            className="group flex w-full flex-col gap-2 rounded-xl border border-[#D4AF37]/40 bg-white p-4 text-left transition hover:border-[#7C191E] disabled:opacity-60"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="font-medium text-[#1A2436]">{a.role}</div>
              {loading === a.email ? (
                <Loader2 className="h-4 w-4 shrink-0 animate-spin text-[#7C191E]" />
              ) : (
                <span className="shrink-0 self-start text-[10px] uppercase tracking-[0.18em] text-[#7C191E] group-hover:underline">
                  Sign in →
                </span>
              )}
            </div>
            <div className="truncate text-xs text-[#475569]">{a.email}</div>
            <div className="line-clamp-2 text-xs text-[#475569]">{a.tagline}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
