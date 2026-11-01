import { LineChart } from "echarts/charts";
import { AriaComponent, GridComponent, MarkLineComponent } from "echarts/components";
import { init, use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";

use([LineChart, AriaComponent, GridComponent, MarkLineComponent, SVGRenderer]);
const points = Array.from({ length: 1_000 }, (_, index) => [
  index + 1,
  10 + Math.sin(index / 21) * 0.2,
]);
const chart = init(document.getElementById("root"), undefined, { renderer: "svg" });
chart.setOption({
  animation: false,
  aria: { enabled: true, description: "관리도 벤치마크" },
  xAxis: { type: "value" },
  yAxis: { type: "value" },
  series: [{
    type: "line",
    data: points,
    showSymbol: false,
    markLine: {
      silent: true,
      symbol: "none",
      data: [{ yAxis: 10.6 }, { yAxis: 10 }, { yAxis: 9.4 }],
    },
  }],
});
