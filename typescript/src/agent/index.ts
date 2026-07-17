/**
 * Agent 核心 — 调用 Gemini 提炼情报
 */

import { google } from "@ai-sdk/google";
import { generateText } from "ai";
import { readFileSync, existsSync } from "fs";
import { resolve } from "path";

import { loadConfig } from "../config";
import { RawIntelligence, RawIntelligenceSchema } from "../types/raw-intelligence";
import { DailyAIRadarReport } from "../types/daily-report";
import { SYSTEM_PROMPT, buildUserPrompt } from "./prompts";
import { parseWithRetry } from "./parser";

export class AIRadarAgent {
  private config: ReturnType<typeof loadConfig>;

  constructor() {
    this.config = loadConfig();
  }

  /**
   * 从文件加载原始情报
   */
  loadRawData(filePath?: string): RawIntelligence[] {
    const path = filePath || this.config.rawDataPath;
    if (!existsSync(path)) {
      throw new Error(`原始数据文件不存在: ${path}`);
    }

    const raw = JSON.parse(readFileSync(path, "utf-8"));
    const items = raw.items || [];

    // 校验每条数据
    return items.map((item: unknown, index: number) => {
      const result = RawIntelligenceSchema.safeParse(item);
      if (!result.success) {
        console.warn(`跳过第 ${index + 1} 条数据，格式不符:`, result.error.message);
        return null;
      }
      return result.data;
    }).filter((item: RawIntelligence | null): item is RawIntelligence => item !== null);
  }

  /**
   * 调用 Gemini 提炼情报
   */
  async refine(items: RawIntelligence[]): Promise<DailyAIRadarReport> {
    if (items.length === 0) {
      throw new Error("没有可提炼的情报数据");
    }

    // 截断过长的数据以节省 token
    const truncated = items.slice(0, 30).map((item) => ({
      source: item.source,
      title: item.title,
      url: item.url,
      rawContent: item.rawContent.slice(0, 500),
      publishedAt: item.publishedAt,
      language: item.language,
    }));

    const userPrompt = buildUserPrompt(JSON.stringify(truncated, null, 2));

    console.log(`调用 Gemini (${this.config.llmModel}) 提炼 ${truncated.length} 条情报...`);

    const { text } = await generateText({
      model: google(this.config.llmModel),
      system: SYSTEM_PROMPT,
      prompt: userPrompt,
      maxTokens: 8192,
    });

    return parseWithRetry(text);
  }

  /**
   * 完整的提炼流程：加载数据 → 调用 LLM → 校验输出
   */
  async run(filePath?: string): Promise<DailyAIRadarReport> {
    const items = this.loadRawData(filePath);
    console.log(`加载了 ${items.length} 条原始情报`);
    return this.refine(items);
  }
}
