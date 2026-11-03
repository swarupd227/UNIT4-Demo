import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import "./index.css";
import { PersonaProvider } from "./lib/persona";
import { ToastProvider } from "./lib/toast";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 5000, retry: 3, retryDelay: 800, refetchOnWindowFocus: false } },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PersonaProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </PersonaProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
