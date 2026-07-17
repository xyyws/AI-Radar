/**
 * 独立报告生成脚本 — 用小米 mimo 模型
 */

import Anthropic from "@anthropic-ai/sdk";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "fs";
import { resolve } from "path";
import { config as dotenvConfig } from "dotenv";

dotenvConfig({ path: resolve(__dirname, "../../.env") });

const DATA_PATH = resolve(__dirname, "../../data/raw/radar_data.json");
const REPORTS_DIR = resolve(__dirname, "../../data/reports");

const SYSTEM_PROMPT = `你是顶级科技投资人兼 AI 技术专家。

重要：你有预采集的数据，不需要搜索。直接从数据中提炼情报。

写法自由，不要用固定模板。用你自己的判断和风格写。
每个事件的写法根据内容决定——有的先讲影响再讲细节，有的用反直觉的洞察开头，有的用数据说话。

但每个事件必须让读者明白：
1. 发生了什么（本质，不是表面）
2. 为什么这件事比表面看起来更重要
3. 接下来会怎样

排除：公关稿、营销内容、小版本更新、重复报道。

输出格式：
📡 AI Radar {日期}

{一句话定调}

{正文：3-5个事件，自由写作}

---
关键词：{词1} | {词2} | {词3}

总字数 500-800 字。所有内容用中文。`;

async function main() {
  if (!existsSync(DATA_PATH)) {
    console.error("数据文件不存在");
    process.exit(1);
  }

  const raw = JSON.parse(readFileSync(DATA_PATH, "utf-8"));
  if (!raw.items || raw.items.length === 0) {
    console.error("数据为空");
    process.exit(1);
  }

  const items = raw.items.slice(0, 30).map((item: any) => ({
    source: item.source,
    title: item.title,
    rawContent: (item.rawContent || "").slice(0, 500),
  }));

  const today = new Date().toISOString().split("T")[0];

  const userPrompt = `以下是今日预采集的 ${items.length} 条 AI 领域原始情报。请从中提炼 3-5 个最有价值的事件，写一篇情报简报。

数据：
${JSON.stringify(items, null, 2)}`;

  console.error(`调用 LLM 提炼 ${items.length} 条情报...`);

  // 使用小米模型 API（Anthropic 兼容格式）
  const client = new Anthropic({
    apiKey: process.env.MIMO_API_KEY || "tp-cpsc4hmutgjg8zl2zrz0ynyj8oa7e9mb2ezaa9joupqrwhqq",
    baseURL: "https://token-plan-cn.xiaomimimo.com/anthropic",
  });

  const response = await client.messages.create({
    model: "mimo-v2.5-pro",
    max_tokens: 4096,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userPrompt }],
  });

  const content = response.content[0];
  if (content.type !== "text") {
    console.error("LLM 返回了非文本内容");
    process.exit(1);
  }

  const text = content.text;

  // 输出到 stdout
  console.log(text);

  // 保存报告
  if (!existsSync(REPORTS_DIR)) {
    mkdirSync(REPORTS_DIR, { recursive: true });
  }
  writeFileSync(resolve(REPORTS_DIR, `${today}.txt`), text, "utf-8");
  console.error(`报告已保存`);
}

main().catch((err) => {
  console.error("报告生成失败:", err.message);
  process.exit(1);
});
