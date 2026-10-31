import { Navigate, Route, Routes } from "react-router-dom";
import { CodeScreen } from "./screens/CodeScreen";
import { CustomerScreen } from "./screens/CustomerScreen";
import { DecisionsScreen } from "./screens/decisions/DecisionsScreen";
import { EstateScreen } from "./screens/EstateScreen";
import { ReconcileScreen } from "./screens/ReconcileScreen";
import { ReportsScreen } from "./screens/ReportsScreen";
import { ScorecardScreen } from "./screens/ScorecardScreen";
import { SignoffScreen } from "./screens/SignoffScreen";
import { WorkflowsScreen } from "./screens/WorkflowsScreen";
import { AppShell } from "./shell/AppShell";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/customer" element={<CustomerScreen />} />
        <Route path="/estate" element={<EstateScreen />} />
        <Route path="/decisions/:itemId?" element={<DecisionsScreen />} />
        <Route path="/code/:itemId?" element={<CodeScreen />} />
        <Route path="/reports" element={<ReportsScreen />} />
        <Route path="/workflows" element={<WorkflowsScreen />} />
        <Route path="/reconcile" element={<ReconcileScreen />} />
        <Route path="/signoff" element={<SignoffScreen />} />
        <Route path="/scorecard" element={<ScorecardScreen />} />
        <Route path="*" element={<Navigate to="/customer" replace />} />
      </Route>
    </Routes>
  );
}
