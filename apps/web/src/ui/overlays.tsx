import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

type OverlayProps = {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  description?: ReactNode;
  children: ReactNode;
};

export function Modal({ open, onClose, title, description, children }: OverlayProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-spine/40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 z-40 w-[560px] max-w-[calc(100vw-32px)] -translate-x-1/2 -translate-y-1/2 rounded-xl bg-surface p-6 shadow-float">
          <Dialog.Title className="text-xl font-semibold">{title}</Dialog.Title>
          <Dialog.Description className="mt-1 text-[15px] text-ink-2">{description}</Dialog.Description>
          <div className="mt-5">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function SideDrawer({ open, onClose, title, description, children }: OverlayProps) {
  return (
    <Dialog.Root open={open} onOpenChange={(next) => !next && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-spine/30" />
        <Dialog.Content className="fixed inset-y-0 right-0 z-40 flex w-[860px] max-w-[92vw] flex-col bg-surface shadow-float">
          <header className="flex items-start justify-between gap-4 border-b border-line px-6 py-4">
            <div>
              <Dialog.Title className="text-xl font-semibold">{title}</Dialog.Title>
              <Dialog.Description className="mt-0.5 text-[15px] text-ink-2">{description}</Dialog.Description>
            </div>
            <Dialog.Close
              aria-label="Close"
              className="rounded-md p-2 text-ink-2 transition-colors hover:bg-line/50"
            >
              <X size={20} />
            </Dialog.Close>
          </header>
          <div className="scroll-quiet min-h-0 flex-1 overflow-y-auto">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
