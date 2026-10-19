import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ImrSetupPage } from "./pages/ImrSetupPage";
import { ResultPage } from "./pages/ResultPage";
import { FmeaListPage } from "./pages/FmeaListPage";
import { FmeaStudyPage } from "./pages/FmeaStudyPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analyses/imr/new" element={<ImrSetupPage />} />
        <Route path="/runs/:runId" element={<ResultPage />} />
        <Route path="/fmea" element={<FmeaListPage />} />
        <Route path="/fmea/:studyId" element={<FmeaStudyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
