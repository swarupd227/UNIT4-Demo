import type { DecisionDetail, Evidence } from "../../lib/api";
import { formatDate } from "../../lib/format";
import { AiBadge, CodeBadge, SourceBadge } from "../../ui/primitives";
import { CodeView } from "../../ui/CodeView";
import { SideDrawer } from "../../ui/overlays";
import { UsageBars } from "../../ui/UsageBars";

type Props = { evidence: Evidence | null; item: DecisionDetail; onClose: () => void };

const CODE_VERIFIED = new Set(["usage", "keyword", "dependency", "entity", "owner", "precedent", "stale"]);

function Provenance({ kind }: { kind: string }) {
  if (kind === "j2x") return <SourceBadge>From J2X.AI (simulated)</SourceBadge>;
  if (kind === "policy") return <SourceBadge>Customer document</SourceBadge>;
  return CODE_VERIFIED.has(kind) ? <CodeBadge /> : <AiBadge />;
}

export function EvidenceDrawer({ evidence, item, onClose }: Props) {
  if (!evidence) return null;
  return (
    <SideDrawer
      open
      onClose={onClose}
      title={evidence.label}
      description={`${item.item_id} · ${item.name}`}
    >
      <div className="flex items-center gap-2 px-6 pt-4">
        <Provenance kind={evidence.kind} />
        {evidence.line && <span className="tnum text-[14px] text-ink-3">Line {evidence.line}</span>}
      </div>
      {evidence.detail && <p className="px-6 pt-3 text-[16px] leading-7 text-ink">{evidence.detail}</p>}
      {evidence.kind === "usage" && (
        <div className="px-6 pt-6">
          <h3 className="mb-4 text-[15px] font-semibold">Uses per month, last 12 months</h3>
          <UsageBars usage={item.usage_by_month} />
          <dl className="mt-6 grid grid-cols-2 gap-4 text-[15px]">
            <div>
              <dt className="text-ink-3">Total in 12 months</dt>
              <dd className="tnum font-medium">{item.usage_12m.toLocaleString("en-GB")}</dd>
            </div>
            <div>
              <dt className="text-ink-3">Last used</dt>
              <dd className="tnum font-medium">{formatDate(item.last_used)}</dd>
            </div>
          </dl>
        </div>
      )}
      {evidence.kind === "code" && item.source_text && (
        <div className="mt-4 border-t border-line">
          <CodeView source={item.source_text} focusLine={evidence.line} />
        </div>
      )}
    </SideDrawer>
  );
}
