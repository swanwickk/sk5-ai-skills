# SK5 AI Skills — Seekrieg 5 海战兵棋 AI 技能集 (v2.0)

将 **Seekrieg 5（SK5）** 战术海战兵棋与 **SimPlot2** 桌面/移动端标图的完整推演流程工程化，供 AI Agent（如 Hermes Agent 等）加载使用的专业技能（Skills）统一体系。

配套在线工具：**SK5 炮击计算器** <https://sk5.swanwick.site>  
移动端标图：**SimPlot Android / 铁底湾** <https://tdw.swanwick.site>

---

## 📦 三位一体统一架构 (3-in-1 Unified Architecture)

```
sk5-ai-skills/
├── skills/
│   ├── sk5-engine/                         # 【推演主引擎】：运动学、鱼雷、雷达/目视侦察、G1射界、H1.6集火、K1-K4穿甲与过穿裁决、Tier闭环与 SimPlot2 存盘
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── simplot_sk5_cmd.py          # SK5 2分钟机动与前冲推进引擎
│   │   │   ├── sk5_scn_tool.py             # SimPlot 存档标准序列化工具
│   │   │   ├── sk5_map_tool.py             # 光栅地图 txt 与坐标换算
│   │   │   └── sk5_distances.py            # D表侦察与地平线测距工具
│   │   └── references/
│   │       └── d-tables-visibility-detection.md  # D1-D5 视距与夜战闪光速查
│   ├── sk5-situation-briefing/             # 【双盲简报通信层】：标准 5 大独立板块、双盲情报隔离、雷达水柱回波/起火爆炸观察规范
│   │   └── SKILL.md
│   └── sk5-ship-database/                  # 【战舰冷资产库】：SQLite 3354 艘 ships.db、PDF 实印坐标直采解析与 CLI 工具
│       └── SKILL.md
├── tools/
│   └── sk5_db.py                           # 冷数据库 CLI 查询工具（list/get/search/query/stats）
└── README.md
```

---

## 🎯 核心能力与推演闭环

### 1. 核心推演主引擎 (`skills/sk5-engine`)
- **SK5 运动学与物理减速**：2 分钟回合标尺；标准舵折算 75%、急舵 50%；多段转向首段强制沿原航向直行（舵效前冲 Advance）；超出船表极速自动截断（Clamp）。
- **实体水下鱼雷建模**：独立 `UnitType: "Torpedo"` 实体、`PastWaypointArray1` 水下航迹链、扇面危险区宽度（宽 1500 码 / 标 1000 码 / 窄 500 码）。
- **双重约束侦察体系**：国际海事精确换算（$1\text{ NM} = 2,025.37\text{ 码}$）；$\min(\text{Table Z4 NOTES}, \text{Chart D3 物理几何地平线})$；Chart D5 重炮闪光（22,000 码）与小口径闪光（17,500 码）。
- **火炮火控与集火**：ROF 单回合门弹数法则；新目标首轮射速减半；Chart G1 射界死角核验；**Chart H1.6 多舰集火全员同等承受 $-(N-1)$ 惩罚**；Chart H1.1e 雷达盲射。
- **法定穿甲等级与过穿裁决**：
  - 部位装甲 $\le 0.5"$ 强制查 **Chart K3**（AP 21-00 过穿未爆 Class B，HE 91-00 过穿）；
  - 穿深 $> 2\times$装甲 强制查 **Chart K2**；
  - **Class B（过穿未爆）只造成 Chart K4 Class B 固定贯穿结构伤**，大幅免受内部大爆炸；
- **总体战损 (Tier) 与内嵌闭环**：累计战损跨越 10% 门槛独立投 D100；触发后查 Table L3 G 栏；次生 DE（DE 100 弹药库殉爆、DE 107 卡死、DE 152 起火 Severity 20 等）当回合全量闭环投骰，严禁未决描述。
- **SimPlot2 双端 100% 互通**：顶层 `TimeState` 模型、19 字符完整时间戳、空对象 `{}` 防崩溃、`PerceptionArray` 连续跟踪动态显隐。

---

### 2. 双盲简报与通信层 (`skills/sk5-situation-briefing`)
- **标准 5 大独立板块**：
  - ① 舰队各舰当前航态与状态（表格）
  - ② 本回合舰队侦察结果（带 `tn xxxx` 编号、方位、距离）
  - ③ 本回合舰队射击结果（明确标注发射弹种，盲射报水柱回波，仅明确产生起火/殉爆才报起火爆炸）
  - ④ 舰队被攻击与战损情况（4.1 本回合被攻击情况，末尾自然陈述“其他单位均报告未受到攻击”；4.2 全舰队累计受损汇总）
  - ⑤ 弹药存量（精确追踪分弹种余量）
- **干练军事文风**：有情况写实况，没情况直接写“未见异常”或“无异常”，严禁负面罗列“未见XX、未见YY”冗余套话。

---

### 3. 战舰冷资产库 (`skills/sk5-ship-database`)
- **绝对零常驻**：SQLite `ships.db` 平时处于冷态，推演时通过 `sk5_db.py` 毫秒级按需提取，不占上下文 Token。
- **100% 官方原页实印**：收录美日二战 3,354 艘战舰标准 Markdown 船表与计算器 JSON 速填卡。

---

## ⚖️ 版权声明

本仓库仅包含 **AI Agent 工作流程文档、推演引擎代码与 SOP**，不含任何 Seekrieg 5 商业规则书扫描件或受版权保护的原版 PDF。Seekrieg 5 为 Jeff Casher（Deep Sea Wargames）作品，相关版权归其所有。

## License

MIT
