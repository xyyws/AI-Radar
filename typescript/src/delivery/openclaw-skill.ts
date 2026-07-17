/**
 * OpenClaw Skill — 将 AI Radar 注册为 OpenClaw 技能
 *
 * 通过 OpenClaw + ClawBot 桥接微信消息到 Agent
 *
 * 安装流程：
 * 1. npx -y @tencent-weixin/openclaw-weixin-cli@latest install
 * 2. openclaw agents add ai-radar
 * 3. openclaw channels login --channel openclaw-weixin
 */

import type { DailyAIRadarReport } from "../types/daily-report";
import { formatReport, formatSummary } from "./formatter";

/**
 * OpenClaw Skill 接口定义
 * 当用户在微信中发送消息时，OpenClaw 会调用此函数
 */
export interface OpenClawSkillContext {
  /** 用户发送的原始消息 */
  userMessage: string;
  /** 用户微信 ID */
  userId: string;
  /** 当前日期 */
  date: string;
}

export interface OpenClawSkillResponse {
  /** 回复给用户的消息 */
  reply: string;
  /** 是否为错误消息 */
  isError?: boolean;
}

/**
 * 处理用户微信消息
 * 识别触发关键词，执行 Agent 提炼，返回格式化报告
 */
export async function handleClawBotMessage(
  ctx: OpenClawSkillContext,
  generateReport: () => Promise<DailyAIRadarReport>,
): Promise<OpenClawSkillResponse> {
  const msg = ctx.userMessage.trim();

  // 检测触发关键词
  const triggers = [
    "今日报告", "今日情报", "今日雷达",
    "AI雷达", "ai雷达", "AI Radar",
    "每日报告", "每日情报",
    "生成报告", "生成情报",
    "今日AI", "今天AI",
  ];

  const isTriggered = triggers.some((t) => msg.includes(t));

  if (!isTriggered) {
    return {
      reply: [
        "你好！我是 AI Radar 情报助手。",
        "",
        "发送以下关键词即可获取今日 AI 情报：",
        "• 今日报告",
        "• 今日情报",
        "• AI雷达",
        "",
        "我会从 GitHub、Arxiv、各大厂动态等 11 个数据源为你提炼每日 AI 圈核心情报。",
      ].join("\n"),
    };
  }

  try {
    const report = await generateReport();
    return { reply: formatReport(report) };
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : String(error);
    return {
      reply: `报告生成失败：${errMsg}\n\n请稍后重试，或检查数据源是否已采集。`,
      isError: true,
    };
  }
}

/**
 * 注册 OpenClaw Skill 元数据
 */
export const SKILL_METADATA = {
  name: "get_today_radar",
  description: "生成今日 AI 情报报告，从 11 个数据源提炼 AI 圈核心动态",
  triggers: ["今日报告", "今日情报", "AI雷达", "AI Radar", "每日报告"],
  version: "0.1.0",
};
