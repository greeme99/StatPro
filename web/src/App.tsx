import { lazy, Suspense, type ComponentType } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ControlChartWorkspacePage } from "./pages/ControlChartWorkspacePage";
import { DashboardPage } from "./pages/DashboardPage";
import { DmaicControlWorkspacePage } from "./pages/DmaicControlWorkspacePage";
import { DmaicProjectOverviewPage } from "./pages/DmaicProjectOverviewPage";
import { DmaicSipocWorkspacePage } from "./pages/DmaicSipocWorkspacePage";
import { DmaicVoiceOfCustomerWorkspacePage } from "./pages/DmaicVoiceOfCustomerWorkspacePage";

function lazyNamed(loader: () => Promise<Record<string, unknown>>, exportName: string) {
  return lazy(async () => ({ default: (await loader())[exportName] as ComponentType }));
}

const ImrSetupPage = lazyNamed(() => import("./pages/ImrSetupPage"), "ImrSetupPage");
const ResultPage = lazyNamed(() => import("./pages/ResultPage"), "ResultPage");
const FmeaListPage = lazyNamed(() => import("./pages/FmeaListPage"), "FmeaListPage");
const FmeaStudyPage = lazyNamed(() => import("./pages/FmeaStudyPage"), "FmeaStudyPage");
const DataPage = lazyNamed(() => import("./pages/DataPage"), "DataPage");
const WorksheetPage = lazyNamed(() => import("./pages/WorksheetPage"), "WorksheetPage");
const DoeSetupPage = lazyNamed(() => import("./pages/DoeSetupPage"), "DoeSetupPage");
const DoeOptimizerPage = lazyNamed(() => import("./pages/DoeOptimizerPage"), "DoeOptimizerPage");
const DoeFractionalSetupPage = lazyNamed(() => import("./pages/DoeFractionalSetupPage"), "DoeFractionalSetupPage");
const DoePlackettBurmanSetupPage = lazyNamed(() => import("./pages/DoePlackettBurmanSetupPage"), "DoePlackettBurmanSetupPage");
const DoeCentralCompositeSetupPage = lazyNamed(() => import("./pages/DoeCentralCompositeSetupPage"), "DoeCentralCompositeSetupPage");
const DoeBoxBehnkenSetupPage = lazyNamed(() => import("./pages/DoeBoxBehnkenSetupPage"), "DoeBoxBehnkenSetupPage");
const AttributeChartSetupPage = lazyNamed(() => import("./pages/AttributeChartSetupPage"), "AttributeChartSetupPage");
const XbarSSetupPage = lazyNamed(() => import("./pages/XbarSSetupPage"), "XbarSSetupPage");
const XbarRSetupPage = lazyNamed(() => import("./pages/XbarRSetupPage"), "XbarRSetupPage");
const EwmaSetupPage = lazyNamed(() => import("./pages/EwmaSetupPage"), "EwmaSetupPage");
const CusumSetupPage = lazyNamed(() => import("./pages/CusumSetupPage"), "CusumSetupPage");
const FeatureCatalogPage = lazyNamed(() => import("./pages/FeatureCatalogPage"), "FeatureCatalogPage");
const DoeWorkspacePage = lazyNamed(() => import("./pages/DoeWorkspacePage"), "DoeWorkspacePage");
const RareEventChartSetupPage = lazyNamed(() => import("./pages/RareEventChartSetupPage"), "RareEventChartSetupPage");
const MenuPreviewPage = lazyNamed(() => import("./pages/MenuPreviewPage"), "MenuPreviewPage");
const DmaicGuidePreviewPage = lazyNamed(() => import("./pages/DmaicGuidePreviewPage"), "DmaicGuidePreviewPage");
const DmaicDefineWorkspacePage = lazyNamed(() => import("./pages/DmaicDefineWorkspacePage"), "DmaicDefineWorkspacePage");
const DmaicStakeholderWorkspacePage = lazyNamed(() => import("./pages/DmaicStakeholderWorkspacePage"), "DmaicStakeholderWorkspacePage");
const DmaicProblemDefinitionWorkspacePage = lazyNamed(() => import("./pages/DmaicProblemDefinitionWorkspacePage"), "DmaicProblemDefinitionWorkspacePage");
const DmaicMeasureWorkspacePage = lazyNamed(() => import("./pages/DmaicMeasureWorkspacePage"), "DmaicMeasureWorkspacePage");
const DmaicRootCauseWorkspacePage = lazyNamed(() => import("./pages/DmaicRootCauseWorkspacePage"), "DmaicRootCauseWorkspacePage");
const DmaicSolutionSelectionWorkspacePage = lazyNamed(() => import("./pages/DmaicSolutionSelectionWorkspacePage"), "DmaicSolutionSelectionWorkspacePage");
const DmaicPilotPlanWorkspacePage = lazyNamed(() => import("./pages/DmaicPilotPlanWorkspacePage"), "DmaicPilotPlanWorkspacePage");
const LearningResourcesPreviewPage = lazyNamed(() => import("./pages/LearningResourcesPreviewPage"), "LearningResourcesPreviewPage");
const SpcWorkspacePage = lazyNamed(() => import("./pages/SpcWorkspacePage"), "SpcWorkspacePage");
const SpcQualityToolPage = lazyNamed(() => import("./pages/SpcQualityToolPage"), "SpcQualityToolPage");
const CheckSheetWorkspacePage = lazyNamed(() => import("./pages/CheckSheetWorkspacePage"), "CheckSheetWorkspacePage");
const ParetoWorkspacePage = lazyNamed(() => import("./pages/ParetoWorkspacePage"), "ParetoWorkspacePage");
const FishboneWorkspacePage = lazyNamed(() => import("./pages/FishboneWorkspacePage"), "FishboneWorkspacePage");
const QualityDashboardPage = lazyNamed(() => import("./pages/QualityDashboardPage"), "QualityDashboardPage");
const DefectAnalysisPage = lazyNamed(() => import("./pages/DefectAnalysisPage"), "DefectAnalysisPage");

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<div className="route-loading" role="status">화면을 불러오는 중입니다.</div>}>
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
        <Route path="/home/dmaic/project" element={<DmaicProjectOverviewPage />} />
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
      </Suspense>
    </AppShell>
  );
}
