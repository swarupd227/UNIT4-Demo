import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const CHANNEL = "assurance-presenter";

export type PresenterMessage =
  | { type: "go"; path: string }
  | { type: "fallback"; scene: number | null }
  | { type: "reset" }
  | { type: "at"; pathname: string };

// The console window talks to the audience window on the same machine, with no server involved.
export function usePresenterChannel(onMessage: (message: PresenterMessage) => void) {
  const handler = useRef(onMessage);
  const channel = useRef<BroadcastChannel | null>(null);
  useEffect(() => {
    handler.current = onMessage;
  });
  useEffect(() => {
    const opened = typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel(CHANNEL);
    channel.current = opened;
    if (opened) opened.onmessage = (event) => handler.current(event.data);
    return () => opened?.close();
  }, []);
  return useCallback((message: PresenterMessage) => channel.current?.postMessage(message), []);
}

// Runs in the audience window.
export function useAudienceLink() {
  const navigate = useNavigate();
  const location = useLocation();
  const client = useQueryClient();
  const [fallback, setFallback] = useState<number | null>(null);

  const send = usePresenterChannel((message) => {
    if (message.type === "go") {
      setFallback(null);
      navigate(message.path);
    } else if (message.type === "fallback") {
      setFallback(message.scene);
    } else if (message.type === "reset") {
      setFallback(null);
      void client.invalidateQueries();
      navigate("/area");
    }
  });

  useEffect(() => send({ type: "at", pathname: location.pathname }), [location.pathname, send]);

  return { fallback, closeFallback: () => setFallback(null) };
}
