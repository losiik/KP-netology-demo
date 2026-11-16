// Предварительный расчёт суммы в браузере — только для подсказки.
// Итог для черновика всё равно пересчитывает сервер.

export function parsePrice(raw) {
  const cleaned = String(raw ?? "")
    .replace(/[\s ₽]/g, "")
    .replace(",", ".");
  if (!cleaned) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(cleaned)) return NaN;
  return Number(cleaned);
}

export function previewTotal(services) {
  let kopecks = 0;
  let invalid = false;
  for (const service of services) {
    const price = parsePrice(service.price);
    if (price === null) continue;
    if (Number.isNaN(price)) invalid = true;
    else kopecks += Math.round(price * 100);
  }
  return { total: kopecks / 100, invalid };
}

export function formatRub(amount) {
  const [integer, fraction] = Number(amount).toFixed(2).split(".");
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return fraction === "00" ? `${grouped} ₽` : `${grouped},${fraction} ₽`;
}

export function formatDate(iso) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
