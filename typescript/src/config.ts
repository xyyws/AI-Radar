/**
 * AI Radar 配置管理
 */

import { config as dotenvConfig } from "dotenv";
import { resolve } from "path";

// 加载 .env
dotenvConfig({ path: resolve(__dirname, "../../.env") });

export interface Config {
  geminiApiKey: string;
  llmModel: string;
  dataDir: string;
  rawDataPath: string;
  reportsDir: string;
  openclawAgentId: string;
  // 推送配置
  pushEnabled: boolean;
  serverChanKey?: string;
}

export function loadConfig(): Config {
  const geminiApiKey = process.env.GOOGLE_GENERATIVE_AI_API_KEY;
  if (!geminiApiKey) {
    throw new Error("GOOGLE_GENERATIVE_AI_API_KEY 环境变量未设置");
  }

  const dataDir = resolve(__dirname, "../../data");

  return {
    geminiApiKey,
    llmModel: process.env.LLM_MODEL || "gemini-2.5-flash",
    dataDir,
    rawDataPath: resolve(dataDir, "raw/radar_data.json"),
    reportsDir: resolve(dataDir, "reports"),
    openclawAgentId: process.env.OPENCLAW_AGENT_ID || "ai-radar",
    // 推送配置
    pushEnabled: process.env.PUSH_ENABLED !== "false", // 默认开启
    serverChanKey: process.env.SERVER_CHAN_KEY || undefined,
  };
}
