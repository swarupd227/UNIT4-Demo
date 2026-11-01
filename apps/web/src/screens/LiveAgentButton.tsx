import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play } from "lucide-react";
import { useEffect, useState } from "react";
import { usePersona } from "../lib/persona";
import { useToast } from "../lib/toast";
import { workbench } from "../lib/workbench";
import { Button } from "../ui/primitives";

// Runs one agent against the model. A failed run leaves the cached result on screen.
export function LiveAgentButton({ agent, subject }: { agent: string; subject: string }) {
  const { role } = usePersona();
  const toast = useToast();
  const client = useQueryClient();
  const { data: status } = useQuery({ queryKey: ["agent-status"], queryFn: () => workbench.agentStatus(role) });
  const [seconds, setSeconds] = useState(0);
  const run = useMutation({
    mutationFn: () => workbench.runAgent(agent, subject, role),
    onSuccess: (result) => {
      client.invalidateQueries();
      toast(`Analysis finished in ${(result.duration_ms / 1000).toFixed(0)} sec`);
    },
    onError: (error: Error) => toast(error.message, "bad"),
  });

  useEffect(() => {
    if (!run.isPending) return;
    setSeconds(0);
    const timer = window.setInterval(() => setSeconds((count) => count + 1), 1000);
    return () => window.clearInterval(timer);
  }, [run.isPending]);

  if (!status?.live || role !== "consultant") return null;
  return (
    <Button disabled={run.isPending} onClick={() => run.mutate()}>
      <Play size={15} aria-hidden />
      {run.isPending ? `Analysing… ${seconds} sec` : "Run live"}
    </Button>
  );
}
