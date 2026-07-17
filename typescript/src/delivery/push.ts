/**
 * 推送抽象层 — 策略模式
 *
 * 支持多通道推送，单通道失败不影响其他通道。
 * 当前支持：Server酱
 * 未来可扩展：OpenClaw 主动推送、WxPusher、企业微信机器人等
 */

import type { DailyAIRadarReport } from "../types/daily-report";
import { formatReport, formatSummary } from "./formatter";
import { sendToServerChan } from "./server-chan";

// ---- 通道接口 ----

export interface PushChannel {
  /** 通道名称，用于日志 */
  name: string;
  /** 发送消息，成功返回 true */
  send(title: string, content: string): Promise<boolean>;
}

// ---- 推送配置 ----

export interface PushConfig {
  enabled: boolean;
  serverChanKey?: string;
}

// ---- 创建通道 ----

function createChannels(config: PushConfig): PushChannel[] {
  const channels: PushChannel[] = [];

  // Server酱
  if (config.serverChanKey) {
    channels.push({
      name: "Server酱",
      send: (title, content) =>
        sendToServerChan({ sendKey: config.serverChanKey! }, title, content),
    });
  }

  // 未来扩展点：
  // if (config.wxPusherToken) {
  //   channels.push({ name: "WxPusher", send: ... });
  // }

  return channels;
}

// ---- 推送报告 ----

/**
 * 将报告推送到所有已配置的通道
 *
 * - 标题：简短摘要（用于通知预览）
 * - 正文：完整 Markdown 报告
 * - 单通道失败不阻断其他通道
 */
export async function pushReport(
  report: DailyAIRadarReport,
  config: PushConfig,
): Promise<{ total: number; success: number; failed: number }> {
  if (!config.enabled) {
    console.log("[Push] 推送已禁用 (PUSH_ENABLED=false)");
    return { total: 0, success: 0, failed: 0 };
  }

  const channels = createChannels(config);

  if (channels.length === 0) {
    console.warn("[Push] 没有配置任何推送通道，请设置 SERVER_CHAN_KEY");
    return { total: 0, success: 0, failed: 0 };
  }

  const title = `AI Radar ${report.date} — ${report.events.length} 条核心情报`;
  const content = formatReport(report);

  console.log(`[Push] 开始推送到 ${channels.length} 个通道...`);

  let success = 0;
  let failed = 0;

  // 并行推送到所有通道
  const results = await Promise.allSettled(
    channels.map(async (channel) => {
      const ok = await channel.send(title, content);
      if (ok) {
        console.log(`[Push] ✓ ${channel.name} 推送成功`);
      } else {
        console.warn(`[Push] ✗ ${channel.name} 推送失败`);
      }
      return ok;
    }),
  );

  for (const result of results) {
    if (result.status === "fulfilled" && result.value) {
      success++;
    } else {
      failed++;
    }
  }

  console.log(`[Push] 推送完成: ${success} 成功, ${failed} 失败`);
  return { total: channels.length, success, failed };
}
