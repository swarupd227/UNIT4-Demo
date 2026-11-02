import { useQuery } from "@tanstack/react-query";
import { Link2, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { usePersona } from "../lib/persona";
import { acceptLabel } from "../lib/terms";
import { workbench } from "../lib/workbench";
import { CodeView } from "../ui/CodeView";
import { Panel, Screen, useDecision } from "../ui/layout";
import { AiBadge, Button, Skeleton, SourceBadge, StatusLabel } from "../ui/primitives";
import { AskDialog } from "./decisions/DecisionDialogs";
import { LiveAgentButton } from "./LiveAgentButton";
import { OntologyChips } from "./OntologyChips";
import { useDecisionActions } from "./decisions/useDecisionActions";

const ITEMS = ["CC-014", "CC-041", "CC-037"];
type Tab = "rule" | "spec" | "skeleton" | "tests";

type Citation = { text: string; find: string; line: number };
type Explanation = {
  plain_english: string;
  purpose_known: boolean;
  ontology_concepts: string[];
  steps: Citation[];
  hidden_rules: Citation[];
  cloud_blockers: Citation[];
};

function CitationList({ title, items, onHover }: {
  title: string;
  items: Citation[];
  onHover: (line: number | undefined) => void;
}) {
  if (items.length === 0) return null;
  return (
    <section>
      <h3 className="mb-1.5 text-[13px] font-semibold tracking-wide text-ink-3 uppercase">{title}</h3>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={`${item.line}-${item.text}`}>
            <button
              type="button"
              onMouseEnter={() => onHover(item.line)}
              onFocus={() => onHover(item.line)}
              onClick={() => onHover(item.line)}
              className="w-full rounded-md px-2 py-1.5 text-left text-[15px] leading-6 transition-colors hover:bg-warn-soft focus:bg-warn-soft"
            >
              {item.text}
              <span className="tnum ml-1.5 text-[13px] text-ink-3">line {item.line}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <section>
      <h3 className="mb-1 text-[13px] font-semibold tracking-wide text-ink-3 uppercase">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-[15px] leading-6">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function RuleTab({ rule, onHover }: { rule: any; onHover: (line?: number) => void }) {
  return (
    <div className="space-y-4">
      <p className="text-[16px] leading-7">{rule.statement}</p>
      <dl className="grid grid-cols-[110px_1fr] gap-y-1.5 text-[15px]">
        <dt className="text-ink-3">Applies to</dt>
        <dd>{rule.applies_to}</dd>
        <dt className="text-ink-3">Approver</dt>
        <dd>{rule.approver}</dd>
        <dt className="text-ink-3">Stored in</dt>
        <dd>{rule.stored_in}</dd>
        <dt className="text-ink-3">Policy</dt>
        <dd>{rule.policy_reference}</dd>
      </dl>
      <CitationList title="Source lines" items={rule.sources} onHover={onHover} />
    </div>
  );
}

function SpecTab({ spec }: { spec: any }) {
  return (
    <div className="space-y-4">
      <p className="text-[16px] leading-7">{spec.summary}</p>
      <List title="Standard covers" items={spec.standard_coverage} />
      <List title={`Extension: ${spec.extension_name}`} items={spec.behaviour} />
      <List title="API calls" items={spec.api_calls.map((call: any) => `${call.purpose}: ${call.call}`)} />
      <List title="Dependencies" items={spec.dependencies} />
      <List title="Open points" items={spec.open_points} />
      <p className="text-[14px] text-ink-3">{spec.caveat}</p>
    </div>
  );
}

function TestsTab({ tests }: { tests: any }) {
  return (
    <table className="w-full text-[15px]">
      <thead>
        <tr className="text-left text-[13px] tracking-wide text-ink-3 uppercase">
          <th className="py-1 font-semibold">Case</th>
          <th className="py-1 text-center font-semibold">At 10%</th>
          <th className="py-1 text-center font-semibold">At 15%</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {tests.cases.map((test: any) => {
          const differs = test.expected_at_10 !== test.expected_at_15;
          return (
            <tr key={test.id} className={differs ? "bg-warn-soft" : ""}>
              <td className="py-1.5 pr-2">{test.description}</td>
              <td className="py-1.5 text-center capitalize">{test.expected_at_10}</td>
              <td className="py-1.5 text-center capitalize">{test.expected_at_15}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function CodeScreen() {
  const { itemId = "CC-014" } = useParams();
  const { role } = usePersona();
  const { data: item } = useDecision(itemId);
  const { data: artefacts } = useQuery({
    queryKey: ["artefacts", itemId],
    queryFn: () => workbench.artefacts(itemId, role),
  });
  const actions = useDecisionActions(itemId);
  const [line, setLine] = useState<number | undefined>();
  const [tab, setTab] = useState<Tab>("rule");
  const [asking, setAsking] = useState(false);

  const content = (kind: string): any => artefacts?.find((a) => a.kind === kind)?.content;
  const explanation: Explanation | undefined = content("code_explanation");
  const explanationSource = artefacts?.find((a) => a.kind === "code_explanation")?.source;
  const rule = content("rule_card");
  const spec = content("extension_spec");
  const tests = content("test_cases");
  const tabs: [Tab, string, unknown][] = [
    ["rule", "Rule card", rule],
    ["spec", "Extension spec", spec],
    ["skeleton", "Skeleton", spec?.code_skeleton],
    ["tests", "Tests", tests],
  ];
  const dependencies = item?.evidence.filter((entry) => entry.kind === "dependency") ?? [];
  const answered = item?.questions.findLast((question) => question.status === "answered");

  return (
    <Screen
      title="Custom code"
      lead="Code analysis, rule extraction and extension design"
      next="reports"
      aside={
        <nav className="flex rounded-lg border border-line-strong bg-surface p-0.5" aria-label="Code items">
          {ITEMS.map((id) => (
            <Link
              key={id}
              to={`/code/${id}`}
              onClick={() => setLine(undefined)}
              className={`tnum rounded-md px-3 py-1.5 text-[15px] font-medium ${
                id === itemId ? "bg-ink text-canvas" : "text-ink-2 hover:text-ink"
              }`}
            >
              {id}
            </Link>
          ))}
        </nav>
      }
    >
      {!item || !explanation ? (
        <Skeleton className="h-[700px]" />
      ) : (
        <>
          <Panel className="flex items-center justify-between gap-6">
            <div className="min-w-0">
              <h2 className="text-[20px] font-semibold">{item.name}</h2>
              <p className="text-[16px] leading-6 text-ink-2">{explanation.plain_english}</p>
              <OntologyChips ids={explanation.ontology_concepts} />
            </div>
            <div className="flex shrink-0 items-center gap-3">
              <StatusLabel status={item.status} />
              <Button variant="primary" disabled={!item.allowed.accept} onClick={() => actions.accept.mutate(itemId)}>
                {acceptLabel(role, item.outcome)} design
              </Button>
              <Button disabled={!item.allowed.ask} onClick={() => setAsking(true)}>
                Raise a question
              </Button>
            </div>
          </Panel>

          {item.conflict && (
            <section
              className={`flex items-center gap-6 rounded-xl border p-4 ${
                answered ? "border-ok/30 bg-ok-soft" : "border-bad/30 bg-bad-soft"
              }`}
            >
              <TriangleAlert size={24} className={answered ? "text-ok" : "text-bad"} aria-hidden />
              <h3 className="text-[17px] font-semibold">
                {answered ? "Resolved" : "Conflict"}: {item.conflict.topic.toLowerCase()}
              </h3>
              <div className="tnum flex items-baseline gap-2 text-[15px]">
                <span className="text-[28px] font-semibold">{item.conflict.left_value}</span>
                {item.conflict.left_label}
              </div>
              <span className="text-ink-3">against</span>
              <div className="tnum flex items-baseline gap-2 text-[15px]">
                <span className="text-[28px] font-semibold">{item.conflict.right_value}</span>
                {item.conflict.right_label}
              </div>
              {answered && <span className="ml-auto text-[15px] font-medium">{answered.answer}</span>}
            </section>
          )}

          <div className="grid grid-cols-[minmax(0,1fr)_420px_460px] gap-4">
            <Panel className="overflow-hidden !p-0">
              <div tabIndex={0} role="region" aria-label="Source code" className="scroll-quiet h-[560px] overflow-y-auto">
                <CodeView source={item.source_text ?? ""} focusLine={line} />
              </div>
            </Panel>
            <Panel
              title="Explanation"
              aside={
                <span className="flex items-center gap-2">
                  <AiBadge source={explanationSource} />
                  <LiveAgentButton agent="code_explainer" subject={itemId} />
                </span>
              }
            >
              <div tabIndex={0} role="region" aria-label="Explanation" className="scroll-quiet h-[488px] space-y-4 overflow-y-auto">
                <CitationList title="Logic" items={explanation.steps} onHover={setLine} />
                <CitationList title="Embedded rules" items={explanation.hidden_rules} onHover={setLine} />
                <CitationList title="Cloud blockers" items={explanation.cloud_blockers} onHover={setLine} />
                {dependencies.map((dependency) => (
                  <p key={dependency.label} className="flex gap-2 rounded-lg bg-warn-soft p-3 text-[15px] leading-6">
                    <Link2 size={18} className="mt-1 shrink-0 text-warn" aria-hidden />
                    <span>
                      <strong>{dependency.label}.</strong> {dependency.detail}
                    </span>
                  </p>
                ))}
              </div>
            </Panel>
            <Panel>
              {rule || spec || tests ? (
                <>
                  <div className="mb-3 flex gap-1 border-b border-line" role="tablist">
                    {tabs
                      .filter(([, , present]) => present)
                      .map(([key, label]) => (
                        <button
                          key={key}
                          type="button"
                          role="tab"
                          aria-selected={tab === key}
                          onClick={() => setTab(key)}
                          className={`-mb-px border-b-2 px-3 py-2 text-[15px] font-medium ${
                            tab === key ? "border-accent text-ink" : "border-transparent text-ink-3 hover:text-ink"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                  </div>
                  <div tabIndex={0} role="region" aria-label={`${tab} detail`} className="scroll-quiet h-[484px] overflow-y-auto">
                    {tab === "rule" && rule && <RuleTab rule={rule} onHover={setLine} />}
                    {tab === "spec" && spec && <SpecTab spec={spec} />}
                    {tab === "skeleton" && spec && <CodeView source={spec.code_skeleton.join("\n")} />}
                    {tab === "tests" && tests && <TestsTab tests={tests} />}
                  </div>
                </>
              ) : (
                <div className="text-[16px] leading-7">
                  <h2 className="mb-2 text-[18px] font-semibold">
                    {explanation.purpose_known ? "No rule card needed" : "No automatic decision"}
                  </h2>
                  <p className="text-ink-2">{item.reason}</p>
                </div>
              )}
            </Panel>
          </div>

          {spec?.agentification_idea && (
            <section className="flex items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-[15px] text-ink-2">
              <SourceBadge>Idea only</SourceBadge>
              <p>
                <strong className="font-semibold text-ink">Agentification.</strong> {spec.agentification_idea}
              </p>
            </section>
          )}
        </>
      )}
      {asking && item && (
        <AskDialog
          item={item}
          onClose={() => setAsking(false)}
          onSend={(question, options) => {
            actions.ask.mutate({ question, options });
            setAsking(false);
          }}
        />
      )}
    </Screen>
  );
}
