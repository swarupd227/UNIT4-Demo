import { Navigate, Route, Routes } from "react-router-dom";
import { AreaScreen } from "./screens/AreaScreen";
import { ContextScreen } from "./screens/ContextScreen";
import { CoverageScreen } from "./screens/CoverageScreen";
import { GeneratedTestsScreen } from "./screens/GeneratedTestsScreen";
import { PendingScreen } from "./screens/PendingScreen";
import { ProofScreen } from "./screens/ProofScreen";
import { STAGES } from "./lib/terms";
import { AppShell } from "./shell/AppShell";

const BUILT = new Set(["area", "coverage", "context", "tests", "proof"]);

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/area" element={<AreaScreen />} />
        <Route path="/coverage" element={<CoverageScreen />} />
        <Route path="/context" element={<ContextScreen />} />
        <Route path="/tests" element={<GeneratedTestsScreen />} />
        <Route path="/proof" element={<ProofScreen />} />
        {STAGES.filter((stage) => !BUILT.has(stage.key)).map((stage) => (
          <Route key={stage.key} path={`/${stage.key}`} element={<PendingScreen title={stage.label} />} />
        ))}
        <Route path="*" element={<Navigate to="/area" replace />} />
      </Route>
    </Routes>
  );
}
