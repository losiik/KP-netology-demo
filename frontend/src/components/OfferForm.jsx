import { formatRub, previewTotal } from "../money.js";
import { emptyService } from "../offerFields.js";

// Форма «Новое предложение». Проверку полей делает сервер (POST /api/drafts),
// ошибки приходят в errors: { client: "...", "services.0.price": "...", ... }.
export default function OfferForm({ fields, errors, message, busy, retry, onChange, onSubmit, onFillSample }) {
  const set = (name) => (event) => onChange({ ...fields, [name]: event.target.value });

  const setService = (index, name) => (event) => {
    const services = fields.services.map((s, i) =>
      i === index ? { ...s, [name]: event.target.value } : s,
    );
    onChange({ ...fields, services });
  };

  const addService = () => onChange({ ...fields, services: [...fields.services, emptyService()] });
  const removeService = (index) =>
    onChange({ ...fields, services: fields.services.filter((_, i) => i !== index) });

  const { total, invalid } = previewTotal(fields.services);

  return (
    <form className="card offer-form" onSubmit={onSubmit} noValidate>
      <div className="card-head">
        <h2>Новое предложение</h2>
        <button type="button" className="btn btn-ghost" onClick={onFillSample}>
          Подставить пример
        </button>
      </div>

      {message && (
        <div className="alert alert-error" role="alert">
          {message}
        </div>
      )}

      <Field id="client" label="Клиент" hint="Название компании" error={errors.client}>
        <input id="client" value={fields.client} onChange={set("client")} />
      </Field>

      <Field id="task" label="Задача" hint="Что нужно сделать для клиента" error={errors.task}>
        <textarea id="task" rows={3} value={fields.task} onChange={set("task")} />
      </Field>

      <fieldset className="field">
        <legend className="label">Услуги</legend>
        <div className="services">
          <div className="services-head" aria-hidden="true">
            <span>Название</span>
            <span>Цена, ₽</span>
            <span />
          </div>
          {fields.services.map((service, index) => {
            const nameError = errors[`services.${index}.name`];
            const priceError = errors[`services.${index}.price`];
            return (
              <div className="service-row" key={service.key}>
                <div>
                  <input
                    aria-label={`Название услуги ${index + 1}`}
                    aria-invalid={Boolean(nameError)}
                    className={nameError ? "invalid" : ""}
                    value={service.name}
                    onChange={setService(index, "name")}
                  />
                  {nameError && <p className="field-error">{nameError}</p>}
                </div>
                <div>
                  <input
                    aria-label={`Цена услуги ${index + 1}`}
                    aria-invalid={Boolean(priceError)}
                    className={`price ${priceError ? "invalid" : ""}`}
                    inputMode="decimal"
                    value={service.price}
                    onChange={setService(index, "price")}
                  />
                  {priceError && <p className="field-error">{priceError}</p>}
                </div>
                <button
                  type="button"
                  className="btn btn-icon"
                  onClick={() => removeService(index)}
                  disabled={fields.services.length === 1}
                  aria-label={`Удалить услугу ${index + 1}`}
                  title="Удалить строку"
                >
                  ×
                </button>
              </div>
            );
          })}
        </div>
        {errors.services && <p className="field-error">{errors.services}</p>}
        <button type="button" className="btn btn-secondary" onClick={addService}>
          + Добавить услугу
        </button>
      </fieldset>

      <div className="total-box" aria-live="polite">
        <span>Итоговая стоимость</span>
        <strong>{formatRub(total)}</strong>
        {invalid && <small>Часть цен не распознана и не учтена</small>}
      </div>

      <Field id="deadline" label="Срок" hint="Например, «15 рабочих дней»" error={errors.deadline}>
        <input id="deadline" value={fields.deadline} onChange={set("deadline")} />
      </Field>

      <Field
        id="extra_terms"
        label="Дополнительные условия"
        hint="Необязательно. Например, «Предоплата 50%»"
        error={errors.extra_terms}
      >
        <input id="extra_terms" value={fields.extra_terms} onChange={set("extra_terms")} />
      </Field>

      <button type="submit" className="btn btn-primary btn-wide" disabled={busy}>
        {busy ? "Готовим черновик…" : retry ? "Повторить" : "Создать черновик"}
      </button>
    </form>
  );
}

function Field({ id, label, hint, error, children }) {
  return (
    <div className={`field ${error ? "has-error" : ""}`}>
      <label className="label" htmlFor={id}>
        {label}
      </label>
      {hint && <p className="hint">{hint}</p>}
      {children}
      {error && (
        <p className="field-error" id={`${id}-error`}>
          {error}
        </p>
      )}
    </div>
  );
}
