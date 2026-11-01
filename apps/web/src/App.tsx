import { lazy, Suspense, type ComponentType } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { CustomerScreen } from "./screens/CustomerScreen";
import { DecisionsScreen } from "./screens/decisions/DecisionsScreen";
import { AppShell } from "./shell/AppShell";

const named = <K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) =>
  lazy(() => load().then((module) => ({ default: module[name] })));

const EstateScreen = named(() => import("./screens/EstateScreen"), "EstateScreen");
const CodeScreen = named(() => import("./screens/CodeScreen"), "CodeScreen");
const ReportsScreen = named(() => import("./screens/ReportsScreen"), "ReportsScreen");
const WorkflowsScreen = named(() => import("./screens/WorkflowsScreen"), "WorkflowsScreen");
const ReconcileScreen = named(() => import("./screens/ReconcileScreen"), "ReconcileScreen");
const SignoffScreen = named(() => import("./screens/SignoffScreen"), "SignoffScreen");
const ScorecardScreen = named(() => import("./screens/ScorecardScreen"), "ScorecardScreen");
const PresenterScreen = named(() => import("./screens/PresenterScreen"), "PresenterScreen");

export function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/presenter" element={<PresenterScreen />} />
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
    </Suspense>
  );
}
