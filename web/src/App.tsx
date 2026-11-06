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
import { XbarRSetupPage } from "./pages/XbarRSetupPage";
import { EwmaSetupPage } from "./pages/EwmaSetupPage";
import { CusumSetupPage } from "./pages/CusumSetupPage";
import { FeatureCatalogPage } from "./pages/FeatureCatalogPage";
import { DoeWorkspacePage } from "./pages/DoeWorkspacePage";
import { RareEventChartSetupPage } from "./pages/RareEventChartSetupPage";
import { MenuPreviewPage } from "./pages/MenuPreviewPage";
import { DmaicGuidePreviewPage } from "./pages/DmaicGuidePreviewPage";
import { DmaicDefineWorkspacePage } from "./pages/DmaicDefineWorkspacePage";
import { DmaicVoiceOfCustomerWorkspacePage } from "./pages/DmaicVoiceOfCustomerWorkspacePage";
import { DmaicSipocWorkspacePage } from "./pages/DmaicSipocWorkspacePage";
import { DmaicStakeholderWorkspacePage } from "./pages/DmaicStakeholderWorkspacePage";
import { DmaicProblemDefinitionWorkspacePage } from "./pages/DmaicProblemDefinitionWorkspacePage";
import { DmaicMeasureWorkspacePage } from "./pages/DmaicMeasureWorkspacePage";
import { DmaicRootCauseWorkspacePage } from "./pages/DmaicRootCauseWorkspacePage";
import { DmaicSolutionSelectionWorkspacePage } from "./pages/DmaicSolutionSelectionWorkspacePage";
import { DmaicPilotPlanWorkspacePage } from "./pages/DmaicPilotPlanWorkspacePage";
import { DmaicControlWorkspacePage } from "./pages/DmaicControlWorkspacePage";
import { LearningResourcesPreviewPage } from "./pages/LearningResourcesPreviewPage";
import { SpcWorkspacePage } from "./pages/SpcWorkspacePage";
import { ControlChartWorkspacePage } from "./pages/ControlChartWorkspacePage";
import { SpcQualityToolPage } from "./pages/SpcQualityToolPage";
import { CheckSheetWorkspacePage } from "./pages/CheckSheetWorkspacePage";
import { ParetoWorkspacePage } from "./pages/ParetoWorkspacePage";
import { FishboneWorkspacePage } from "./pages/FishboneWorkspacePage";
import { QualityDashboardPage } from "./pages/QualityDashboardPage";
import { DefectAnalysisPage } from "./pages/DefectAnalysisPage";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/analyses/imr/new" element={<ImrSetupPage />} />
        <Route path="/analyses/spc/attribute" element={<AttributeChartSetupPage />} />
        <Route path="/analyses/spc/xbar-s" element={<XbarSSetupPage />} />
        <Route path="/analyses/spc/xbar-r" element={<XbarRSetupPage />} />
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
        <Route path="/spc" element={<SpcWorkspacePage />} />
        <Route path="/spc/control-charts" element={<ControlChartWorkspacePage />} />
        <Route path="/spc/tools/check-sheet" element={<CheckSheetWorkspacePage />} />
        <Route path="/spc/tools/pareto-chart" element={<ParetoWorkspacePage />} />
        <Route path="/spc/tools/fishbone" element={<FishboneWorkspacePage />} />
        <Route path="/spc/tools/:toolId" element={<SpcQualityToolPage />} />
        <Route path="/runs/:runId" element={<ResultPage />} />
        <Route path="/data" element={<DataPage />} />
        <Route path="/data/:worksheetId" element={<WorksheetPage />} />
        <Route path="/fmea" element={<FmeaListPage />} />
        <Route path="/fmea/:studyId" element={<FmeaStudyPage />} />
        <Route path="/quality" element={<QualityDashboardPage />} />
        <Route path="/defects" element={<DefectAnalysisPage />} />
        <Route path="/home" element={<MenuPreviewPage />} />
        <Route path="/home/dmaic" element={<DmaicGuidePreviewPage />} />
        <Route path="/home/dmaic/define" element={<DmaicDefineWorkspacePage />} />
        <Route path="/home/dmaic/voc" element={<DmaicVoiceOfCustomerWorkspacePage />} />
        <Route path="/home/dmaic/sipoc" element={<DmaicSipocWorkspacePage />} />
        <Route path="/home/dmaic/stakeholders" element={<DmaicStakeholderWorkspacePage />} />
        <Route path="/home/dmaic/problem-definition" element={<DmaicProblemDefinitionWorkspacePage />} />
        <Route path="/home/dmaic/measure" element={<DmaicMeasureWorkspacePage />} />
        <Route path="/home/dmaic/analyze/root-causes" element={<DmaicRootCauseWorkspacePage />} />
        <Route path="/home/dmaic/improve/solution-selection" element={<DmaicSolutionSelectionWorkspacePage />} />
        <Route path="/home/dmaic/improve/pilot-plan" element={<DmaicPilotPlanWorkspacePage />} />
        <Route path="/home/dmaic/control" element={<DmaicControlWorkspacePage />} />
        <Route path="/home/learning" element={<LearningResourcesPreviewPage />} />
        <Route path="/ui-preview" element={<Navigate to="/home" replace />} />
        <Route path="/ui-preview/dmaic" element={<Navigate to="/home/dmaic" replace />} />
        <Route path="/ui-preview/learning" element={<Navigate to="/home/learning" replace />} />
        <Route path="/catalog/:section" element={<FeatureCatalogPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}
