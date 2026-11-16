// Поля формы КП и преобразование между видом формы и видом API.

let nextKey = 1;
const newKey = () => `row-${nextKey++}`;

export const SAMPLE_OFFER = {
  client: "Кофейня «Зерно»",
  task: "Запустить сайт с меню и формой заказа.",
  services: [
    { name: "Дизайн", price: "30000" },
    { name: "Разработка", price: "50000" },
  ],
  deadline: "15 рабочих дней",
  extra_terms: "Предоплата 50%",
};

export function emptyService() {
  return { key: newKey(), name: "", price: "" };
}

export function emptyFields() {
  return { client: "", task: "", services: [emptyService()], deadline: "", extra_terms: "" };
}

// Из API (или образца) — в состояние формы: у каждой строки услуги свой key для React.
export function toFormFields(fields) {
  return {
    client: fields.client ?? "",
    task: fields.task ?? "",
    services: (fields.services ?? []).map((s) => ({
      key: newKey(),
      name: s.name ?? "",
      price: String(s.price ?? ""),
    })),
    deadline: fields.deadline ?? "",
    extra_terms: fields.extra_terms ?? "",
  };
}

// Из формы — в тело запроса.
export function toApiFields(fields) {
  return {
    client: fields.client,
    task: fields.task,
    services: fields.services.map(({ name, price }) => ({ name, price })),
    deadline: fields.deadline,
    extra_terms: fields.extra_terms,
  };
}
