import { AnimatePresence, motion } from "motion/react";
import { CheckCircle2, CircleAlert } from "lucide-react";
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type Toast = { message: string; tone: "ok" | "bad" };
type Notify = (message: string, tone?: Toast["tone"]) => void;

const Context = createContext<Notify | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<Toast | null>(null);
  const timer = useRef<number | undefined>(undefined);

  const notify = useCallback<Notify>((message, tone = "ok") => {
    window.clearTimeout(timer.current);
    setToast({ message, tone });
    timer.current = window.setTimeout(() => setToast(null), 3600);
  }, []);

  return (
    <Context.Provider value={notify}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-6 z-50 flex justify-center">
        <AnimatePresence>
          {toast && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={{ duration: 0.18 }}
              className="flex items-center gap-2.5 rounded-lg bg-spine px-4 py-2.5 text-[15px] text-on-spine shadow-float"
            >
              {toast.tone === "ok" ? <CheckCircle2 size={18} /> : <CircleAlert size={18} />}
              {toast.message}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </Context.Provider>
  );
}

export function useToast(): Notify {
  const notify = useContext(Context);
  if (!notify) throw new Error("useToast must be used inside ToastProvider");
  return notify;
}
