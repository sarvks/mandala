import { useEffect, useState } from "react";
import { Slider } from "../components/ui/slider";
import { Lock, Unlock } from "lucide-react";

const round = (v) => Math.round(v * 10) / 10;

export default function SplitAllocator({ temples, total, onChange }) {
  const [entries, setEntries] = useState([]);
  const [locked, setLocked] = useState({}); // id -> bool

  useEffect(() => {
    if (!temples.length) return;
    const equal = round(100 / temples.length);
    const base = temples.map((t, i) => ({
      temple_id: t.id,
      name: t.name,
      city: t.city,
      percentage: i === temples.length - 1 ? round(100 - equal * (temples.length - 1)) : equal,
    }));
    setEntries(base);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [temples.map((t) => t.id).join(",")]);

  useEffect(() => {
    if (!entries.length) return;
    const withAmounts = entries.map((e) => ({
      ...e,
      amount: round((Number(total) * e.percentage) / 100),
    }));
    onChange?.({
      splits: withAmounts.map((e) => ({
        temple_id: e.temple_id,
        percentage: e.percentage,
        amount: e.amount,
      })),
      display: withAmounts,
      valid: Math.abs(withAmounts.reduce((s, x) => s + x.percentage, 0) - 100) < 0.5,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entries, total]);

  const onSlide = (idx, newVal) => {
    const id = entries[idx].temple_id;
    if (locked[id]) return;
    const v = Math.min(100, Math.max(0, newVal));
    const oldV = entries[idx].percentage;
    const delta = v - oldV;
    const others = entries
      .map((e, i) => ({ e, i }))
      .filter(({ i }) => i !== idx && !locked[entries[i].temple_id]);
    const remaining = others.reduce((s, { e }) => s + e.percentage, 0);
    if (remaining <= 0 && delta > 0) return;
    const next = entries.map((e, i) => {
      if (i === idx) return { ...e, percentage: round(v) };
      if (locked[e.temple_id]) return e;
      if (remaining === 0) return e;
      const share = e.percentage / remaining;
      return { ...e, percentage: Math.max(0, round(e.percentage - delta * share)) };
    });
    // normalize rounding error
    const sum = next.reduce((s, x) => s + x.percentage, 0);
    const diff = round(100 - sum);
    if (Math.abs(diff) > 0.05) {
      const adjustIdx = next.findIndex((e, i) => i !== idx && !locked[e.temple_id]);
      if (adjustIdx >= 0) next[adjustIdx].percentage = round(next[adjustIdx].percentage + diff);
    }
    setEntries(next);
  };

  const toggleLock = (id) => setLocked((l) => ({ ...l, [id]: !l[id] }));

  const resetEqual = () => {
    const equal = round(100 / entries.length);
    const base = entries.map((e, i) => ({
      ...e,
      percentage: i === entries.length - 1 ? round(100 - equal * (entries.length - 1)) : equal,
    }));
    setLocked({});
    setEntries(base);
  };

  const totalPct = entries.reduce((s, x) => s + x.percentage, 0);

  return (
    <div data-testid="split-allocator" className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="label-small">Split across {entries.length} temples</p>
        <button
          type="button"
          onClick={resetEqual}
          data-testid="split-reset-equal"
          className="text-xs uppercase tracking-[0.22em] text-[#7C191E] hover:underline"
        >
          Reset · Equal
        </button>
      </div>
      <div className="space-y-4">
        {entries.map((e, idx) => {
          const amt = round((Number(total) * e.percentage) / 100);
          return (
            <div
              key={e.temple_id}
              data-testid={`split-row-${e.temple_id}`}
              className="rounded-xl border border-stone-200 bg-white p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium text-[#1A2436]">{e.name}</div>
                  <div className="text-xs text-[#475569]">{e.city}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="font-mono text-sm text-[#1A2436]">
                    {e.percentage.toFixed(1)}%
                  </div>
                  <div className="font-mono text-sm text-[#7C191E]">
                    ₹{amt.toLocaleString("en-IN")}
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleLock(e.temple_id)}
                    data-testid={`split-lock-${e.temple_id}`}
                    className={`inline-flex h-7 w-7 items-center justify-center rounded-full border ${
                      locked[e.temple_id]
                        ? "border-[#7C191E] text-[#7C191E]"
                        : "border-stone-300 text-[#475569]"
                    }`}
                    aria-label="lock"
                  >
                    {locked[e.temple_id] ? (
                      <Lock className="h-3.5 w-3.5" strokeWidth={1.5} />
                    ) : (
                      <Unlock className="h-3.5 w-3.5" strokeWidth={1.5} />
                    )}
                  </button>
                </div>
              </div>
              <div className="mt-3">
                <Slider
                  value={[e.percentage]}
                  min={0}
                  max={100}
                  step={0.5}
                  onValueChange={(v) => onSlide(idx, v[0])}
                  disabled={!!locked[e.temple_id]}
                  data-testid={`split-slider-${e.temple_id}`}
                />
              </div>
            </div>
          );
        })}
      </div>
      <div
        data-testid="split-total-indicator"
        className={`flex items-center justify-between rounded-xl border px-4 py-3 text-sm ${
          Math.abs(totalPct - 100) < 0.5
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : "border-amber-200 bg-amber-50 text-amber-800"
        }`}
      >
        <span className="label-small">Total split</span>
        <span className="font-mono">{totalPct.toFixed(1)}% / 100%</span>
      </div>
    </div>
  );
}
