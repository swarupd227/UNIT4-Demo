const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" });
const timeFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});
const monthFormat = new Intl.DateTimeFormat("en-GB", { month: "short" });

export function formatDate(value: string | null): string {
  return value ? dateFormat.format(new Date(value)) : "Never";
}

export function formatTime(value: string): string {
  return timeFormat.format(new Date(value));
}

export function formatMonth(month: string): string {
  return monthFormat.format(new Date(`${month}-01`));
}

export function usageLabel(frequency: string | null, usage: number): string {
  if (usage === 0) return "none";
  if (frequency === "nightly") return "nightly";
  if (frequency === "daily") return "daily";
  if (frequency === "weekly") return "weekly";
  if (frequency === "monthly") return "monthly";
  if (usage <= 12) return `${usage} / yr`;
  return `${usage.toLocaleString("en-GB")} / yr`;
}

export function confidenceWord(confidence: number): "High" | "Medium" | "Low" {
  if (confidence >= 85) return "High";
  return confidence >= 65 ? "Medium" : "Low";
}

// The 12-month usage window, oldest first.
export function usageWindow(): string[] {
  return Array.from({ length: 12 }, (_, i) => {
    const date = new Date(Date.UTC(2025, 10 + i, 1));
    return date.toISOString().slice(0, 7);
  });
}
