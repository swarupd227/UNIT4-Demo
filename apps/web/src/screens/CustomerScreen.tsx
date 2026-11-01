import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import { ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";
import { ITEM_TYPE_KEYS, ITEM_TYPES } from "../lib/terms";
import { Panel, Screen } from "../ui/layout";
import { Skeleton } from "../ui/primitives";

export function CustomerScreen() {
  const { role } = usePersona();
  const { data } = useQuery({ queryKey: ["case", role], queryFn: () => api.case(role) });
  if (!data) {
    return (
      <div className="space-y-4 p-5">
        <Skeleton className="h-12 w-1/2" />
        <Skeleton className="h-64" />
      </div>
    );
  }
  const estate = ITEM_TYPE_KEYS.flatMap((key) => data.estate.filter((row) => row.item_type === key));
  return (
    <Screen title={data.customer_name} lead={data.goal} next="estate">
      <section className="flex items-center gap-3 rounded-lg border border-line bg-surface px-4 py-3 text-[15px] text-ink-2">
        <ShieldCheck size={20} aria-hidden className="shrink-0 text-accent" />
        <p>
          <strong className="font-semibold text-ink">Sandbox environment.</strong> Test data only, with no payroll or
          HR data. Not connected to J2X.AI or a production tenant. The ERPx target is simulated.
        </p>
      </section>
      <div className="grid grid-cols-4 gap-4">
        {estate.map((row, index) => (
          <motion.div
            key={row.item_type}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06, duration: 0.2 }}
            className="rounded-xl bg-surface p-5 shadow-panel"
          >
            <div className="tnum text-[32px] leading-none font-semibold">{row.count}</div>
            <div className="mt-2 text-[16px] text-ink-2">{ITEM_TYPES[row.item_type].estate}</div>
          </motion.div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Panel title="Customer profile">
          <dl className="grid grid-cols-[180px_1fr] gap-y-2.5 text-[16px]">
            <dt className="text-ink-3">Sector</dt>
            <dd>{data.sector}</dd>
            <dt className="text-ink-3">Size</dt>
            <dd className="tnum">About {data.staff_count.toLocaleString("en-GB")} staff</dd>
            <dt className="text-ink-3">History</dt>
            <dd className="tnum">
              Unit4 ERP since {data.erp_since}, on CR since {data.cr_since}
            </dd>
            <dt className="text-ink-3">In scope</dt>
            <dd>{data.modules_in_scope.replaceAll(";", ",")}</dd>
            <dt className="text-ink-3">Out of scope</dt>
            <dd>{data.out_of_scope}</dd>
          </dl>
        </Panel>
        <Panel title="Legal entities">
          <ul className="divide-y divide-line">
            {data.entities.map((entity) => (
              <li key={entity.entity_code} className="flex items-center justify-between gap-4 py-2.5 text-[16px]">
                <span>
                  {entity.name}
                  {entity.status === "dormant" && <span className="text-ink-3"> (dormant)</span>}
                </span>
                {entity.in_migration_scope && (
                  <span className="rounded-md bg-accent-soft px-2 py-0.5 text-[14px] font-semibold text-accent">
                    In migration scope
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </Screen>
  );
}
