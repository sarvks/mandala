import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.name}`);
      if (user.role === "super_admin") navigate("/admin");
      else if (user.role === "temple_admin") navigate("/temple-admin");
      else navigate(next);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="login-page" className="mx-auto max-w-md px-6 py-20 md:px-10">
      <h1 className="font-serif text-4xl text-[#1A2436]">Welcome back</h1>
      <p className="mt-2 text-[#475569]">Login to manage your sankalps and subscriptions.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block">
          <span className="label-small text-[#7C191E]">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            data-testid="login-email-input"
            className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-3 outline-none transition focus:border-[#7C191E]"
          />
        </label>
        <label className="block">
          <span className="label-small text-[#7C191E]">Password</span>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="login-password-input"
            className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-3 outline-none transition focus:border-[#7C191E]"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          data-testid="login-submit-btn"
          className="btn-crimson w-full disabled:opacity-60"
        >
          {loading ? "Entering…" : "Enter"}
        </button>
      </form>
      <p className="mt-6 text-sm text-[#475569]">
        Don&apos;t have an account?{" "}
        <Link to="/signup" className="text-[#7C191E] underline">Create one</Link>
      </p>
      <div className="mt-8 rounded-xl border border-stone-200 bg-[#F9F6F0] p-4 text-xs text-[#475569]">
        <div className="label-small mb-2 text-[#7C191E]">Demo accounts</div>
        <div>Donor · devotee@mandala.in / devotee123</div>
        <div>Admin · admin@mandala.in / mandala123</div>
      </div>
    </div>
  );
}
