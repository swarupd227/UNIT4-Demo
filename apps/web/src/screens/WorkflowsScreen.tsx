import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, FileText, Send } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { WORKFLOW_PACK_PATH, workbench, type WorkflowVariant } from "../lib/workbench";
import { useDecision, Panel, Screen } from "../ui/layout";
import { AiBadge, Button, CodeBadge, Skeleton } from "../ui/primitives";
import { useRefresh } from "./decisions/useDecisionActions";
import { LiveAgentButton } from "./LiveAgentButton";

const PACK_ITEM = "WF-001";
const PACK_OPTIONS = ["Adopt the three workflows", "Keep the nine workflows"];

function disposition(variant: WorkflowVariant): { label: string; tone: string } {
  if (variant.outcome === "retire") return { label: "Retire", tone: "text-bad" };
  if (variant.action?.startsWith("merge_into:")) {
    return { label: `Merges into ${variant.action.split(":")[1]}`, tone: "text-ink-3" };
  }
  return { label: "Keep", tone: "text-accent" };
}

export function WorkflowsScreen() {
  const { role } = usePersona();
  const toast = useToast();
  const refresh = useRefresh();
  const { data } = useQuery({ queryKey: ["workflows"], queryFn: () => workbench.workflows(role) });
  const { data: packItem } = useDecision(PACK_ITEM);
  const [proposal, setProposal] = useState(false);

  const send = useMutation({
    mutationFn: () => api.ask(PACK_ITEM, role, data?.pack.decision_needed ?? "", PACK_OPTIONS),
    onSuccess: () => toast("Decision pack sent to the customer"),
    onError: (error: Error) => toast(error.message, "bad"),
    onSettled: refresh,
  });

  if (!data) return <Skeleton className="m-5 h-96" />;
  const { variants, pack, pack_source: packSource } = data;
  const max = Math.max(...variants.map((variant) => variant.usage_12m));
  const total = variants.reduce((sum, variant) => sum + variant.usage_12m, 0);
  const topTwo = variants[0].usage_12m + variants[1].usage_12m;
  const sent = packItem?.questions.some((question) => question.question.startsWith("Ardleigh's finance lead"));

  return (
    <Screen
      title="Approval workflows"
      lead={`${variants.length} variants, ${pack.to_count} proposed. The top two handle ${Math.round((topTwo / total) * 100)}% of ${total.toLocaleString("en-GB")} approvals in 12 months.`}
      next="reconcile"
      aside={
        !proposal && (
          <Button variant="primary" onClick={() => setProposal(true)}>
            View proposal
          </Button>
        )
      }
    >
      <div className={`grid gap-4 ${proposal ? "grid-cols-[minmax(0,1fr)_minmax(0,1fr)]" : "grid-cols-1"}`}>
        <Panel title="Use in the last 12 months" aside={<CodeBadge />}>
          <ul className="space-y-2.5">
            {variants.map((variant) => {
              const { label, tone } = disposition(variant);
              return (
                <li key={variant.item_id}>
                  <div className="flex items-baseline justify-between gap-3 text-[16px]">
                    <span>
                      <span className="tnum mr-2 text-ink-3">{variant.item_id}</span>
                      {variant.name}
                    </span>
                    <span className="flex shrink-0 items-baseline gap-4">
                      {proposal && <span className={`text-[14px] font-semibold ${tone}`}>{label}</span>}
                      <span className="tnum w-14 text-right font-medium">{variant.usage_12m.toLocaleString("en-GB")}</span>
                    </span>
                  </div>
                  <div className="mt-1 h-2.5 rounded-sm bg-canvas">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.max((variant.usage_12m / max) * 100, 0.6)}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full rounded-sm ${variant.outcome === "retire" ? "bg-bad" : "bg-accent"}`}
                    />
                  </div>
                  {proposal && variant.flags.includes("dormant_use") && (
                    <p className="mt-1 text-[14px] text-bad">Used only by a dormant legal entity</p>
                  )}
                </li>
              );
            })}
          </ul>
        </Panel>

        {proposal && (
          <motion.div initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} className="space-y-4">
            <Panel
              title={pack.headline}
              aside={
                <span className="flex items-center gap-2">
                  <AiBadge source={packSource} />
                  <LiveAgentButton agent="workflow_pack" subject={PACK_ITEM} />
                </span>
              }
            >
              <ul className="space-y-3">
                {pack.proposed.map((workflow) => (
                  <li key={workflow.keeps} className="rounded-lg border border-line p-3">
                    <div className="flex items-center gap-2 text-[16px] font-semibold">
                      {workflow.name}
                      <span className="tnum text-[14px] font-normal text-ink-3">{workflow.keeps}</span>
                    </div>
                    <p className="text-[15px] text-ink-2">{workflow.rule}</p>
                    <ul className="mt-1 list-disc pl-5 text-[14px] leading-6 text-ink-2">
                      {workflow.erpx_configuration.map((line) => (
                        <li key={line}>{line}</li>
                      ))}
                    </ul>
                    {workflow.absorbs.length > 0 && (
                      <p className="tnum mt-1 flex items-center gap-1.5 text-[14px] text-ink-3">
                        {workflow.absorbs.join(", ")}
                        <ArrowRight size={14} aria-hidden /> {workflow.keeps}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            </Panel>
            <Panel title="Control impact">
              <ul className="list-disc space-y-1 pl-5 text-[15px] leading-6">
                {pack.control_impact.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <p className="mt-3 text-[15px] font-medium">{pack.decision_needed}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <a
                  href={WORKFLOW_PACK_PATH}
                  target="_blank"
                  rel="noopener"
                  className="inline-flex h-11 items-center gap-2 rounded-lg border border-line-strong px-4 text-[15px] font-medium hover:bg-surface-2"
                >
                  <FileText size={17} aria-hidden />
                  Open decision pack
                </a>
                <Button
                  variant="primary"
                  disabled={sent || !packItem?.allowed.ask || send.isPending}
                  onClick={() => send.mutate()}
                >
                  <Send size={17} aria-hidden />
                  {sent ? "Sent to the customer" : "Send pack to customer"}
                </Button>
              </div>
            </Panel>
            <Panel title="Test cases">
              <table className="w-full text-[15px]">
                <tbody className="divide-y divide-line">
                  {pack.tests.map((test) => (
                    <tr key={test.id}>
                      <th scope="row" className="tnum py-1.5 pr-3 text-left align-top font-semibold">{test.id}</th>
                      <td className="py-1.5 pr-3 align-top">{test.description}</td>
                      <td className="py-1.5 align-top text-ink-2">{test.expected}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Panel>
          </motion.div>
        )}
      </div>
    </Screen>
  );
}
