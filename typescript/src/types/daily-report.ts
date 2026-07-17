/**
 * DailyAIRadarReport 类型定义
 * 与 shared/schema/daily-report.json 对齐
 */

import { z } from "zod";

// --- Zod Schema ---

export const RadarEventSchema = z.object({
  title: z.string().min(1).max(200),
  what: z.string().min(10).max(1000),
  whyImportant: z.string().min(10).max(1000),
  adoption: z.string().min(5).max(1000),
  trend: z.string().min(10).max(1000),
  tags: z.array(z.string().min(1)).min(1).max(10),
});

export const DailyAIRadarReportSchema = z.object({
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  summary: z.string().min(100).max(5000),
  events: z.array(RadarEventSchema).min(1).max(10),
  keywords: z.array(z.string().min(1)).min(1).max(30),
});

// --- TypeScript Type (derived from Zod) ---

export type RadarEvent = z.infer<typeof RadarEventSchema>;
export type DailyAIRadarReport = z.infer<typeof DailyAIRadarReportSchema>;
