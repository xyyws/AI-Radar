/**
 * RawIntelligence 类型定义
 * 与 shared/schema/raw-intelligence.json 对齐
 */

import { z } from "zod";

// --- Zod Schema ---

export const SourceEnum = z.enum([
  "github",
  "arxiv",
  "openai",
  "anthropic",
  "deepmind",
  "meta",
  "huggingface",
  "twitter",
  "reddit",
  "wechat",
  "zhihu",
]);

export const LanguageEnum = z.enum(["en", "zh"]);

export const RawIntelligenceSchema = z.object({
  source: SourceEnum,
  title: z.string().min(1).max(500),
  url: z.string().url(),
  rawContent: z.string().min(1).max(10000),
  publishedAt: z.string().datetime({ offset: true }),
  language: LanguageEnum,
  metadata: z.record(z.unknown()).default({}),
  evidence: z.array(z.string()).default([]),
});

// --- TypeScript Type (derived from Zod) ---

export type Source = z.infer<typeof SourceEnum>;
export type Language = z.infer<typeof LanguageEnum>;
export type RawIntelligence = z.infer<typeof RawIntelligenceSchema>;
