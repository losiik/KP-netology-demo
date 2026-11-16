import { useEffect, useState } from "react";
import { Link } from "react-router";
import { api } from "../api.js";
import { formatDate, formatRub } from "../money.js";

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
        <h2>История предложений</h2>
        <Link className="btn btn-primary" to="/new">
          + Новое предложение
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {!documents && !error && <p className="hint">Загрузка…</p>}

      {documents?.length === 0 && (
        <p className="empty">Пока нет сохранённых предложений. Создайте черновик и нажмите «Сохранить».</p>
      )}

      {documents?.length > 0 && (
        <ul className="history-list">
          <li className="history-row history-header" aria-hidden="true">
            <span>Клиент</span>
            <span>Сумма</span>
            <span>Обновлено</span>
          </li>
          {documents.map((doc) => (
            <li key={doc.id}>
              <Link className="history-row" to={`/documents/${doc.id}`}>
                <span className="history-client">{doc.client}</span>
                <span className="history-total">{formatRub(doc.total)}</span>
                <span className="history-date">{formatDate(doc.updated_at)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
