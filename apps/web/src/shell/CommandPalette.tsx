import { useQuery } from "@tanstack/react-query";
import { Command } from "cmdk";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { usePersona } from "../lib/persona";

type Props = { open: boolean; onClose: () => void };

const ITEM = "flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-[15px] data-[selected=true]:bg-selected";

export function CommandPalette({ open, onClose }: Props) {
  const { role } = usePersona();
  const navigate = useNavigate();
  const { data = [] } = useQuery({
    queryKey: ["decisions"],
    queryFn: () => api.decisions(role),
    enabled: open,
  });

  return (
    <Command.Dialog
      open={open}
      onOpenChange={(next) => !next && onClose()}
      label="Jump to an item"
      overlayClassName="fixed inset-0 z-40 bg-spine/40"
      contentClassName="fixed top-[16vh] left-1/2 z-40 w-[640px] -translate-x-1/2 overflow-hidden rounded-xl bg-surface shadow-float"
    >
      <Command.Input
        placeholder="Find an item by ID or name"
        className="h-14 w-full border-b border-line bg-transparent px-5 text-[17px] outline-none"
      />
      <Command.List className="scroll-quiet max-h-96 overflow-y-auto p-2">
        <Command.Empty className="p-6 text-center text-ink-2">Nothing found.</Command.Empty>
        {data.map((row) => (
          <Command.Item
            key={row.item_id}
            value={`${row.item_id} ${row.name}`}
            onSelect={() => {
              navigate(`/decisions/${row.item_id}`);
              onClose();
            }}
            className={ITEM}
          >
            <span className="tnum w-20 shrink-0 font-medium">{row.item_id}</span>
            <span className="truncate text-ink-2">{row.name}</span>
          </Command.Item>
        ))}
      </Command.List>
    </Command.Dialog>
  );
}
