import { Navigate, Route, Routes } from "react-router-dom";
import { DecisionsScreen } from "./screens/decisions/DecisionsScreen";
import { AppShell } from "./shell/AppShell";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/decisions/:itemId?" element={<DecisionsScreen />} />
        <Route path="*" element={<Navigate to="/decisions" replace />} />
      </Route>
    </Routes>
  );
}
