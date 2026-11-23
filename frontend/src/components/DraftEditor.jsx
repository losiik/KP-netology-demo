import { formatDate } from "../money.js";
import SourceBadge from "./SourceBadge.jsx";

// Редактор черновика: текст правится вручную, «Сохранить» пишет текущую редакцию.
export default function DraftEditor({
  client,
  text,
  source,
  onChange,
  onSave,
  onCopy,
  busy,
  dirty,
  savedAt,
  message,
}) {
  if (text === null) {
    return (
      <section className="card editor editor-empty">
        <h2>Черновик</h2>
        <p>
          Заполните форму и нажмите <b>«Создать черновик»</b>. Текст появится здесь,
          его можно будет поправить, сохранить и скопировать.
        </p>
      </section>
    );
  }

  return (
    <section className="card editor">
      <div className="card-head">
        <h2>Черновик{client ? ` · ${client}` : ""}</h2>
        <SourceBadge source={source} />
      </div>

      {message && (
        <div className="alert alert-error" role="alert">
          {message}
        </div>
      )}

      <div className="editor-label-row">
        <label className="label" htmlFor="draft-text">
          Текст предложения
        </label>
        <span className={`save-status ${dirty ? "is-dirty" : "is-saved"}`}>
          {dirty ? "Есть несохранённые изменения" : `Сохранено ${savedAt ? formatDate(savedAt) : ""}`}
        </span>
      </div>
      <textarea
        id="draft-text"
        className="draft-text"
        value={text}
        onChange={(event) => onChange(event.target.value)}
        spellCheck
      />

      <div className="editor-actions">
        <button type="button" className="btn btn-primary" onClick={onSave} disabled={busy || !text.trim()}>
          {busy ? "Сохраняем…" : "Сохранить"}
        </button>
        <button type="button" className="btn btn-secondary" onClick={onCopy} disabled={!text}>
          Скопировать
        </button>
        <span className="editor-hint">Проверьте текст перед отправкой</span>
      </div>
    </section>
  );
}
