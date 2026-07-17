/**
 * Agent 输出解析与 Zod 校验
 */

import { DailyAIRadarReport, DailyAIRadarReportSchema } from "../types/daily-report";

/**
 * 从 Agent 的原始输出中提取 JSON 字符串
 */
function extractJson(raw: string): string {
  // 尝试从 markdown code block 中提取
  const codeBlockMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (codeBlockMatch) {
    return codeBlockMatch[1].trim();
  }

  // 尝试提取第一个 { 到最后一个 } 之间的内容
  const firstBrace = raw.indexOf("{");
  const lastBrace = raw.lastIndexOf("}");
  if (firstBrace !== -1 && lastBrace > firstBrace) {
    return raw.slice(firstBrace, lastBrace + 1);
  }

  // 如果没有闭合的 }，可能是截断的 JSON
  if (firstBrace !== -1) {
    return raw.slice(firstBrace);
  }

  return raw;
}

/**
 * 尝试修复截断的 JSON
 */
function repairTruncatedJson(jsonStr: string): string {
  let repaired = jsonStr;

  // 移除末尾不完整的字符串值
  repaired = repaired.replace(/[^"]*$/, "");

  // 计算未闭合的括号
  let openBraces = 0;
  let openBrackets = 0;
  let inString = false;
  let escapeNext = false;

  for (const char of repaired) {
    if (escapeNext) {
      escapeNext = false;
      continue;
    }
    if (char === "\\") {
      escapeNext = true;
      continue;
    }
    if (char === '"') {
      inString = !inString;
      continue;
    }
    if (inString) continue;
    if (char === "{") openBraces++;
    if (char === "}") openBraces--;
    if (char === "[") openBrackets++;
    if (char === "]") openBrackets--;
  }

  // 如果在字符串中间截断，闭合字符串
  if (inString) {
    repaired += '"';
  }

  // 移除末尾的逗号
  repaired = repaired.replace(/,\s*$/, "");

  // 闭合所有未闭合的括号
  for (let i = 0; i < openBrackets; i++) {
    repaired += "]";
  }
  for (let i = 0; i < openBraces; i++) {
    repaired += "}";
  }

  return repaired;
}

/**
 * 从 Agent 的原始输出中提取并校验 JSON
 */
export function parseAgentOutput(raw: string): DailyAIRadarReport {
  const jsonStr = extractJson(raw);

  // 尝试直接解析
  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonStr);
  } catch {
    // 尝试修复截断的 JSON
    try {
      const repaired = repairTruncatedJson(jsonStr);
      parsed = JSON.parse(repaired);
    } catch {
      throw new Error(`Agent 输出的不是有效 JSON: ${jsonStr.slice(0, 200)}...`);
    }
  }

  // Zod 校验
  const result = DailyAIRadarReportSchema.safeParse(parsed);
  if (!result.success) {
    const errors = result.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("\n");
    throw new Error(`Agent 输出不符合 DailyAIRadarReport 格式:\n${errors}`);
  }

  return result.data;
}

/**
 * 尝试修复常见的 Agent 输出问题
 */
export function tryFixAgentOutput(raw: string): string {
  let fixed = raw;

  // 修复尾部逗号
  fixed = fixed.replace(/,\s*([\]}])/g, "$1");

  // 修复单引号
  fixed = fixed.replace(/'/g, '"');

  // 修复 NaN / undefined
  fixed = fixed.replace(/:\s*NaN/g, ": null");
  fixed = fixed.replace(/:\s*undefined/g, ": null");

  return fixed;
}

/**
 * 带重试的解析
 */
export function parseWithRetry(raw: string, maxRetries: number = 2): DailyAIRadarReport {
  try {
    return parseAgentOutput(raw);
  } catch (firstError) {
    if (maxRetries <= 0) throw firstError;

    try {
      const fixed = tryFixAgentOutput(raw);
      return parseAgentOutput(fixed);
    } catch {
      throw firstError;
    }
  }
}
