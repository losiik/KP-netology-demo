import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from "react-router";
import { AuthProvider, RequireAuth } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import HistoryPage from "./pages/HistoryPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import OfferPage from "./pages/OfferPage.jsx";

// Отдельный key для каждого документа и для каждого перехода на «Новое предложение»,
// чтобы состояние формы не переезжало между документами.
function OfferRoute() {
  const { id } = useParams();
  const location = useLocation();
  return <OfferPage key={id ? `doc-${id}` : `new-${location.key}`} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route path="/new" element={<OfferRoute />} />
            <Route path="/documents/:id" element={<OfferRoute />} />
            <Route path="/history" element={<HistoryPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/new" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
