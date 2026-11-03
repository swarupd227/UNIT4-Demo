import { Navigate, Route, Routes } from "react-router-dom";
import { AreaScreen } from "./screens/AreaScreen";
import { PendingScreen } from "./screens/PendingScreen";
import { STAGES } from "./lib/terms";
import { AppShell } from "./shell/AppShell";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/area" element={<AreaScreen />} />
        {STAGES.filter((stage) => stage.key !== "area").map((stage) => (
          <Route key={stage.key} path={`/${stage.key}`} element={<PendingScreen title={stage.label} />} />
        ))}
        <Route path="*" element={<Navigate to="/area" replace />} />
      </Route>
    </Routes>
  );
}
