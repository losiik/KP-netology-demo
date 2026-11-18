import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import { api } from "../api.js";
import DraftEditor from "../components/DraftEditor.jsx";
import OfferForm from "../components/OfferForm.jsx";
import Toast, { useToast } from "../components/Toast.jsx";
import { emptyFields, SAMPLE_OFFER, toApiFields, toFormFields } from "../offerFields.js";

// Страница предложения: /new — новый документ, /documents/:id — сохранённый.
export default function OfferPage() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  // Сразу после первого сохранения документ передаётся через state навигации,
  // чтобы не загружать его повторно.
  const [initialDoc] = useState(() => {
    const doc = location.state?.doc;
    return doc && String(doc.id) === id ? doc : null;
  });

  const [fields, setFields] = useState(() => (initialDoc ? toFormFields(initialDoc.fields) : emptyFields()));
  const [errors, setErrors] = useState({});
  const [formMessage, setFormMessage] = useState("");
  const [canRetry, setCanRetry] = useState(false);

  // draftFields — поля, из которых собран текущий черновик (их и сохраняем как исходные).
  const [draftFields, setDraftFields] = useState(initialDoc?.fields ?? null);
  const [text, setText] = useState(initialDoc?.text ?? null);
  const [generatedText, setGeneratedText] = useState(null);
  const [saved, setSaved] = useState(() => (initialDoc ? savedSnapshot(initialDoc) : null));
  const [docId, setDocId] = useState(initialDoc?.id ?? null);

  const [loadState, setLoadState] = useState(id && !initialDoc ? "loading" : "ready");
  const [loadError, setLoadError] = useState("");
  const [busy, setBusy] = useState(null);
  const [editorMessage, setEditorMessage] = useState("");
  const [toast, showToast] = useToast();

  function applyDoc(doc) {
    setFields(toFormFields(doc.fields));
    setDraftFields(doc.fields);
    setText(doc.text);
    setGeneratedText(null);
    setSaved(savedSnapshot(doc));
    setDocId(doc.id);
    setLoadState("ready");
  }

  useEffect(() => {
    if (!id) return;
    if (initialDoc) {
      showToast(location.state?.notice || "Документ сохранён");
      navigate(location.pathname, { replace: true, state: null });
      return;
    }
    let cancelled = false;
    api(`/api/documents/${id}`)
      .then((doc) => !cancelled && applyDoc(doc))
      .catch((err) => {
        if (cancelled) return;
        setLoadError(err.message);
        setLoadState(err.status === 404 ? "notfound" : "error");
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const dirty =
    text !== null &&
    (!saved || saved.text !== text || saved.fieldsJson !== JSON.stringify(draftFields));

  useEffect(() => {
    if (!dirty) return;
    const warn = (event) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function handleFillSample() {
    setFields(toFormFields(SAMPLE_OFFER));
    setErrors({});
    setFormMessage("");
    setCanRetry(false);
  }

  async function handleCreateDraft(event) {
    event.preventDefault();
    const editedByHand = text !== null && text !== generatedText;
    if (editedByHand && !window.confirm("Текст в редакторе будет заменён новым черновиком. Продолжить?")) {
      return;
    }
    setBusy("draft");
    setFormMessage("");
    setCanRetry(false);
    try {
      const result = await api("/api/drafts", { method: "POST", body: toApiFields(fields) });
      setErrors({});
      setDraftFields(result.fields);
      setText(result.text);
      setGeneratedText(result.text);
      setEditorMessage("");
    } catch (err) {
      // Введённые значения остаются в форме — меняем только ошибки.
      setErrors(err.errors || {});
      setFormMessage(err.message);
      setCanRetry(Boolean(err.retry));
      requestAnimationFrame(() =>
        document.querySelector(".field-error")?.scrollIntoView({ block: "center", behavior: "smooth" }),
      );
    } finally {
      setBusy(null);
    }
  }

  async function handleSave() {
    setBusy("save");
    setEditorMessage("");
    try {
      const body = { fields: draftFields, text };
      if (docId) {
        const doc = await api(`/api/documents/${docId}`, { method: "PUT", body });
        setSaved(savedSnapshot(doc));
        showToast("Документ сохранён");
      } else {
        const doc = await api("/api/documents", { method: "POST", body });
        setSaved(savedSnapshot(doc));
        navigate(`/documents/${doc.id}`, { replace: true, state: { doc, notice: "Документ сохранён" } });
      }
    } catch (err) {
      setEditorMessage(err.message);
    } finally {
      setBusy(null);
    }
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      copyWithTextarea(text);
    }
    showToast("Текст скопирован");
  }

  if (loadState === "loading") return <div className="page-message">Открываем документ…</div>;
  if (loadState === "notfound" || loadState === "error") {
    return (
      <div className="card page-message">
        <h2>{loadState === "notfound" ? "Документ недоступен" : "Не удалось открыть документ"}</h2>
        <p>{loadError}</p>
        <Link className="btn btn-primary" to="/history">
          К истории
        </Link>
      </div>
    );
  }

  return (
    <>
      <div className="offer-layout">
        <OfferForm
          fields={fields}
          errors={errors}
          message={formMessage}
          busy={busy === "draft"}
          retry={canRetry}
          onChange={setFields}
          onSubmit={handleCreateDraft}
          onFillSample={handleFillSample}
        />
        <DraftEditor
          text={text}
          onChange={setText}
          onSave={handleSave}
          onCopy={handleCopy}
          busy={busy === "save"}
          dirty={dirty}
          savedAt={saved?.updatedAt}
          message={editorMessage}
        />
      </div>
      <Toast message={toast} />
    </>
  );
}

function savedSnapshot(doc) {
  return { text: doc.text, fieldsJson: JSON.stringify(doc.fields), updatedAt: doc.updated_at };
}

function copyWithTextarea(value) {
  const area = document.createElement("textarea");
  area.value = value;
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  document.execCommand("copy");
  area.remove();
}
