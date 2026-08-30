---
name: sk5-ship-database
description: SK5战舰数据库与调船：查船/调出船表/ships.db/生成推演卡。
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sk5, seekrieg, seekrieg5, ship-database, sqlite, wargame, 兵棋, 战舰数据库]
---

# SK5 本地战舰冷数据库运维与按需调用技能 (SK5 Ship Database)

本技能定义了本地 **Seekrieg 5 (SK5) 战舰冷数据库** 的物理架构、SQLite 数据库规范、CLI 检索工具操作、批量导入入库 SOP 以及 AI 兵棋推演过程中的“零常驻、按需冷调用”标准工作流。

---

## 🏛️ 核心架构与设计原则

数据库根目录固定为 `/root/sk5_database/`：

```
/root/sk5_database/
├── ships.db            # SQLite 核心单文件数据库（含元数据、FTS5 全文索引、MD 全文与 JSON 速填卡缓存）
├── sk5_db.py           # CLI 终端极速检索与导出工具
├── md/                 # 3,354 艘战舰的标准 Markdown 船表（中文名_英文安全名_年代_标准船表.md）
├── json/               # 3,354 艘战舰的炮击计算器 JSON 速填卡
├── pdf/                # 原始分队/全集 PDF 文件归档
├── import_usa_full_fleet_v2.py  # 权威实印批量解析与入库脚本
└── README.md           # 数据库使用手册
```

### 三大核心原则
1. **绝对零常驻（Zero Context Footprint）**：
   - 数据库平时完全处于“冷态”，不常驻 AI 上下文，不占用提示词 Token，不消耗后台进程内存；
   - 只有玩家明确要求“*调出某舰船表*”、“*查询某类战舰*”或进行对局解算时，AI 才通过 CLI 脚本毫秒级按需提取数据。
2. **100% 官方原页实印（Real Printed Data Grounding）**：
   - 严禁任何口径/年代预设推断或合成数据；
   - 库内所有双页战舰的穿透表（Penetration Table）与火控表（Fire Control Table）均通过物理坐标聚类从官方 PDF 真实抓取。
3. **单页小艇与双页大舰双版式自适应**：
   - 严格区分 2,121 艘双页主力大舰与 91 艘单页独立小艇（DD-1、炸药炮巡洋舰 Vesuvius、撞角巡洋舰 Katahdin）；
   - 单页小艇规范标记为近程速射炮（RF）与鱼雷武装，统一查 Table W1 简化火控表，绝不强行拼页。

---

## 🗄️ SQLite 数据库规范 (`ships.db`)

### 主表：`ships` (当前已收录 3,354 艘)
```sql
CREATE TABLE ships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_zh TEXT NOT NULL,              -- 中文标准舰名（如：华盛顿、爱荷华、企业、法拉格特）
    name_en TEXT NOT NULL,              -- 英文原名（如：Washington, Iowa, Enterprise (CV 6)）
    country TEXT NOT NULL,              -- 国别（UNITED STATES: 2212艘, JAPAN: 1142艘）
    hull_type TEXT NOT NULL,            -- 舰型代码（BB, CB, CA, CL, CV, DD, BM 等）
    class_code TEXT,                    -- 舰级与编号（2207-0 IOWA Class, 5239-0 FARRAGUT Class）
    year_variant TEXT,                  -- 年代变体（1943 to 1945, 1899 to 1912）
    displacement INTEGER,               -- 标准排水量 (ts)
    total_dp INTEGER,                   -- 总损伤点数 (Total DP)
    max_speed REAL,                     -- 最大航速 (KTS)
    target_size INTEGER,                -- 目标尺寸 (Target Sz)
    main_gun_mount TEXT,                -- 主炮配置型号（9 x 16"/50 Mk 7, 6pdr/42 57mm）
    main_gun_caliber REAL,              -- 主炮口径（16.0, 14.0, 5.0, 2.24 英寸）
    main_gun_df INTEGER,                -- 主炮损伤因数 (DF)
    radar_fc_bonus INTEGER,             -- 火控雷达加成点数（0, 2, 3）
    dcr INTEGER,                        -- 损管等级 (DCR)
    team TEXT,                          -- 所属分队/全集编制标签
    md_filename TEXT,                   -- Markdown 文件名（已安全清洗特殊符号）
    md_content TEXT,                    -- 标准 Markdown 船表全文
    json_content TEXT,                  -- 计算器 JSON 速填卡全文
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 全文检索表：`ships_fts` (FTS5)
```sql
CREATE VIRTUAL TABLE ships_fts USING fts5(
    name_zh, name_en, country, hull_type, class_code, main_gun_mount, md_content,
    content='ships', content_rowid='id'
);
```

---

## 🛠️ CLI 工具使用指南 (`sk5_db.py`)

在 Linux 终端或 AI 执行环境中调用：

```bash
# 1. 查看数据库统计与各舰型/编制分布
python3 /root/sk5_database/sk5_db.py stats

# 2. 列出战舰列表（支持按国别、舰型、编制过滤）
python3 /root/sk5_database/sk5_db.py list --country "UNITED STATES" --hull BB
python3 /root/sk5_database/sk5_db.py list --country "UNITED STATES" --hull CV
python3 /root/sk5_database/sk5_db.py list --team "美军驱逐舰_WW2"

# 3. 调出指定战舰
# (1) 战舰快速属性卡
python3 /root/sk5_database/sk5_db.py get "爱荷华"
python3 /root/sk5_database/sk5_db.py get "Enterprise (CV 6)"
python3 /root/sk5_database/sk5_db.py get "Washington" --format json
# (2) 导出完整六章标准 Markdown 船表
python3 /root/sk5_database/sk5_db.py get "Washington" --format md --out /root/.hermes/workspace/Washington_1942.md

# 4. 全文关键词检索（武器、雷达、飞机、动力型号）
python3 /root/sk5_database/sk5_db.py search "16\"/50 Mk 7"
python3 /root/sk5_database/sk5_db.py search "Kingfisher"
python3 /root/sk5_database/sk5_db.py search "CXAM"

# 5. 复合数值条件筛选
python3 /root/sk5_database/sk5_db.py query --min-gun 16.0 --min-dp 3000 --country "UNITED STATES"
python3 /root/sk5_database/sk5_db.py query --radar --min-speed 30.0
```

---

## 🤖 AI 兵棋推演按需冷调用 SOP

1. **“调出 [舰名] 船表”**：终端调用 `sk5_db.py get [舰名] --format md` 提取六章标准船表展示；
2. **“计算 [射击舰] 炮击 [目标舰]”**：分别提取射击舰与目标舰的 JSON 速填卡，提取主炮口径、DF、ROF、射程、火控雷达及目标装甲，严格按 SK5 规则查表解算。
