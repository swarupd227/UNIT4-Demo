import { formatMonth, usageWindow } from "../lib/format";

type Props = { usage: { month: string; count: number }[] };

// One series, so no legend: the heading names it. Each column is a full-height hover target.
export function UsageBars({ usage }: Props) {
  const counts = new Map(usage.map((row) => [row.month, row.count]));
  const months = usageWindow().map((month) => ({ month, count: counts.get(month) ?? 0 }));
  const max = Math.max(...months.map((row) => row.count), 1);

  return (
    <figure>
      <div className="flex h-44 items-end gap-1.5 border-b border-line-strong" aria-hidden>
        {months.map(({ month, count }) => (
          <div key={month} className="group relative flex h-full flex-1 items-end">
            <div
              className="w-full rounded-t bg-accent transition-opacity group-hover:opacity-80"
              style={{ height: count ? `${Math.max((count / max) * 100, 3)}%` : 0 }}
            />
            <div className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 rounded-md bg-spine px-2 py-1 text-[13px] whitespace-nowrap text-on-spine group-hover:block">
              {formatMonth(month)}: {count.toLocaleString("en-GB")}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-1.5 flex gap-1.5 text-[13px] text-ink-3" aria-hidden>
        {months.map(({ month }) => (
          <span key={month} className="flex-1 text-center">
            {formatMonth(month)}
          </span>
        ))}
      </div>
      <table className="sr-only">
        <caption>Uses per month</caption>
        <tbody>
          {months.map(({ month, count }) => (
            <tr key={month}>
              <th scope="row">{month}</th>
              <td>{count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
