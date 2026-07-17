/**
 * 验证 radar_data.json 能被 Zod 正确校验
 */

import { readFileSync } from "fs";
import { resolve } from "path";
import { RawIntelligenceSchema } from "../src/types/raw-intelligence";

const dataPath = resolve(__dirname, "../../data/raw/radar_data.json");
const data = JSON.parse(readFileSync(dataPath, "utf-8"));

console.log(`总条数: ${data.total_items}`);

let valid = 0;
let invalid = 0;

for (const item of data.items) {
  const result = RawIntelligenceSchema.safeParse(item);
  if (result.success) {
    valid++;
  } else {
    invalid++;
    console.warn(`校验失败: ${item.title} - ${result.error.issues[0]?.message}`);
  }
}

console.log(`有效: ${valid}, 无效: ${invalid}`);
console.log(`首条: ${data.items[0]?.title}`);
