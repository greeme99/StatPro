import { line } from "d3-shape";
import { useId } from "react";
import type { FishboneSnapshot } from "../types";

const path = line<[number, number]>().x((point) => point[0]).y((point) => point[1]);

export function FishboneDiagram({ diagram }: { diagram: FishboneSnapshot }) {
  const descriptionId = useId();
  const startX = 90;
  const endX = 860;
  const centerY = 260;
  const spacing = (endX - startX) / (diagram.categories.length + 1);

  return (
    <figure className="fishbone-figure">
      <svg viewBox="0 0 1000 520" role="img" aria-label={diagram.title} aria-describedby={descriptionId}>
        <title>{diagram.title}</title>
        <desc id={descriptionId}>{diagram.problem_statement}의 원인 후보를 범주별로 정리한 특성요인도</desc>
        <path className="fishbone-spine" d={path([[startX, centerY], [endX, centerY]]) ?? undefined} />
        <path className="fishbone-arrow" d={path([[endX - 24, centerY - 14], [endX, centerY], [endX - 24, centerY + 14]]) ?? undefined} />
        <g className="fishbone-effect">
          <rect x="870" y="210" width="118" height="100" rx="12" />
          <text x="929" y="240" textAnchor="middle">문제</text>
          <foreignObject x="880" y="250" width="98" height="52">
            <div className="fishbone-effect-text">{diagram.problem_statement}</div>
          </foreignObject>
        </g>
        {diagram.categories.map((category, index) => {
          const anchorX = startX + spacing * (index + 1);
          const above = index % 2 === 0;
          const outerY = above ? 86 : 434;
          const labelY = above ? 62 : 462;
          const bonePath = path([[anchorX, centerY], [anchorX - 94, outerY]]);
          return (
            <g key={category.category_id}>
              <path className="fishbone-bone" d={bonePath ?? undefined} />
              <text className="fishbone-category" x={anchorX - 94} y={labelY} textAnchor="middle">{category.name}</text>
              {category.causes.slice(0, 5).map((cause, causeIndex) => {
                const ratio = (causeIndex + 1) / 6;
                const x = anchorX - 94 * ratio;
                const y = centerY + (outerY - centerY) * ratio;
                const branchEndX = x + (above ? -78 : 78);
                return (
                  <g key={cause.cause_id} className={cause.selected_for_verification ? "is-selected" : undefined}>
                    <path className="fishbone-cause-line" d={path([[x, y], [branchEndX, y]]) ?? undefined} />
                    <text className="fishbone-cause" x={branchEndX} y={y - 7} textAnchor={above ? "end" : "start"}>{cause.text}</text>
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
      <figcaption>선택 표시된 원인은 검증 대상으로 지정된 가설이며, 입증된 근본원인을 의미하지 않습니다.</figcaption>
      <div className="table-wrap fishbone-accessible-table">
        <table>
          <thead><tr><th>범주</th><th>원인 후보</th><th>검증</th><th>증거 참조</th></tr></thead>
          <tbody>{diagram.categories.flatMap((category) => category.causes.length > 0
            ? category.causes.map((cause) => <tr key={cause.cause_id}><td>{category.name}</td><td>{cause.text}</td><td>{cause.selected_for_verification ? "대상" : "미선정"}</td><td>{cause.evidence_refs.join(", ") || "없음"}</td></tr>)
            : [<tr key={`${category.category_id}-empty`}><td>{category.name}</td><td>등록된 원인 없음</td><td>—</td><td>—</td></tr>])}</tbody>
        </table>
      </div>
    </figure>
  );
}
