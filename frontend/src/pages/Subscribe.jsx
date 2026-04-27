import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import SplitAllocator from "../components/SplitAllocator";
import { toast } from "sonner";
import { Repeat, Award, CheckCircle2 } from "lucide-react";

export default function Subscribe() {
  const { deityId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [deity, setDeity] = useState(null);
  const [temples, setTemples] = useState([]);
  const [tiers, setTiers] = useState(null);

  const [mode, setMode] = useState("monthly"); // "monthly" | "tier"
  const [amount, setAmount] = useState(501);
  const [tier, setTier] = useState("silver");
  const [split, setSplit] = useState({ splits: [], display: [], valid: false });
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get(`/deities/${deityId}`),
      api.get(`/deities/${deityId}/temples`),
      api.get("/patron-tiers"),
    ]).then(([d, t, pt]) => {
      setDeity(d.data);
      setTemples(t.data);
      setTiers(pt.data);
    });
  }, [deityId]);

  const currentAmount = mode === "tier" && tiers ? tiers[tier].amount : Number(amount);

  const subscribe = async () => {
    if (!user) {
      toast.error("Please login to subscribe");
      return navigate(`/login?next=/subscribe/${deityId}`);
    }
    if (!split.valid) return toast.error("Splits must total 100%");
    setProcessing(true);
    try {
      const { data } = await api.post("/subscriptions", {
        deity_id: deityId,
        kind: mode,
        amount: mode === "monthly" ? Number(amount) : undefined,
        tier: mode === "tier" ? tier : undefined,
        splits: split.splits,
      });
      await new Promise((r) => setTimeout(r, 1200));
      setSuccess(data);
      toast.success("Subscription started · first charge recorded");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start subscription");
    } finally {
      setProcessing(false);
    }
  };

  if (!deity || !tiers) return <div className="py-24 text-center text-[#475569]">Loading…</div>;

  if (success) {
    return (
      <div data-testid="subscribe-success" className="mx-auto max-w-2xl px-6 py-20 md:px-10">
        <div className="rounded-3xl border border-stone-200 bg-white p-10 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#D4AF37]/20 text-[#D4AF37]">
            <CheckCircle2 className="h-8 w-8" strokeWidth={1.5} />
          </div>
          <h2 className="mt-6 font-serif text-4xl text-[#1A2436]">Subscription active</h2>
          <p className="mt-3 text-[#475569]">
            You will offer ₹{success.amount.toLocaleString("en-IN")} every month to{" "}
            {success.deity_name}. Next charge on{" "}
            {new Date(success.next_charge_at).toLocaleDateString("en-IN")}.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link to="/dashboard" data-testid="subscribe-success-dashboard" className="btn-crimson">
              Manage subscriptions
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="subscribe-page" className="mx-auto max-w-6xl px-6 py-16 md:px-10">
      <div className="grid gap-10 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <p className="label-small text-[#7C191E]">Monthly sankalp</p>
          <h1 className="mt-2 font-serif text-5xl text-[#1A2436]">{deity.name}</h1>
          <p className="mt-3 text-[#475569]">
            Recurring offering to {deity.name}. Automatically split across every associated temple, every month.
          </p>
          <div className="mt-8 overflow-hidden rounded-2xl border border-stone-200">
            <img src={deity.image_url} alt={deity.name} className="h-64 w-full object-cover" />
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="rounded-3xl border border-stone-200 bg-white p-8">
            <div className="grid grid-cols-2 gap-2 rounded-full bg-[#F9F6F0] p-1">
              <button
                onClick={() => setMode("monthly")}
                data-testid="sub-mode-monthly"
                className={`rounded-full py-2 text-sm font-medium transition ${
                  mode === "monthly" ? "bg-white text-[#7C191E] shadow-sm" : "text-[#475569]"
                }`}
              >
                <Repeat className="mr-2 inline h-4 w-4" strokeWidth={1.5} /> Monthly amount
              </button>
              <button
                onClick={() => setMode("tier")}
                data-testid="sub-mode-tier"
                className={`rounded-full py-2 text-sm font-medium transition ${
                  mode === "tier" ? "bg-white text-[#7C191E] shadow-sm" : "text-[#475569]"
                }`}
              >
                <Award className="mr-2 inline h-4 w-4" strokeWidth={1.5} /> Patron tier
              </button>
            </div>

            {mode === "monthly" ? (
              <div className="mt-8">
                <div className="label-small text-[#7C191E]">Choose a monthly amount (min ₹51)</div>
                <div className="mt-4 flex items-center gap-2 rounded-xl border border-stone-200 bg-[#F9F6F0] px-4 py-3">
                  <span className="font-serif text-xl text-[#475569]">₹</span>
                  <input
                    type="number"
                    min={51}
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    data-testid="sub-amount-input"
                    className="w-full bg-transparent text-2xl font-medium outline-none"
                  />
                  <span className="label-small">/ month</span>
                </div>
              </div>
            ) : (
              <div className="mt-8 grid gap-4 sm:grid-cols-3">
                {Object.entries(tiers).map(([k, v]) => (
                  <button
                    key={k}
                    onClick={() => setTier(k)}
                    data-testid={`sub-tier-${k}`}
                    className={`rounded-2xl border p-5 text-left transition ${
                      tier === k
                        ? "border-[#7C191E] bg-[#F9F6F0]"
                        : "border-stone-200 bg-white hover:border-[#D4AF37]"
                    }`}
                  >
                    <div className="label-small text-[#D4AF37]">{v.name}</div>
                    <div className="mt-2 font-serif text-3xl text-[#1A2436]">₹{v.amount.toLocaleString("en-IN")}</div>
                    <ul className="mt-4 space-y-1 text-xs text-[#475569]">
                      {v.perks.map((p) => <li key={p}>· {p}</li>)}
                    </ul>
                  </button>
                ))}
              </div>
            )}

            <div className="mt-10">
              <SplitAllocator temples={temples} total={currentAmount} onChange={setSplit} />
            </div>

            <div className="mt-10 flex items-center justify-between gap-4 border-t border-stone-200 pt-6">
              <div>
                <div className="label-small text-[#7C191E]">Every month</div>
                <div className="font-serif text-3xl text-[#1A2436]">
                  ₹{currentAmount.toLocaleString("en-IN")}
                </div>
              </div>
              <button
                onClick={subscribe}
                disabled={processing || !split.valid}
                data-testid="sub-start-btn"
                className="btn-crimson inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {processing ? "Starting…" : "Start monthly sankalp"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
