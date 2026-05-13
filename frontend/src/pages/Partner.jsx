import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Coins, MapPin, Globe } from "lucide-react";

export default function Partner() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      navigate("/login");
      return;
    }
    if (user.role !== "temple_admin" && user.role !== "partner") {
      navigate("/dashboard");
      return;
    }
    api
      .get("/partner/overview")
      .then((r) => setData(r.data))
      .catch((e) => setErr(e?.response?.data?.detail || "Could not load partner data"));
  }, [user, loading, navigate]);

  if (!user) return null;
  if (err) return <div className="py-24 text-center text-[#7C191E]">{err}</div>;
  if (!data) return <div className="py-24 text-center text-[#475569]">Loading…</div>;

  const { kind, entity, total_received_inr, donation_count, donations, role } = data;
  const kindLabel = kind === "temple" ? "Temple Desk" : "Partner Desk";
  const contextHeader = kind === "temple" ? "Deity" : "Cause";

  return (
    <div data-testid="partner-page" className="mx-auto max-w-7xl px-6 py-12 md:px-10">
      <header className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="label-small text-[#7C191E]">{kindLabel}</p>
          <h1 className="mt-2 font-serif text-5xl text-[#1A2436]">{entity?.name}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-4 text-[#475569]">
            <span className="inline-flex items-center gap-2">
              <MapPin className="h-4 w-4" strokeWidth={1.5} />
              {entity?.city}, {entity?.state}
            </span>
            {entity?.website && (
              <a href={`https://${entity.website.replace(/^https?:\/\//, "")}`} target="_blank" rel="noreferrer"
                className="inline-flex items-center gap-2 text-[#7C191E] hover:underline">
                <Globe className="h-4 w-4" strokeWidth={1.5} /> {entity.website}
              </a>
            )}
          </div>
        </div>
        <span className="rounded-full bg-[#7C191E]/10 px-4 py-2 text-xs uppercase tracking-[0.18em] text-[#7C191E]">
          {role.replace("_", " ")}
        </span>
      </header>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7C191E]/10 text-[#7C191E]">
              <Coins className="h-5 w-5" strokeWidth={1.5} />
            </div>
            <div className="label-small">Total share received</div>
          </div>
          <div className="mt-4 font-serif text-4xl text-[#1A2436]">
            ₹{(total_received_inr || 0).toLocaleString("en-IN")}
          </div>
        </div>
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <div className="label-small">Offerings touched</div>
          <div className="mt-4 font-serif text-4xl text-[#1A2436]">{donation_count}</div>
        </div>
      </div>

      <div className="mt-10 rounded-2xl border border-stone-200 bg-white">
        <div className="border-b border-stone-200 p-5">
          <div className="label-small text-[#7C191E]">Incoming donations (your share)</div>
        </div>
        {donations.length === 0 ? (
          <div className="p-10 text-center text-[#475569]">No donations received yet.</div>
        ) : (
          <table data-testid="partner-donations-table" className="w-full text-sm">
            <thead className="border-b border-stone-200 text-left text-xs uppercase tracking-[0.18em] text-[#475569]">
              <tr>
                <th className="px-5 py-4">Date</th>
                <th className="px-5 py-4">Donor</th>
                <th className="px-5 py-4">{contextHeader}</th>
                <th className="px-5 py-4">Share</th>
                <th className="px-5 py-4">% of total</th>
                <th className="px-5 py-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {donations.map((d) => (
                <tr key={d.donation_id} className="border-b border-stone-100 last:border-0">
                  <td className="px-5 py-4 text-[#475569]">{new Date(d.created_at).toLocaleDateString("en-IN")}</td>
                  <td className="px-5 py-4 text-[#1A2436]">{d.donor_name}</td>
                  <td className="px-5 py-4 font-serif text-[#1A2436]">{d.context_name}</td>
                  <td className="px-5 py-4 font-mono text-[#7C191E]">₹{d.share_amount.toLocaleString("en-IN")}</td>
                  <td className="px-5 py-4 text-[#475569]">{d.share_percentage}%</td>
                  <td className="px-5 py-4">
                    <span className={`rounded-full px-3 py-1 text-xs ${
                      d.status === "succeeded" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
                    }`}>{d.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
