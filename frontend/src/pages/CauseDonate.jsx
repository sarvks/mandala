import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import SplitAllocator from "../components/SplitAllocator";
import { toast } from "sonner";
import { CheckCircle2, ShieldCheck, Lock } from "lucide-react";

const PRESETS = [101, 251, 501, 1101, 2501, 5100];

export default function CauseDonate() {
  const { causeId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [cause, setCause] = useState(null);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [amount, setAmount] = useState(501);
  const [note, setNote] = useState("");
  const [split, setSplit] = useState({ splits: [], display: [], valid: false });
  const [processing, setProcessing] = useState(false);
  const [success, setSuccess] = useState(null);

  // Adapt beneficiaries to the SplitAllocator's temple shape (id + name + city)
  const items = beneficiaries.map((b) => ({ id: b.id, name: b.name, city: b.city }));

  useEffect(() => {
    Promise.all([api.get(`/causes/${causeId}`), api.get(`/causes/${causeId}/beneficiaries`)]).then(
      ([c, b]) => {
        setCause(c.data);
        setBeneficiaries(b.data);
      }
    );
  }, [causeId]);

  const pay = async () => {
    if (!user) {
      toast.error("Please login to donate");
      navigate(`/login?next=/cause-donate/${causeId}`);
      return;
    }
    if (amount < 11) return toast.error("Minimum donation is ₹11");
    if (!split.valid) return toast.error("Splits must total 100%");
    setProcessing(true);
    try {
      const { data: d } = await api.post("/cause-donations", {
        cause_id: causeId,
        total_amount: Number(amount),
        splits: split.splits,
        donor_note: note || null,
      });
      await new Promise((r) => setTimeout(r, 1500));
      const { data: confirmed } = await api.post(`/cause-donations/${d.id}/confirm`);
      setSuccess(confirmed);
      toast.success("Offering received — reaching every partner");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Something went wrong");
    } finally {
      setProcessing(false);
    }
  };

  if (!cause) return <div className="py-24 text-center text-[#475569]">Loading…</div>;

  if (success) {
    return (
      <div data-testid="cause-donate-success" className="mx-auto max-w-2xl px-6 py-20 md:px-10">
        <div className="rounded-3xl border border-stone-200 bg-white p-10 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#7C191E]/10 text-[#7C191E]">
            <CheckCircle2 className="h-8 w-8" strokeWidth={1.5} />
          </div>
          <h2 className="mt-6 font-serif text-4xl text-[#1A2436]">Offering received</h2>
          <p className="mt-3 text-[#475569]">
            ₹{success.total_amount.toLocaleString("en-IN")} has been split across{" "}
            {success.splits.length} partners working on {success.cause_name}.
          </p>
          <div className="mt-8 space-y-2 rounded-xl border border-stone-200 bg-[#F9F6F0] p-5 text-left">
            <div className="label-small text-[#7C191E]">Transaction</div>
            <div className="font-mono text-xs text-[#475569]">{success.payment_ref}</div>
            <div className="mt-4 label-small text-[#7C191E]">Splits</div>
            {success.splits.map((s) => {
              const t = beneficiaries.find((x) => x.id === s.temple_id);
              return (
                <div key={s.temple_id} className="flex justify-between text-sm text-[#1A2436]">
                  <span>{t?.name || s.temple_id}</span>
                  <span className="font-mono">₹{s.amount.toLocaleString("en-IN")} · {s.percentage}%</span>
                </div>
              );
            })}
          </div>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link to="/dashboard" className="btn-crimson">View my donations</Link>
            <Link to="/causes" className="btn-ghost-gold">Explore other causes</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="cause-donate-page" className="mx-auto max-w-6xl px-6 py-16 md:px-10">
      <div className="grid gap-10 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <p className="label-small text-[#7C191E]">Donate to</p>
          <h1 className="mt-2 font-serif text-4xl text-[#1A2436]">{cause.name}</h1>
          <p className="mt-3 text-[#475569]">{cause.short_desc}</p>
          <div className="mt-8 overflow-hidden rounded-2xl border border-stone-200">
            <img src={cause.image_url} alt={cause.name} className="h-64 w-full object-cover" />
          </div>
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-stone-200 bg-white p-4 text-sm text-[#475569]">
            <ShieldCheck className="h-5 w-5 text-[#7C191E]" strokeWidth={1.5} />
            <span>Razorpay test mode · payments are simulated for this preview.</span>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="rounded-3xl border border-stone-200 bg-white p-8">
            <div className="label-small text-[#7C191E]">Step 1 · Amount</div>
            <div className="mt-4 flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button key={p} onClick={() => setAmount(p)} data-testid={`cause-preset-${p}`}
                  className={`rounded-full border px-4 py-2 text-sm transition ${
                    amount === p ? "border-[#7C191E] bg-[#7C191E] text-white" : "border-stone-300 hover:border-[#7C191E]"
                  }`}>
                  ₹{p.toLocaleString("en-IN")}
                </button>
              ))}
            </div>
            <div className="mt-5 flex items-center gap-2 rounded-xl border border-stone-200 bg-[#F9F6F0] px-4 py-3">
              <span className="font-serif text-xl text-[#475569]">₹</span>
              <input type="number" min={11} value={amount} onChange={(e) => setAmount(Number(e.target.value))}
                data-testid="cause-donate-amount-input"
                className="w-full bg-transparent text-2xl font-medium outline-none" />
              <span className="label-small">INR</span>
            </div>

            <div className="mt-10 label-small text-[#7C191E]">
              Step 2 · Split across {beneficiaries.length} partners
            </div>
            <div className="mt-4">
              <SplitAllocator temples={items} total={amount} onChange={setSplit} />
            </div>

            <div className="mt-10">
              <div className="label-small text-[#7C191E]">Step 3 · Note (optional)</div>
              <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3}
                data-testid="cause-donate-note-input"
                placeholder="Add a note to the partners"
                className="mt-4 w-full rounded-xl border border-stone-200 bg-white p-4 text-sm outline-none transition focus:border-[#7C191E]" />
            </div>

            <div className="mt-10 flex items-center justify-between gap-4 border-t border-stone-200 pt-6">
              <div>
                <div className="label-small text-[#7C191E]">Total</div>
                <div className="font-serif text-3xl text-[#1A2436]">₹{Number(amount).toLocaleString("en-IN")}</div>
              </div>
              <button onClick={pay} disabled={processing || !split.valid} data-testid="cause-donate-pay-btn"
                className="btn-crimson inline-flex items-center gap-2 disabled:cursor-not-allowed disabled:opacity-50">
                <Lock className="h-4 w-4" strokeWidth={1.5} />
                {processing ? "Processing…" : "Pay securely"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
