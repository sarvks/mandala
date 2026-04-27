import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs";
import { toast } from "sonner";
import { Calendar, HeartHandshake, Repeat, XCircle, MapPin, Heart, Bell } from "lucide-react";
import FavouriteButton from "../components/FavouriteButton";

export default function Dashboard() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const [donations, setDonations] = useState([]);
  const [subs, setSubs] = useState([]);
  const [favTemples, setFavTemples] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const loadFavouritesAndNotifs = async () => {
    const [f, n] = await Promise.all([
      api.get("/favourites/me"),
      api.get("/notifications/me"),
    ]);
    setFavTemples(f.data.temples || []);
    setNotifications(n.data.notifications || []);
  };

  useEffect(() => {
    if (loading) return;
    if (!user) {
      navigate("/login");
      return;
    }
    api.get("/donations/me").then((r) => setDonations(r.data));
    api.get("/subscriptions/me").then((r) => setSubs(r.data));
    loadFavouritesAndNotifs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, loading, navigate]);

  const cancel = async (id) => {
    try {
      await api.post(`/subscriptions/${id}/cancel`);
      setSubs((s) => s.map((x) => (x.id === id ? { ...x, status: "cancelled" } : x)));
      toast.success("Subscription cancelled");
    } catch {
      toast.error("Could not cancel");
    }
  };

  const totalGiven = donations
    .filter((d) => d.status === "succeeded")
    .reduce((s, d) => s + d.total_amount, 0);
  const activeSubs = subs.filter((s) => s.status === "active");

  if (!user) return null;

  return (
    <div data-testid="dashboard-page" className="mx-auto max-w-7xl px-6 py-16 md:px-10">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="label-small text-[#7C191E]">Namaste</p>
          <h1 className="mt-2 font-serif text-5xl text-[#1A2436]">{user.name}</h1>
          <p className="mt-2 text-[#475569]">Your sankalps, patron subscriptions and favourite temples</p>
        </div>
        <Link to="/deities" data-testid="dashboard-cta-donate" className="btn-crimson">Make an offering</Link>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-4">
        <StatCard icon={HeartHandshake} label="Total offered" value={`₹${totalGiven.toLocaleString("en-IN")}`} />
        <StatCard icon={Calendar} label="Donations" value={donations.length} />
        <StatCard icon={Repeat} label="Active subs" value={activeSubs.length} />
        <StatCard icon={Heart} label="My temples" value={favTemples.length} />
      </div>

      {notifications.length > 0 && (
        <div
          data-testid="dashboard-notifications"
          className="mt-10 rounded-2xl border border-[#D4AF37]/40 bg-[#fdf7e4] p-6"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#D4AF37]/30 text-[#7C191E]">
              <Bell className="h-5 w-5" strokeWidth={1.5} />
            </div>
            <div>
              <div className="label-small text-[#7C191E]">Upcoming festivals at your temples</div>
              <div className="font-serif text-2xl text-[#1A2436]">{notifications.length} sacred days ahead</div>
            </div>
          </div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {notifications.slice(0, 6).map((n, i) => (
              <div
                key={`${n.festival}-${i}`}
                data-testid={`notif-${i}`}
                className="rounded-xl border border-[#D4AF37]/30 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="font-serif text-lg text-[#1A2436]">{n.festival}</div>
                  <span className="rounded-full bg-[#7C191E] px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.14em] text-white">
                    {n.days_until === 0 ? "Today" : `${n.days_until}d`}
                  </span>
                </div>
                <div className="mt-1 text-xs text-[#475569]">
                  {new Date(n.date).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}
                </div>
                <div className="mt-3 text-sm text-[#1A2436]">
                  {n.temples?.length === 1
                    ? n.temples[0].temple_name
                    : `${n.temples?.length || 0} of your temples`}
                </div>
                <div className="mt-1 text-xs leading-relaxed text-[#475569] line-clamp-2">
                  {n.temples?.map((t) => t.temple_name).join(" · ")}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <Tabs defaultValue="donations" className="mt-12">
        <TabsList data-testid="dashboard-tabs" className="bg-[#F9F6F0]">
          <TabsTrigger value="donations" data-testid="tab-donations">Donations</TabsTrigger>
          <TabsTrigger value="subs" data-testid="tab-subs">Subscriptions</TabsTrigger>
          <TabsTrigger value="temples" data-testid="tab-temples">My Temples</TabsTrigger>
        </TabsList>

        <TabsContent value="donations" className="mt-6">
          <div className="rounded-2xl border border-stone-200 bg-white">
            {donations.length === 0 ? (
              <div className="p-10 text-center text-[#475569]">
                No offerings yet.{" "}
                <Link to="/deities" className="text-[#7C191E] underline">Make your first sankalp</Link>
              </div>
            ) : (
              <table data-testid="donations-table" className="w-full text-sm">
                <thead className="border-b border-stone-200 text-left text-xs uppercase tracking-[0.18em] text-[#475569]">
                  <tr>
                    <th className="px-5 py-4">Date</th>
                    <th className="px-5 py-4">Deity</th>
                    <th className="px-5 py-4">Amount</th>
                    <th className="px-5 py-4">Temples</th>
                    <th className="px-5 py-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {donations.map((d) => (
                    <tr key={d.id} className="border-b border-stone-100 last:border-0">
                      <td className="px-5 py-4 text-[#475569]">{new Date(d.created_at).toLocaleDateString("en-IN")}</td>
                      <td className="px-5 py-4 font-serif text-[#1A2436]">{d.deity_name}</td>
                      <td className="px-5 py-4 font-mono text-[#1A2436]">₹{d.total_amount.toLocaleString("en-IN")}</td>
                      <td className="px-5 py-4 text-[#475569]">{d.splits.length}</td>
                      <td className="px-5 py-4">
                        <span className={`rounded-full px-3 py-1 text-xs ${
                          d.status === "succeeded" ? "bg-emerald-100 text-emerald-800" :
                          d.status === "pending" ? "bg-amber-100 text-amber-800" : "bg-stone-200 text-stone-700"
                        }`}>{d.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </TabsContent>

        <TabsContent value="subs" className="mt-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {subs.length === 0 ? (
              <div className="col-span-full rounded-2xl border border-stone-200 bg-white p-10 text-center text-[#475569]">
                No active subscriptions yet.{" "}
                <Link to="/patron" className="text-[#7C191E] underline">Become a patron</Link>
              </div>
            ) : (
              subs.map((s) => (
                <div key={s.id} data-testid={`sub-card-${s.id}`} className="rounded-2xl border border-stone-200 bg-white p-6">
                  <div className="label-small text-[#D4AF37]">
                    {s.kind === "tier" ? `${s.tier?.toUpperCase()} patron` : "Monthly sankalp"}
                  </div>
                  <div className="mt-2 font-serif text-2xl text-[#1A2436]">{s.deity_name}</div>
                  <div className="mt-1 font-mono text-sm text-[#7C191E]">
                    ₹{s.amount.toLocaleString("en-IN")} / month
                  </div>
                  <div className="mt-4 text-xs text-[#475569]">
                    Next charge: {new Date(s.next_charge_at).toLocaleDateString("en-IN")}
                  </div>
                  <div className="mt-4">
                    <span className={`rounded-full px-3 py-1 text-xs ${
                      s.status === "active" ? "bg-emerald-100 text-emerald-800" : "bg-stone-200 text-stone-700"
                    }`}>{s.status}</span>
                  </div>
                  {s.status === "active" && (
                    <button
                      onClick={() => cancel(s.id)}
                      data-testid={`sub-cancel-${s.id}`}
                      className="mt-5 inline-flex items-center gap-2 text-sm text-[#7C191E] hover:underline"
                    >
                      <XCircle className="h-4 w-4" strokeWidth={1.5} /> Cancel
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </TabsContent>

        <TabsContent value="temples" className="mt-6">
          {favTemples.length === 0 ? (
            <div className="rounded-2xl border border-stone-200 bg-white p-10 text-center text-[#475569]">
              No favourite temples yet.{" "}
              <Link to="/temples" className="text-[#7C191E] underline">Browse the sacred atlas</Link>{" "}
              and tap the heart on temples you hold dear.
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {favTemples.map((t) => (
                <article
                  key={t.id}
                  data-testid={`fav-temple-${t.id}`}
                  className="card-surface overflow-hidden"
                >
                  <div className="relative h-40 overflow-hidden">
                    <img src={t.image_url} alt={t.name} className="h-full w-full object-cover" />
                    <div className="absolute right-3 top-3">
                      <FavouriteButton templeId={t.id} size="sm" />
                    </div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-serif text-lg text-[#1A2436]">{t.name}</h3>
                    <div className="mt-1 flex items-center gap-2 text-xs text-[#475569]">
                      <MapPin className="h-3.5 w-3.5" strokeWidth={1.5} />
                      {t.city}, {t.state}
                    </div>
                    <p className="mt-3 line-clamp-2 text-sm text-[#475569]">{t.description}</p>
                    <div className="mt-4 flex items-center gap-2">
                      {t.deity_ids?.[0] && (
                        <Link
                          to={`/donate/${t.deity_ids[0]}`}
                          data-testid={`fav-temple-donate-${t.id}`}
                          className="text-xs uppercase tracking-[0.18em] text-[#7C191E] hover:underline"
                        >
                          Offer now →
                        </Link>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#7C191E]/10 text-[#7C191E]">
          <Icon className="h-5 w-5" strokeWidth={1.5} />
        </div>
        <div className="label-small">{label}</div>
      </div>
      <div className="mt-4 font-serif text-3xl text-[#1A2436]">{value}</div>
    </div>
  );
}
