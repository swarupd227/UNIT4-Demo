import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { ROLE_KEYS, type Role } from "./terms";

const STORAGE_KEY = "studio.persona";

type PersonaContext = { role: Role; setRole: (role: Role) => void };

const Context = createContext<PersonaContext | null>(null);

function loadRole(): Role {
  try {
    const saved = localStorage.getItem(STORAGE_KEY) as Role | null;
    return saved && ROLE_KEYS.includes(saved) ? saved : "consultant";
  } catch {
    return "consultant";
  }
}

export function PersonaProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>(loadRole);
  const setRole = useCallback((next: Role) => {
    setRoleState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Remembering the persona is a convenience only.
    }
  }, []);
  const value = useMemo(() => ({ role, setRole }), [role, setRole]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function usePersona(): PersonaContext {
  const value = useContext(Context);
  if (!value) throw new Error("usePersona must be used inside PersonaProvider");
  return value;
}
