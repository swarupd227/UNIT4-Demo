import { Navigate, Route, Routes } from "react-router-dom";
import { AreaScreen } from "./screens/AreaScreen";
import { ContextScreen } from "./screens/ContextScreen";
import { CoverageScreen } from "./screens/CoverageScreen";
import { FlakyScreen } from "./screens/FlakyScreen";
import { GapsScreen } from "./screens/GapsScreen";
import { GeneratedTestsScreen } from "./screens/GeneratedTestsScreen";
import { ProofScreen } from "./screens/ProofScreen";
import { ReviewScreen } from "./screens/ReviewScreen";
import { ScorecardScreen } from "./screens/ScorecardScreen";
import { AppShell } from "./shell/AppShell";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/area" element={<AreaScreen />} />
        <Route path="/coverage" element={<CoverageScreen />} />
        <Route path="/context" element={<ContextScreen />} />
        <Route path="/tests" element={<GeneratedTestsScreen />} />
        <Route path="/proof" element={<ProofScreen />} />
        <Route path="/flaky" element={<FlakyScreen />} />
        <Route path="/review" element={<ReviewScreen />} />
        <Route path="/gaps" element={<GapsScreen />} />
        <Route path="/scorecard" element={<ScorecardScreen />} />
        <Route path="*" element={<Navigate to="/area" replace />} />
      </Route>
    </Routes>
  );
}
