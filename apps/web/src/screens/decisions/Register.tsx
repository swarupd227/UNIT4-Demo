import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type RowSelectionState,
  type SortingState,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ArrowDown, ArrowUp, ShieldAlert } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { DecisionRow } from "../../lib/api";
import { confidenceWord, usageLabel } from "../../lib/format";
import { ACTIONS, HELD_LABEL, OUTCOMES } from "../../lib/terms";
import { StatusLabel } from "../../ui/primitives";
import { refusedRetire } from "./registerModel";

// Below 1600px the confidence column drops out. It stays in the detail panel, so nothing is lost.
const COLUMNS =
  "grid-cols-[44px_88px_minmax(190px,1fr)_96px_190px_156px] min-[1600px]:grid-cols-[44px_92px_minmax(240px,1fr)_112px_minmax(190px,230px)_124px_164px]";
const wideOnly = (id: string) => (id === "confidence" ? "hidden min-[1600px]:flex" : "flex");
const ROW_HEIGHT = 66;

const column = createColumnHelper<DecisionRow>();

function DecisionCell({ row }: { row: DecisionRow }) {
  if (row.outcome === null) {
    return (
      <span className="flex flex-col">
        <span className="font-medium text-warn">{HELD_LABEL}</span>
        {refusedRetire(row) && (
          <span className="mt-0.5 inline-flex items-center gap-1 text-[13px] font-semibold text-warn">
            <ShieldAlert size={14} aria-hidden />
            Retirement blocked
          </span>
        )}
      </span>
    );
  }
  const action = row.action && ACTIONS[row.action.split(":")[0]];
  return (
    <span className="flex flex-col">
      <span className="font-medium">{OUTCOMES[row.outcome].label}</span>
      {action && <span className="text-[13px] text-ink-3">{action}</span>}
    </span>
  );
}

const columns = [
  column.display({
    id: "select",
    header: ({ table }) => (
      <input
        type="checkbox"
        aria-label="Select all shown"
        className="size-4 accent-[var(--accent)]"
        checked={table.getIsAllRowsSelected()}
        onChange={table.getToggleAllRowsSelectedHandler()}
      />
    ),
    cell: ({ row }) => (
      <input
        type="checkbox"
        aria-label={`Select ${row.original.item_id}`}
        className="size-4 accent-[var(--accent)]"
        checked={row.getIsSelected()}
        onClick={(event) => event.stopPropagation()}
        onChange={row.getToggleSelectedHandler()}
      />
    ),
  }),
  column.accessor("item_id", {
    header: "ID",
    cell: (info) => <span className="tnum font-medium">{info.getValue()}</span>,
  }),
  column.accessor("name", {
    header: "Item and reason",
    cell: ({ row }) => (
      <span className="block min-w-0">
        <span className="block truncate font-medium">{row.original.name}</span>
        <span className="block truncate text-[14px] text-ink-3">{row.original.reason}</span>
      </span>
    ),
  }),
  column.accessor("usage_12m", {
    header: "Used",
    cell: ({ row }) => (
      <span className="tnum whitespace-nowrap text-ink-2">
        {row.original.item_type === "CF" ? "n/a" : usageLabel(row.original.frequency, row.original.usage_12m)}
      </span>
    ),
  }),
  column.accessor((row) => row.outcome ?? "", {
    id: "decision",
    header: "Decision",
    cell: ({ row }) => <DecisionCell row={row.original} />,
  }),
  column.accessor((row) => row.confidence ?? -1, {
    id: "confidence",
    header: "Confidence",
    cell: ({ row }) =>
      row.original.confidence === null ? (
        <span className="text-ink-3">None</span>
      ) : (
        <span className="tnum whitespace-nowrap text-ink-2">
          {confidenceWord(row.original.confidence)} {row.original.confidence}
        </span>
      ),
  }),
  column.accessor("status", {
    header: "Status",
    cell: (info) => <StatusLabel status={info.getValue()} />,
  }),
];

type Props = {
  rows: DecisionRow[];
  selectedId: string | null;
  onOpen: (id: string) => void;
  selection: RowSelectionState;
  onSelection: (next: RowSelectionState) => void;
  onOrder: (ids: string[]) => void;
};

export function Register({ rows, selectedId, onOpen, selection, onSelection, onOrder }: Props) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, rowSelection: selection },
    getRowId: (row) => row.item_id,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onRowSelectionChange: (updater) => onSelection(typeof updater === "function" ? updater(selection) : updater),
  });

  const visible = table.getRowModel().rows;
  const scroller = useRef<HTMLDivElement>(null);
  const virtualizer = useVirtualizer({
    count: visible.length,
    getScrollElement: () => scroller.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 8,
  });

  const order = useMemo(() => visible.map((row) => row.id), [visible]);
  useEffect(() => onOrder(order), [order, onOrder]);

  const selectedIndex = selectedId ? order.indexOf(selectedId) : -1;
  useEffect(() => {
    if (selectedIndex >= 0) virtualizer.scrollToIndex(selectedIndex, { align: "auto" });
  }, [selectedIndex, virtualizer]);

  return (
    <div role="table" aria-label="Decision register" className="flex min-h-0 flex-1 flex-col">
      {table.getHeaderGroups().map((group) => (
        <div
          key={group.id}
          role="row"
          className={`grid ${COLUMNS} items-center border-b border-line-strong px-1 text-[13px] font-semibold tracking-wide text-ink-3 uppercase`}
        >
          {group.headers.map((header) => {
            const sortable = header.column.getCanSort();
            const direction = header.column.getIsSorted();
            return (
              <div key={header.id} role="columnheader" className={`${wideOnly(header.column.id)} h-11 items-center px-3`}>
                {sortable ? (
                  <button
                    type="button"
                    onClick={header.column.getToggleSortingHandler()}
                    className="inline-flex items-center gap-1 uppercase hover:text-ink"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {direction === "asc" && <ArrowUp size={13} aria-hidden />}
                    {direction === "desc" && <ArrowDown size={13} aria-hidden />}
                  </button>
                ) : (
                  flexRender(header.column.columnDef.header, header.getContext())
                )}
              </div>
            );
          })}
        </div>
      ))}

      <div ref={scroller} className="scroll-quiet min-h-0 flex-1 overflow-y-auto">
        {visible.length === 0 ? (
          <p className="p-10 text-center text-ink-2">No items match these filters.</p>
        ) : (
          <div style={{ height: virtualizer.getTotalSize(), position: "relative" }}>
            {virtualizer.getVirtualItems().map((virtual) => {
              const row = visible[virtual.index];
              const selected = row.id === selectedId;
              return (
                <div
                  key={row.id}
                  role="row"
                  aria-selected={selected}
                  onClick={() => onOpen(row.id)}
                  style={{ height: ROW_HEIGHT, transform: `translateY(${virtual.start}px)` }}
                  className={`absolute inset-x-0 top-0 grid cursor-pointer ${COLUMNS} items-center border-b border-line px-1 text-[15px] transition-colors ${
                    selected ? "bg-selected shadow-[inset_3px_0_0_var(--accent)]" : "hover:bg-surface-2"
                  }`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <div key={cell.id} role="cell" className={`${wideOnly(cell.column.id)} min-w-0 items-center px-3`}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
