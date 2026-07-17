/**
 * Markdown 排版 — 适配微信 ClawBot 渲染
 */

import type { DailyAIRadarReport, RadarEvent } from "../types/daily-report";

/**
 * 将 DailyAIRadarReport 格式化为微信友好的 Markdown
 */
export function formatReport(report: DailyAIRadarReport): string {
  const lines: string[] = [];

  // 标题
  lines.push(`# AI Radar 每日情报`);
  lines.push(`> ${report.date}\n`);

  // 总览
  lines.push(`## 概览\n`);
  lines.push(report.summary);
  lines.push("");

  // 核心事件
  for (let i = 0; i < report.events.length; i++) {
    const event = report.events[i];
    lines.push(`---\n`);
    lines.push(formatEvent(event, i + 1));
    lines.push("");
  }

  // 关键词
  lines.push(`---\n`);
  lines.push(`## 关键词\n`);
  lines.push(report.keywords.map((kw) => `\`${kw}\``).join("  "));
  lines.push("");

  // 尾部
  lines.push(`---`);
  lines.push(`> AI Radar — 每日 AI 情报自动提炼`);

  return lines.join("\n");
}

function formatEvent(event: RadarEvent, index: number): string {
  const lines: string[] = [];

  lines.push(`### ${index}. ${event.title}\n`);
  lines.push(`**是什么**：${event.what}\n`);
  lines.push(`**为什么重要**：${event.whyImportant}\n`);
  lines.push(`**哪些公司开始用了**：${event.adoption}\n`);
  lines.push(`**未来趋势**：${event.trend}\n`);

  if (event.tags.length > 0) {
    lines.push(`标签：${event.tags.map((t) => `\`${t}\``).join(" ")}`);
  }

  return lines.join("\n");
}

/**
 * 生成简短摘要（用于微信消息预览）
 */
export function formatSummary(report: DailyAIRadarReport): string {
  const eventTitles = report.events.map((e, i) => `${i + 1}. ${e.title}`).join("\n");
  return `AI Radar ${report.date}\n\n${eventTitles}\n\n共 ${report.events.length} 条核心情报，${report.keywords.length} 个关键词`;
}
