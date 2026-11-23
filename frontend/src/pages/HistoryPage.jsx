import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api } from "../api.js";
import SourceBadge from "../components/SourceBadge.jsx";
import { formatRelativeDate } from "../money.js";

// «Мои предложения» — документы текущего пользователя. Чужие сервер не отдаёт.
export default function HistoryPage() {
  const [documents, setDocuments] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/documents")
      .then((data) => setDocuments(data.documents))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <section className="card history">
      <div className="card-head">
        <h2>Мои предложения</h2>
        <Link className="btn btn-primary" to="/new">
          Новое предложение
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {!documents && !error && <p className="hint">Загрузка…</p>}

      {documents?.length === 0 && (
        <p className="empty">Пока нет сохранённых предложений. Создайте черновик и нажмите «Сохранить».</p>
      )}

      {documents?.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>Клиент</th>
              <th>Как создан</th>
              <th>Обновлено</th>
              <th>Действие</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr key={doc.id}>
                <td className="history-client">{doc.client}</td>
                <td>
                  <SourceBadge source={doc.source} />
                </td>
                <td className="history-date">{formatRelativeDate(doc.updated_at)}</td>
                <td>
                  <Link className="history-open" to={`/documents/${doc.id}`}>
                    Открыть
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="hint history-note">Сохранённые документы доступны после повторного входа</p>
    </section>
  );
}
