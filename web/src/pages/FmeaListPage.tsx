import { AlertTriangle, ArrowRight, FilePlus2, FileWarning } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createFmeaStudy, listFmeaStudies } from "../api";
import { Button } from "../components/Button";
import type { StoredFmeaStudy } from "../types";

const statusLabels = {
  draft: "작성 중",
  in_review: "검토 중",
  approved: "승인됨",
  archived: "보관됨",
};

export function FmeaListPage() {
  const navigate = useNavigate();
  const idRef = useRef<HTMLInputElement>(null);
  const [studies, setStudies] = useState<StoredFmeaStudy[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    listFmeaStudies()
      .then((page) => { if (active) { setStudies(page.items); setState("ready"); } })
      .catch(() => { if (active) setState("error"); });
    return () => { active = false; };
  }, []);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const studyId = String(form.get("study_id") ?? "").trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(studyId)) {
      setError("Study ID는 영문자나 숫자로 시작하고 영문자, 숫자, 점, 밑줄, 하이픈만 사용할 수 있습니다.");
      idRef.current?.focus();
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const created = await createFmeaStudy({
        study_id: studyId,
        name: String(form.get("name") ?? "").trim(),
        study_type: form.get("study_type") === "design" ? "design" : "process",
        standard_version: String(form.get("standard_version") ?? "").trim(),
        actor: String(form.get("actor") ?? "").trim(),
        occurred_at: new Date().toISOString(),
      });
      navigate(`/fmea/${created.study_id}`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "FMEA Study를 만들지 못했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page fmea-page" data-density="compact">
      <section className="page-heading">
        <div><span className="eyebrow">RISK WORKBENCH</span><h1>FMEA Study</h1><p>고장 모드와 위험평가를 revision 단위로 기록하고 검토 상태를 관리합니다.</p></div>
      </section>

      {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{error}</p></div>}

      <section className="fmea-list-layout">
        <article className="panel">
          <header className="panel-heading"><div><span className="eyebrow">STUDIES</span><h2>등록된 Study</h2></div><span>{studies.length}개</span></header>
          {state === "loading" && <div className="state-message"><p>FMEA 목록을 불러오는 중입니다.</p></div>}
          {state === "error" && <div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h3>목록을 불러오지 못했습니다</h3><p>로컬 API 연결을 확인하세요.</p></div>}
          {state === "ready" && studies.length === 0 && <div className="state-message"><FileWarning aria-hidden="true" /><h3>아직 FMEA Study가 없습니다</h3><p>오른쪽 양식에서 첫 Study를 만드세요.</p></div>}
          {studies.length > 0 && <div className="table-scroll"><table><thead><tr><th>Study</th><th>Revision</th><th>유형</th><th>상태</th><th>고장 모드</th><th><span className="sr-only">열기</span></th></tr></thead><tbody>{studies.map(({ study }) => <tr key={study.study_id}><td><strong>{study.name}</strong><small className="table-subtitle">{study.study_id}</small></td><td>{study.revision}</td><td>{study.study_type === "process" ? "PFMEA" : "DFMEA"}</td><td><span className={`status-badge status-${study.status}`}>{statusLabels[study.status]}</span></td><td>{study.items.length}</td><td><Link className="text-link" to={`/fmea/${study.study_id}`}>열기 <ArrowRight aria-hidden="true" /></Link></td></tr>)}</tbody></table></div>}
        </article>

        <form className="panel compact-form" onSubmit={handleCreate}>
          <header className="panel-heading"><div><span className="eyebrow">NEW STUDY</span><h2>Study 만들기</h2></div><FilePlus2 aria-hidden="true" /></header>
          <div className="form-stack">
            <label className="field">Study ID<input ref={idRef} name="study_id" required defaultValue="PFMEA-001" /><small>저장 경로에 쓰이는 변경 불가 식별자</small></label>
            <label className="field">Study 이름<input name="name" required defaultValue="Connector Assembly" /></label>
            <label className="field">유형<select name="study_type" defaultValue="process"><option value="process">Process FMEA</option><option value="design">Design FMEA</option></select></label>
            <label className="field">적용 표준 버전<input name="standard_version" required defaultValue="customer-standard-2026" /><small>고객이 적법하게 제공한 표준의 버전을 기록합니다.</small></label>
            <label className="field">작성자<input name="actor" required defaultValue="quality.engineer" /></label>
            <Button type="submit" variant="primary" loading={submitting} icon={<FilePlus2 />}>Study 만들기</Button>
          </div>
        </form>
      </section>
    </div>
  );
}
