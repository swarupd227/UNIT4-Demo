import { useQuery } from "@tanstack/react-query";
import { usePersona } from "../lib/persona";
import { workbench } from "../lib/workbench";

// The concepts an analysis relied on. The gateway rejects any it was not given.
export function OntologyChips({ ids }: { ids?: string[] }) {
  const { role } = usePersona();
  const { data } = useQuery({ queryKey: ["ontology"], queryFn: () => workbench.ontology(role) });
  if (!data || !ids?.length) return null;
  return (
    <p className="mt-2 flex flex-wrap items-center gap-1.5 text-[14px] text-ink-3">
      <span className="font-medium">Grounded in the ontology:</span>
      {ids.map((id) => (
        <span
          key={id}
          title={data.concepts[id]?.meaning}
          className="rounded-md bg-accent-soft px-1.5 py-0.5 text-[13px] font-medium text-accent"
        >
          {data.concepts[id]?.label ?? id}
        </span>
      ))}
    </p>
  );
}
