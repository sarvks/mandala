import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Coins, MapPin } from "lucide-react";

export default function TempleAdmin() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (loading) return;
    if (!user || user.role !== "temple_admin") {
      navigate("/login");
      return;
    }
    api.get("/temple-admin/overview").then((r) => setData(r.data));
  }, [user, loading, navigate]);

  if (!user || !data) return <div className="py-24 text-center text-[#475569]">Loading…</div>;
  const { temple, total_received_inr, donation_count, donations } = data;

  return (
    <div data-testid="temple-admin-page" className="mx-auto max-w-7xl px-6 py-12 md:px-10">
      <header>
        <p className="label-small text-[#7C191E]">Temple desk</p>
        <h1 className="mt-2 font-serif text-5xl text-[#1A2436]">{temple?.name}</h1>
        <div className="mt-2 flex items-center gap-2 text-[#475569]">
          <MapPin className="h-4 w-4" strokeWidth={1.5} />
          {temple?.city}, {temple?.state}
        </div>
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
            ₹{total_received_inr.toLocaleString("en-IN")}
          </div>
        </div>
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <div className="label-small">Total offerings touched</div>
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
          <table data-testid="temple-admin-donations" className="w-full text-sm">
            <thead className="border-b border-stone-200 text-left text-xs uppercase tracking-[0.18em] text-[#475569]">
              <tr>
                <th className="px-5 py-4">Date</th>
                <th className="px-5 py-4">Donor</th>
                <th className="px-5 py-4">Deity</th>
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
                  <td className="px-5 py-4 font-serif text-[#1A2436]">{d.deity_name}</td>
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
