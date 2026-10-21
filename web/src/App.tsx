import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ImrSetupPage } from "./pages/ImrSetupPage";
import { ResultPage } from "./pages/ResultPage";
import { FmeaListPage } from "./pages/FmeaListPage";
import { FmeaStudyPage } from "./pages/FmeaStudyPage";
import { DataPage } from "./pages/DataPage";
import { WorksheetPage } from "./pages/WorksheetPage";
import { DoeSetupPage } from "./pages/DoeSetupPage";
import { DoeOptimizerPage } from "./pages/DoeOptimizerPage";
import { DoeFractionalSetupPage } from "./pages/DoeFractionalSetupPage";
import { DoePlackettBurmanSetupPage } from "./pages/DoePlackettBurmanSetupPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analyses/imr/new" element={<ImrSetupPage />} />
        <Route path="/analyses/doe/full-factorial" element={<DoeSetupPage />} />
        <Route path="/analyses/doe/fractional-factorial" element={<DoeFractionalSetupPage />} />
        <Route path="/analyses/doe/plackett-burman" element={<DoePlackettBurmanSetupPage />} />
        <Route path="/analyses/doe/response-optimizer" element={<DoeOptimizerPage />} />
        <Route path="/runs/:runId" element={<ResultPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/data/:worksheetId" element={<WorksheetPage />} />
        <Route path="/fmea" element={<FmeaListPage />} />
        <Route path="/fmea/:studyId" element={<FmeaStudyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
