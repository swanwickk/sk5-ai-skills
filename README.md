# SK5 AI Skills — Seekrieg 5 海战兵棋 AI 技能集

将 **Seekrieg 5（SK5）** 战术海战兵棋的船表数据管理、转录与火控解算流程工程化，供 AI Agent（如 Hermes Agent 等）加载使用的技能（Skills）合集。

配套在线工具：**SK5 炮击计算器** <https://sk5.swanwick.site>

## 📦 内容

```
sk5-ai-skills/
├── skills/
│   ├── sk5-ship-database-SKILL.md        # 船表冷数据库：SQLite 架构、CLI 检索、零常驻冷调用 SOP
│   ├── sk5-ship-log-reader-SKILL.md      # 船表读取：PDF 船表 → 标准 Markdown + 计算器 JSON 速填卡
│   ├── sk5-gunfire-calculator-SKILL.md   # 炮击计算：全场统筹修正 → 命中/穿透/DP/DE 完整解算 SOP
│   └── simplot-sk5/
│       ├── SKILL.md                      # SimPlot2 存档生成/编辑：SK5 移动引擎、光栅地图协议
│       └── scripts/                      # 存档读写 / 地图坐标换算 / SK5 机动推进工具脚本
│           ├── sk5_scn_tool.py
│           ├── sk5_map_tool.py
│           └── simplot_sk5_cmd.py
├── tools/
│   └── sk5_db.py                         # 冷数据库 CLI 查询工具（list/get/search/query/stats）
└── references/
    └── sk5_ship_log_spec.md              # SK5 标准船表字段规范与规则手册映射（B1/B2/C4/W1/J1/K4/L/M1）
```

## 🎯 设计原则

1. **绝对零常驻（Zero Context Footprint）**——数据库平时完全冷态，不占 AI 上下文 Token；推演时按需毫秒级提取。
2. **100% 官方原页实印**——严禁按口径/年代推断或合成穿深表、火控表；所有数值从官方 PDF 物理坐标聚类直采。
3. **双版式自适应**——区分双页主力大舰与单页独立小艇（RF 速射炮/鱼雷走 Table W1 简化火控），绝不强行拼页。
4. **零脑补阻断机制**——推演要素缺失时立即暂停并向玩家索取，绝不自行代入默认值。

## 🚀 快速开始

### 数据库 CLI

```bash
# 统计摘要
python3 tools/sk5_db.py stats

# 按国别+舰型筛选
python3 tools/sk5_db.py list --country "UNITED STATES" --hull BB

# 调出完整标准 Markdown 船表
python3 tools/sk5_db.py get "爱荷华" --format md

# 全文检索武器 / 雷达型号
python3 tools/sk5_db.py search "16\"/50 Mk 7"

# 复合条件筛选
python3 tools/sk5_db.py query --min-gun 14 --min-speed 28 --radar
```

> `tools/sk5_db.py` 默认读取同目录下 `./database/ships.db`。数据库本体（含 3000+ 艘舰的标准 Markdown 船表全文、计算器 JSON 速填卡与 FTS5 全文索引）由官方 PDF 解析脚本离线构建，因版权原因不在本仓库分发。

### 加载为 AI 技能

将 `skills/*.md` 放入你的 Agent 技能目录（Hermes Agent 为 `~/.hermes/skills/<category>/<name>/SKILL.md`），Agent 即可按其中的 SOP 执行：

- 「调出 XX 船表」→ CLI 提取六章标准 Markdown 船表
- 「计算 A 炮击 B」→ 全场统筹修正 → 命中部位 → 穿透比对 → DP/DE 结算 → 结构化战报
- 「解析这份 PDF」→ 双页/单页版式判定 → 穿透表/火控表物理坐标直采 → MD + JSON 双交付物
- 「SimPlot 存档 / 移动标绘」→ SK5 机动引擎推进（前冲 + 渐进尾迹）→ SimPlot2 存档生成与编辑

## 🚢 SimPlot 移动引擎（skills/simplot-sk5）

针对 SimPlot2 桌面兵棋的 SK5 定制存档方案，含可运行脚本：

- **SK5 机动引擎**：每回合 2 分钟；转向 >15° 时标准舵距离折算 75%、急舵 50%；多段转向首段强制沿原航向直行（舵效前冲），其余角度平均分配，切出 1~5 段平滑渐进尾迹。
- **光栅地图协议**（反编译验证）：`Scenario.TypeOfMap=1` + 配套 CRLF txt（`MAP=` 图片、`SCALE=` 每海里像素数），像素 ↔ 世界坐标换算公式与已知坑位清单齐全。
- **存档安全红线**：所有空数组必须写 `{}`（写 `[]` 桌面版崩溃）、舰船 `Speed/Course ×1000` 定点整数、机场/登陆点无机动字段等，逐条经工作存档验证。

```python
import simplot_sk5_cmd as cmd
cmd.process_turn(unit_data, 30.0, 90.0, False, "12:02:00")
# 自动计算前冲、分配转角、折扣距离，写入航路点画出圆滑尾迹
```

## 📋 三技能流水线

```
官方 PDF 船表
     │
     ▼
[sk5-ship-log-reader]  版式判定 + 坐标聚类实印直采
     │
     ▼
标准 Markdown 船表 + JSON 速填卡 ──► SQLite 冷库 (ships.db)
     │                                        │
     ▼                                        ▼
[sk5-gunfire-calculator] ◄──按需冷调用── [tools/sk5_db.py]
     │
     ▼
结构化推演战报（命中数 / 部位 / 穿透 / DP / DE / Tier 检定）
```

## ⚖️ 版权声明

本仓库仅包含**工作流程文档、SOP 与工具代码**，不含任何 Seekrieg 5 规则书文本、数据表格原文或官方 PDF。Seekrieg 5 为 Jeff Casher（Deep Sea Wargames）作品，相关版权归其所有。

## License

MIT
