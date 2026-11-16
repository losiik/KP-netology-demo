import { NavLink, Outlet, useNavigate } from "react-router";
import { useAuth } from "../auth.jsx";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">КП</span>
          <span>Коммерческие предложения</span>
        </div>
        <nav className="nav">
          <NavLink to="/new">Новое предложение</NavLink>
          <NavLink to="/history">История</NavLink>
        </nav>
        <div className="user">
          <span>{user.name}</span>
          <button type="button" className="btn btn-ghost btn-small" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
