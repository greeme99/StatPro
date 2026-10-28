import { Download, FileJson, FileSpreadsheet, FileText, ImageDown, ImageUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ResultBundle } from "../types";
import { Button } from "./Button";

function downloadJson(filename: string, result: ResultBundle) {
  const blob = new Blob([`${JSON.stringify(result, null, 2)}\n`], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ResultExportMenu({ runId, result }: { runId: string; result: ResultBundle }) {
  const [open, setOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocumentPointerDown = (event: PointerEvent) => {
      if (!menu.current?.contains(event.target as Node)) setOpen(false);
    };
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onDocumentPointerDown);
    document.addEventListener("keydown", onEscape);
    return () => {
      document.removeEventListener("pointerdown", onDocumentPointerDown);
      document.removeEventListener("keydown", onEscape);
    };
  }, [open]);

  return (
    <div className="result-export-menu" ref={menu}>
      <Button variant="primary" icon={<Download />} aria-expanded={open} aria-haspopup="menu" onClick={() => setOpen((value) => !value)}>결과 출력</Button>
      {open && <div className="export-popover" role="menu" aria-label="결과 출력 형식">
        <button role="menuitem" onClick={() => { downloadJson(`${runId}-result.json`, result); setOpen(false); }}><FileJson aria-hidden="true" />JSON으로 저장</button>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><FileText aria-hidden="true" />PDF 보고서 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><FileSpreadsheet aria-hidden="true" />Excel로 저장 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageDown aria-hidden="true" />차트를 PNG로 저장 <small>개발 예정</small></span>
        <span role="menuitem" aria-disabled="true" title="개발 예정"><ImageUp aria-hidden="true" />차트를 SVG로 저장 <small>개발 예정</small></span>
      </div>}
    </div>
  );
}
