import type { ReactNode } from "react";
import { useState } from "react";
import { downloadArtifact } from "../xbarRExport";

type ReportPdfDownloadProps = {
  href: string;
  filename: string;
  children: ReactNode;
  onError: (message: string) => void;
};

function errorMessage(response: Response, body: string) {
  let code: string | undefined;
  let message: string | undefined;
  try {
    const payload = JSON.parse(body) as { error?: { code?: string; message?: string } };
    code = payload.error?.code;
    message = payload.error?.message;
  } catch {
    // A non-JSON error response still receives a safe, actionable explanation below.
  }
  if (code === "pdf_renderer_unavailable" || code === "pdf_render_failed") {
    return "PDF 생성기를 사용할 수 없습니다. HTML 보고서를 내려받은 뒤 브라우저의 인쇄 기능에서 PDF로 저장하세요.";
  }
  return message ?? `PDF 보고서를 내려받지 못했습니다. (HTTP ${response.status})`;
}

export function ReportPdfDownload({ href, filename, children, onError }: ReportPdfDownloadProps) {
  const [downloading, setDownloading] = useState(false);

  async function download() {
    setDownloading(true);
    onError("");
    try {
      const response = await fetch(href);
      if (!response.ok) {
        throw new Error(errorMessage(response, await response.text()));
      }
      downloadArtifact(filename, await response.blob(), "application/pdf");
    } catch (error) {
      onError(error instanceof Error ? error.message : "PDF 보고서를 내려받지 못했습니다.");
    } finally {
      setDownloading(false);
    }
  }

  return <button type="button" className="button button-secondary" onClick={download} disabled={downloading}>{downloading ? "PDF 생성 중…" : children}</button>;
}
