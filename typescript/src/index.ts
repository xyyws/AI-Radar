/**
 * AI Radar 主入口
 *
 * 支持两种运行模式：
 * 1. OpenClaw Skill 模式：作为 OpenClaw 技能被 ClawBot 调用
 * 2. CLI 模式：命令行直接执行
 */

import { Orchestrator } from "./orchestrator";
import { SKILL_METADATA } from "./delivery/openclaw-skill";

// 导出供 OpenClaw 集成使用
export { Orchestrator } from "./orchestrator";
export { AIRadarAgent } from "./agent";
export { handleClawBotMessage, SKILL_METADATA } from "./delivery/openclaw-skill";
export { formatReport, formatSummary } from "./delivery/formatter";

// 导出类型
export type {
  RawIntelligence,
  Source,
  Language,
} from "./types/raw-intelligence";
export type {
  DailyAIRadarReport,
  RadarEvent,
} from "./types/daily-report";

console.log(`AI Radar v${SKILL_METADATA.version}`);
console.log(`Skill: ${SKILL_METADATA.name}`);
console.log(`Triggers: ${SKILL_METADATA.triggers.join(", ")}`);
