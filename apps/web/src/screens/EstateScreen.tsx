import { useQuery } from "@tanstack/react-query";
import { Check, Download } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { usePersona } from "../lib/persona";
import { ITEM_TYPE_KEYS, ITEM_TYPES } from "../lib/terms";
import { workbench } from "../lib/workbench";
import { Panel, Screen } from "../ui/layout";
import { Button, Skeleton, SourceBadge } from "../ui/primitives";

const LOADED_KEY = "studio.estate-loaded";
const STAGES = ["Assessment", "Decision", "Technical execution", "Validation", "Customer acceptance"];

function wasLoaded(): boolean {
  try {
    return sessionStorage.getItem(LOADED_KEY) === "1";
  } catch {
    return false;
  }
}

export function EstateScreen() {
  const { role } = usePersona();
  const { data } = useQuery({ queryKey: ["estate"], queryFn: () => workbench.estate(role) });
  const [step, setStep] = useState(wasLoaded() ? 99 : -1);

  const sources = data
    ? [
        { label: "J2X.AI assessment", detail: "Assessment dated 14 September 2026" },
        { label: "Custom code", detail: `${data.types.find((t) => t.item_type === "CC")?.count} items` },
        { label: "Reports and usage logs", detail: `${data.volumes.usage_events.toLocaleString("en-GB")} usage records` },
        { label: "Configuration", detail: `${data.volumes.accounts.toLocaleString("en-GB")} accounts` },
        { label: "UK data extract", detail: `${data.volumes.receivables.toLocaleString("en-GB")} receivables, ${data.volumes.payables.toLocaleString("en-GB")} payables` },
      ]
    : [];
  const done = step >= sources.length && sources.length > 0;

  useEffect(() => {
    if (step < 0 || done) return;
    const timer = setTimeout(() => setStep((current) => current + 1), 380);
    return () => clearTimeout(timer);
  }, [step, done]);

  useEffect(() => {
    if (!done) return;
    try {
      sessionStorage.setItem(LOADED_KEY, "1");
    } catch {
      // Remembering this only skips the animation.
    }
  }, [done]);

  if (!data) return <Skeleton className="m-5 h-96" />;
  const types = ITEM_TYPE_KEYS.flatMap((key) => data.types.filter((row) => row.item_type === key));

  return (
    <Screen
      title="CR estate"
      lead="J2X.AI assessment and source inventory"
      next={done ? "decisions" : undefined}
      aside={
        step < 0 && (
          <Button variant="primary" onClick={() => setStep(0)}>
            <Download size={18} aria-hidden />
            Load estate
          </Button>
        )
      }
    >
      <Panel title="Sources">
        <ol className="grid grid-cols-5 gap-3">
          {sources.map((source, index) => {
            const loaded = index < step;
            return (
              <li
                key={source.label}
                className={`rounded-lg border p-3 transition-colors ${
                  loaded ? "border-accent bg-selected" : "border-line text-ink-3"
                }`}
              >
                <span className="flex items-center gap-1.5 text-[16px] font-medium">
                  {loaded && <Check size={17} className="text-accent" aria-hidden />}
                  {source.label}
                </span>
                <span className="tnum mt-0.5 block text-[14px] text-ink-2">{source.detail}</span>
              </li>
            );
          })}
        </ol>
      </Panel>

      {done && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
          <Panel
            title="Estate map"
            aside={
              <span className="flex items-center gap-4 text-[14px] text-ink-2">
                <span className="flex items-center gap-1.5">
                  <i className="size-3 rounded-sm bg-accent" /> Explained by J2X
                </span>
                <span className="flex items-center gap-1.5">
                  <i className="size-3 rounded-sm bg-neutral-mark" /> Not yet explained
                </span>
              </span>
            }
          >
            <ul className="space-y-3.5">
              {types.map((row) => (
                <li key={row.item_type} className="grid grid-cols-[190px_1fr_170px] items-center gap-4">
                  <span className="text-[16px] font-medium">{ITEM_TYPES[row.item_type].estate}</span>
                  <span className="flex h-4 gap-0.5" title={`${row.j2x_explained} of ${row.count} explained by J2X`}>
                    {row.j2x_explained > 0 && (
                      <span className="rounded-l bg-accent" style={{ flexGrow: row.j2x_explained, flexBasis: 0 }} />
                    )}
                    {row.count > row.j2x_explained && (
                      <span
                        className="rounded-r bg-neutral-mark"
                        style={{ flexGrow: row.count - row.j2x_explained, flexBasis: 0 }}
                      />
                    )}
                  </span>
                  <span className="tnum text-right text-[15px] text-ink-2">
                    {row.j2x_explained} of {row.count} explained
                  </span>
                </li>
              ))}
            </ul>
          </Panel>
          <div className="grid grid-cols-2 gap-4">
            <Panel title="Time by stage">
              <table className="w-full text-[16px]">
                <tbody className="divide-y divide-line">
                  {STAGES.map((stage) => (
                    <tr key={stage}>
                      <th scope="row" className="py-2 text-left font-normal">
                        {stage}
                      </th>
                      <td className="py-2 text-right text-ink-3">Baseline pending</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
            <Panel title={`${data.integrations.length} integrations`} aside={<SourceBadge>Listed only</SourceBadge>}>
              <ul className="grid grid-cols-2 gap-x-6 gap-y-1 text-[15px]">
                {data.integrations.map((integration) => (
                  <li key={integration.item_id} className="flex gap-2">
                    <span className="tnum text-ink-3">{integration.item_id}</span>
                    <span className="truncate">{integration.name}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          </div>
        </motion.div>
      )}
    </Screen>
  );
}
