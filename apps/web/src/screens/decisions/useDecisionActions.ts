import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { api } from "../../lib/api";
import { usePersona } from "../../lib/persona";
import type { Outcome } from "../../lib/terms";
import { useToast } from "../../lib/toast";

export function useRefresh() {
  const client = useQueryClient();
  return () => client.invalidateQueries();
}

export function useDecisionActions(itemId: string | null) {
  const { role } = usePersona();
  const toast = useToast();
  const refresh = useRefresh();
  const id = itemId ?? "";

  const options = { onSettled: refresh, onError: (error: Error) => toast(error.message, "bad") };

  const accept = useMutation({
    ...options,
    mutationFn: () => api.accept(id, role),
    onSuccess: () => toast(`${id} accepted`),
  });
  const edit = useMutation({
    ...options,
    mutationFn: ({ outcome, reason }: { outcome: Outcome; reason: string }) => api.edit(id, role, outcome, reason),
    onSuccess: () => toast(`${id} changed. Your reason is on the audit trail.`),
  });
  const ask = useMutation({
    ...options,
    mutationFn: ({ question, options: choices }: { question: string; options: string[] }) =>
      api.ask(id, role, question, choices),
    onSuccess: () => toast(`Question sent to the customer`),
  });
  const answer = useMutation({
    ...options,
    mutationFn: (text: string) => api.answer(id, role, text),
    onSuccess: () => toast(`Answer recorded on ${id}`),
  });

  return useMemo(() => ({ accept, edit, ask, answer }), [accept, edit, ask, answer]);
}
