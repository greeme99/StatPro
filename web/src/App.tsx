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
import { DoeCentralCompositeSetupPage } from "./pages/DoeCentralCompositeSetupPage";
import { DoeBoxBehnkenSetupPage } from "./pages/DoeBoxBehnkenSetupPage";
import { AttributeChartSetupPage } from "./pages/AttributeChartSetupPage";
import { XbarSSetupPage } from "./pages/XbarSSetupPage";
import { EwmaSetupPage } from "./pages/EwmaSetupPage";
import { CusumSetupPage } from "./pages/CusumSetupPage";
import { FeatureCatalogPage } from "./pages/FeatureCatalogPage";
import { DoeWorkspacePage } from "./pages/DoeWorkspacePage";
import { RareEventChartSetupPage } from "./pages/RareEventChartSetupPage";
import { MenuPreviewPage } from "./pages/MenuPreviewPage";
import { DmaicGuidePreviewPage } from "./pages/DmaicGuidePreviewPage";
import { LearningResourcesPreviewPage } from "./pages/LearningResourcesPreviewPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analyses/imr/new" element={<ImrSetupPage />} />
        <Route path="/analyses/spc/attribute" element={<AttributeChartSetupPage />} />
        <Route path="/analyses/spc/xbar-s" element={<XbarSSetupPage />} />
        <Route path="/analyses/spc/ewma" element={<EwmaSetupPage />} />
        <Route path="/analyses/spc/cusum" element={<CusumSetupPage />} />
        <Route path="/analyses/spc/rare-events" element={<RareEventChartSetupPage />} />
        <Route path="/analyses/doe/full-factorial" element={<DoeSetupPage />} />
        <Route path="/analyses/doe/fractional-factorial" element={<DoeFractionalSetupPage />} />
        <Route path="/analyses/doe/plackett-burman" element={<DoePlackettBurmanSetupPage />} />
        <Route path="/analyses/doe/central-composite" element={<DoeCentralCompositeSetupPage />} />
        <Route path="/analyses/doe/box-behnken" element={<DoeBoxBehnkenSetupPage />} />
        <Route path="/analyses/doe/response-optimizer" element={<DoeOptimizerPage />} />
        <Route path="/doe" element={<DoeWorkspacePage />} />
        <Route path="/runs/:runId" element={<ResultPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/data/:worksheetId" element={<WorksheetPage />} />
        <Route path="/fmea" element={<FmeaListPage />} />
        <Route path="/fmea/:studyId" element={<FmeaStudyPage />} />
        <Route path="/ui-preview" element={<MenuPreviewPage />} />
        <Route path="/ui-preview/dmaic" element={<DmaicGuidePreviewPage />} />
        <Route path="/ui-preview/learning" element={<LearningResourcesPreviewPage />} />
        <Route path="/catalog/:section" element={<FeatureCatalogPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
