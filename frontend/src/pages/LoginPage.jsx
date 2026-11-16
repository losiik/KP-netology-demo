import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";
import { useAuth } from "../auth.jsx";

const DEMO_ACCOUNTS = [
  { login: "anna", password: "anna123", name: "Анна Смирнова" },
  { login: "boris", password: "boris123", name: "Борис Петров" },
];

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const target = location.state?.from || "/new";

  const [form, setForm] = useState({ login: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to={target} replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(form.login, form.password);
      navigate(target, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <form className="card login-card" onSubmit={handleSubmit}>
        <div className="brand brand-large">
          <span className="brand-mark">КП</span>
          <span>Коммерческие предложения</span>
        </div>
        <h1>Вход</h1>

        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        <div className="field">
          <label className="label" htmlFor="login">Логин</label>
          <input
            id="login"
            autoComplete="username"
            value={form.login}
            onChange={(e) => setForm({ ...form, login: e.target.value })}
          />
        </div>
        <div className="field">
          <label className="label" htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <button type="submit" className="btn btn-primary btn-wide" disabled={busy}>
          {busy ? "Входим…" : "Войти"}
        </button>

        <div className="demo-accounts">
          <p className="hint">Учебные аккаунты — нажмите, чтобы подставить:</p>
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.login}
              type="button"
              className="btn btn-ghost demo-account"
              onClick={() => setForm({ login: account.login, password: account.password })}
            >
              <b>{account.name}</b>
              <span>
                {account.login} / {account.password}
              </span>
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
