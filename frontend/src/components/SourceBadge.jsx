// Метка «кто подготовил черновик». Показывается в редакторе и в «Моих предложениях».
const SOURCES = {
  template: { icon: "⚙", label: "Собрано по шаблону", className: "source-template" },
  ai: { icon: "✦", label: "Подготовил ИИ", className: "source-ai" },
};

export default function SourceBadge({ source }) {
  const info = SOURCES[source] ?? SOURCES.template;
  return (
    <span className={`source-badge ${info.className}`}>
      <span aria-hidden="true">{info.icon}</span> {info.label}
    </span>
  );
}
