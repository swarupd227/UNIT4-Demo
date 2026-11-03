export type AreaCard = {
  area: string;
  module: string;
  rules: number;
  critical_rules: number;
  manual_cases: number;
  automated_tests: number;
  defects: number;
  code_files: number;
  code_lines: number;
  help_pages: number;
  gate_percent: number;
};

async function get<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`The server could not load ${path} (${response.status}).`);
  return response.json() as Promise<T>;
}

export const api = {
  area: () => get<AreaCard>("/api/area"),
};
