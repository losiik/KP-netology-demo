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
        <div className="brand">Предложения</div>
        <nav className="nav">
          <NavLink to="/new">Новое предложение</NavLink>
          <NavLink to="/history">Мои предложения</NavLink>
        </nav>
        <div className="user">
          <span className="stage-chip" title="Черновик собирается по шаблону, ИИ подключим на лекции">
            Учебный макет
          </span>
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
