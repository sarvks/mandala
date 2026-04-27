import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = params.get("next") || "/dashboard";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) return toast.error("Password must be at least 6 characters");
    setLoading(true);
    try {
      await signup(name, email, password);
      toast.success("Account created · welcome to Mandala");
      navigate(next);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="signup-page" className="mx-auto max-w-md px-6 py-20 md:px-10">
      <h1 className="font-serif text-4xl text-[#1A2436]">Create your account</h1>
      <p className="mt-2 text-[#475569]">So you can track every offering you make.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <label className="block">
          <span className="label-small text-[#7C191E]">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            data-testid="signup-name-input"
            className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-3 outline-none focus:border-[#7C191E]"
          />
        </label>
        <label className="block">
          <span className="label-small text-[#7C191E]">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            data-testid="signup-email-input"
            className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-3 outline-none focus:border-[#7C191E]"
          />
        </label>
        <label className="block">
          <span className="label-small text-[#7C191E]">Password</span>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="signup-password-input"
            className="mt-2 w-full rounded-xl border border-stone-200 bg-white px-4 py-3 outline-none focus:border-[#7C191E]"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          data-testid="signup-submit-btn"
          className="btn-crimson w-full disabled:opacity-60"
        >
          {loading ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="mt-6 text-sm text-[#475569]">
        Already have one?{" "}
        <Link to="/login" className="text-[#7C191E] underline">Login</Link>
      </p>
    </div>
  );
}
