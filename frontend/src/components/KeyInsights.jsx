export default function KeyInsights({ insights }) {
  if (!insights) return null;

  const insightEntries = Object.entries(insights);

  if (insightEntries.length === 0) return null;

  const formatTitle = (key) => {
    return key
      .replace(/[_]/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }
  return (
    <section className="rounded-xl border border-orange-200 bg-[#3d2000] p-4 sm:p-5">
      <h2 className="mb-2 text-sm font-semibold text-amber-600">Key insights</h2>
      <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-amber-300">
        {insightEntries.map(([key, text]) => (
          <li key={key}>{formatTitle(key)}: {text}</li>
        ))}
      </ul>
    </section>
  );
}
