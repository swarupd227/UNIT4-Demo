import { Navigate, Route, Routes } from "react-router-dom";
import { AreaScreen } from "./screens/AreaScreen";
import { ContextScreen } from "./screens/ContextScreen";
import { CoverageScreen } from "./screens/CoverageScreen";
import { PendingScreen } from "./screens/PendingScreen";
import { STAGES } from "./lib/terms";
import { AppShell } from "./shell/AppShell";

const BUILT = new Set(["area", "coverage", "context"]);

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/area" element={<AreaScreen />} />
        <Route path="/coverage" element={<CoverageScreen />} />
        <Route path="/context" element={<ContextScreen />} />
        {STAGES.filter((stage) => !BUILT.has(stage.key)).map((stage) => (
          <Route key={stage.key} path={`/${stage.key}`} element={<PendingScreen title={stage.label} />} />
        ))}
        <Route path="*" element={<Navigate to="/area" replace />} />
      </Route>
    </Routes>
  );
}
