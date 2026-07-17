/**
 * 端到端编排 — 双模式运行
 *
 * 模式 A（定时预采集）：Python 爬虫 → radar_data.json → Agent 提炼
 * 模式 B（用户触发）：ClawBot 消息 → 读取已采集数据 → Agent 提炼 → 回复
 */

import { execFile } from "child_process";
import { promisify } from "util";
import { existsSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { resolve } from "path";
import cron from "node-cron";

import { loadConfig } from "./config";
import { AIRadarAgent } from "./agent";
import { formatReport, formatSummary } from "./delivery/formatter";
import {
  handleClawBotMessage,
  OpenClawSkillContext,
  SKILL_METADATA,
} from "./delivery/openclaw-skill";
import { pushReport } from "./delivery/push";
import type { DailyAIRadarReport } from "./types/daily-report";

const execFileAsync = promisify(execFile);

export class Orchestrator {
  readonly config: ReturnType<typeof loadConfig>;
  private agent: AIRadarAgent;

  constructor() {
    this.config = loadConfig();
    this.agent = new AIRadarAgent();
  }

  // ---- 模式 A：定时预采集 ----

  /**
   * 执行 Python 爬虫采集
   */
  async runCollection(sources?: string[]): Promise<void> {
    console.log("启动 Python 数据采集...");

    const args = ["-m", "python.src.pipeline"];
    if (sources) {
      args.push("--sources", ...sources);
    }
    args.push("--output-dir", resolve(this.config.dataDir, "raw"));

    try {
      const { stdout, stderr } = await execFileAsync("python", args, {
        cwd: resolve(__dirname, "../.."),
        timeout: 300_000, // 5 分钟超时
      });
      console.log(stdout);
      if (stderr) console.warn(stderr);
    } catch (error) {
      console.error("Python 采集失败:", error);
      throw error;
    }
  }

  /**
   * 启动每日定时任务
   */
  startCronSchedule(cronExpression: string = "0 8 * * *"): void {
    console.log(`定时任务已启动: ${cronExpression}`);

    cron.schedule(cronExpression, async () => {
      console.log("定时任务触发，开始采集...");
      try {
        // ① 采集
        await this.runCollection();
        console.log("定时采集完成");

        // ② Agent 提炼
        console.log("开始 Agent 提炼...");
        const report = await this.generateReport();
        console.log(`提炼完成: ${report.events.length} 条情报`);

        // ③ 推送到微信
        const pushResult = await pushReport(report, {
          enabled: this.config.pushEnabled,
          serverChanKey: this.config.serverChanKey,
        });
        console.log(`推送结果: ${pushResult.success}/${pushResult.total} 成功`);
      } catch (error) {
        console.error("定时任务失败:", error);
      }
    });
  }

  // ---- 模式 B：用户触发（ClawBot） ----

  /**
   * 处理 ClawBot 消息
   */
  async handleClawMessage(userMessage: string, userId: string): Promise<string> {
    const ctx: OpenClawSkillContext = {
      userMessage,
      userId,
      date: new Date().toISOString().split("T")[0],
    };

    const response = await handleClawBotMessage(ctx, () => this.generateReport());
    return response.reply;
  }

  /**
   * 生成报告（核心逻辑）
   */
  async generateReport(): Promise<DailyAIRadarReport> {
    // 确保目录存在
    if (!existsSync(this.config.reportsDir)) {
      mkdirSync(this.config.reportsDir, { recursive: true });
    }

    // 运行 Agent
    const report = await this.agent.run();

    // 保存报告
    const reportPath = resolve(this.config.reportsDir, `${report.date}.json`);
    writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf-8");
    console.log(`报告已保存: ${reportPath}`);

    return report;
  }

  /**
   * 端到端运行：采集 + 提炼
   */
  async runFullPipeline(sources?: string[]): Promise<string> {
    await this.runCollection(sources);
    const report = await this.generateReport();
    return formatReport(report);
  }

  // ---- 工具方法 ----

  /**
   * 检查今日数据是否已采集
   */
  isDataReady(): boolean {
    return existsSync(this.config.rawDataPath);
  }

  /**
   * 获取今日报告（如果已生成）
   */
  getTodayReport(): DailyAIRadarReport | null {
    const today = new Date().toISOString().split("T")[0];
    const reportPath = resolve(this.config.reportsDir, `${today}.json`);
    if (!existsSync(reportPath)) return null;
    return JSON.parse(readFileSync(reportPath, "utf-8"));
  }
}

// ---- CLI 入口 ----

async function main() {
  const orchestrator = new Orchestrator();
  const command = process.argv[2];

  switch (command) {
    case "collect":
      await orchestrator.runCollection();
      break;

    case "refine":
      if (!orchestrator.isDataReady()) {
        console.error("数据未采集，请先运行: npm run orchestrate collect");
        process.exit(1);
      }
      const report = await orchestrator.generateReport();
      console.log(formatReport(report));
      break;

    case "full":
      const output = await orchestrator.runFullPipeline();
      console.log(output);
      break;

    case "push":
      const todayReport = orchestrator.getTodayReport();
      if (!todayReport) {
        console.error("今日报告未生成，请先运行: npm run orchestrate full");
        process.exit(1);
      }
      const pushResult = await pushReport(todayReport, {
        enabled: orchestrator.config.pushEnabled,
        serverChanKey: orchestrator.config.serverChanKey,
      });
      console.log(`推送结果: ${pushResult.success}/${pushResult.total} 成功`);
      break;

    case "schedule":
      const cronExpr = process.argv[3] || "0 8 * * *";
      orchestrator.startCronSchedule(cronExpr);
      console.log("定时任务运行中，按 Ctrl+C 退出");
      break;

    default:
      console.log(`
AI Radar Orchestrator

用法:
  tsx orchestrator.ts collect          # 执行数据采集
  tsx orchestrator.ts refine           # 执行 Agent 提炼（需先采集）
  tsx orchestrator.ts full             # 端到端：采集 + 提炼
  tsx orchestrator.ts push             # 推送今日报告到微信
  tsx orchestrator.ts schedule [cron]  # 启动定时任务（默认每天 08:00）
`);
  }
}

main().catch(console.error);
