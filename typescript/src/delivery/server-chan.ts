/**
 * Server酱推送通道
 *
 * https://sct.ftqq.com/ — 国内最成熟的微信推送服务
 * 免费版每日 5 条，日报场景完全够用
 *
 * 使用方式：
 * 1. 访问 https://sct.ftqq.com/ 用 GitHub 登录
 * 2. 获取 SendKey（SCT 开头）
 * 3. 设置环境变量 SERVER_CHAN_KEY=SCTxxxxxxxxxxxx
 */

const API_BASE = "https://sctapi.ftqq.com";

export interface ServerChanConfig {
  sendKey: string;
}

/**
 * 通过 Server酱推送消息到微信
 *
 * @returns true 推送成功，false 推送失败（不抛异常，避免阻断主流程）
 */
export async function sendToServerChan(
  config: ServerChanConfig,
  title: string,
  content: string,
): Promise<boolean> {
  if (!config.sendKey) {
    console.warn("[Server酱] SendKey 未配置，跳过推送");
    return false;
  }

  const url = `${API_BASE}/${config.sendKey}.send`;

  try {
    const body = new URLSearchParams({
      title: title.slice(0, 100), // Server酱标题限 100 字
      desp: content,              // 正文支持 Markdown，无严格长度限制
    });

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });

    const data = (await response.json()) as {
      code: number;
      message: string;
      data?: { pushid: string; readkey: string };
    };

    if (data.code === 0) {
      console.log(`[Server酱] 推送成功，pushid: ${data.data?.pushid}`);
      return true;
    }

    console.error(`[Server酱] 推送失败: ${data.message}`);
    return false;
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : String(error);
    console.error(`[Server酱] 推送异常: ${errMsg}`);
    return false;
  }
}
