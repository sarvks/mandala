import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { Sparkles, Building2, Users, Coins } from "lucide-react";

const COLORS = ["#7C191E", "#D4AF37", "#1A2436", "#8B5E3C", "#0E7490", "#B45309"];

export default function AdminDashboard() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (loading) return;
    if (!user || user.role !== "super_admin") {
      navigate("/login");
      return;
    }
    api.get("/admin/analytics").then((r) => setData(r.data));
  }, [user, loading, navigate]);

  if (!user || !data) return <div className="py-24 text-center text-[#475569]">Loading…</div>;

  return (
    <div data-testid="admin-dashboard-page" className="mx-auto max-w-7xl px-6 py-12 md:px-10">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label-small text-[#7C191E]">Control Room</p>
          <h1 className="mt-2 font-serif text-5xl text-[#1A2436]">Mandala admin</h1>
        </div>
      </header>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Coins} label="Total donated" value={`₹${(data.total_donations_inr || 0).toLocaleString("en-IN")}`} sub={`${data.total_donation_count} offerings`} />
        <StatCard icon={Sparkles} label="MRR" value={`₹${(data.mrr_inr || 0).toLocaleString("en-IN")}`} sub={`${data.active_subscriptions} active subs`} />
        <StatCard icon={Building2} label="Temples" value={data.counts.temples} sub={`${data.counts.deities} deities`} />
        <StatCard icon={Users} label="Donors" value={data.counts.donors} sub="registered devotees" />
      </div>

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <div className="mb-2 label-small text-[#7C191E]">Top deities by giving</div>
          {data.top_deities.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data.top_deities} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis type="number" stroke="#94A3B8" fontSize={12} />
                <YAxis dataKey="name" type="category" stroke="#1A2436" fontSize={12} width={150} />
                <Tooltip cursor={{ fill: "#F9F6F0" }} />
                <Bar dataKey="total" fill="#7C191E" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-[#475569]">No donations yet</div>
          )}
        </div>

        <div className="rounded-2xl border border-stone-200 bg-white p-6">
          <div className="mb-2 label-small text-[#7C191E]">Top temples by share received</div>
          {data.top_temples.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={data.top_temples} dataKey="total" nameKey="name" innerRadius={60} outerRadius={110} paddingAngle={3}>
                  {data.top_temples.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend layout="vertical" align="right" verticalAlign="middle" wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-64 items-center justify-center text-sm text-[#475569]">No donations yet</div>
          )}
        </div>
      </div>

      <div className="mt-10 rounded-2xl border border-stone-200 bg-white">
        <div className="border-b border-stone-200 p-5">
          <div className="label-small text-[#7C191E]">Recent donations</div>
        </div>
        {data.recent_donations.length === 0 ? (
          <div className="p-10 text-center text-[#475569]">No offerings yet.</div>
        ) : (
          <table data-testid="admin-recent-donations" className="w-full text-sm">
            <thead className="border-b border-stone-200 text-left text-xs uppercase tracking-[0.18em] text-[#475569]">
              <tr>
                <th className="px-5 py-4">Date</th>
                <th className="px-5 py-4">Donor</th>
                <th className="px-5 py-4">Deity</th>
                <th className="px-5 py-4">Amount</th>
                <th className="px-5 py-4">Temples</th>
                <th className="px-5 py-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_donations.map((d) => (
                <tr key={d.id} className="border-b border-stone-100 last:border-0">
                  <td className="px-5 py-4 text-[#475569]">{new Date(d.created_at).toLocaleDateString("en-IN")}</td>
                  <td className="px-5 py-4 text-[#1A2436]">{d.donor_name}</td>
                  <td className="px-5 py-4 font-serif text-[#1A2436]">{d.deity_name}</td>
                  <td className="px-5 py-4 font-mono text-[#1A2436]">₹{d.total_amount.toLocaleString("en-IN")}</td>
                  <td className="px-5 py-4 text-[#475569]">{d.splits.length}</td>
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

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7C191E]/10 text-[#7C191E]">
          <Icon className="h-5 w-5" strokeWidth={1.5} />
        </div>
        <div className="label-small">{label}</div>
      </div>
      <div className="mt-4 font-serif text-3xl text-[#1A2436]">{value}</div>
      {sub && <div className="mt-1 text-xs text-[#475569]">{sub}</div>}
    </div>
  );
}
