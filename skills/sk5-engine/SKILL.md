---
name: sk5-engine
description: SK5推演核心引擎：统筹运动学、鱼雷、侦察、炮击、过穿与战损。
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sk5, seekrieg, seekrieg5, engine, wargame, 兵棋, 推演引擎, simplot]
---

# Seekrieg 5 (SK5) 海战推演核心引擎 (SK5 Engine)

本技能为 Seekrieg 5 (SK5) 桌面与移动端兵棋推演的**唯一底层统一推演主引擎**，统筹负责机动运动学、水下鱼雷建模、雷达与目视侦察、火炮火控解算、法定穿甲等级与过穿裁决、总体战损闭环及 SimPlot2 存档生成。

---

## 🏛️ 第一部分：运动学与 SimPlot 存档规范

### 1. 运动学与航迹计算
- **时间标尺**：每回合固定为 **2 分钟**；
- **转向折算**：
  - $\le 15^\circ$：实际移动距离不缩减（100%）；
  - $> 15^\circ$：标准舵（Standard Turn）折算 **75% 航程**，急舵（Emergency Turn）折算 **50% 航程**；
- **渐进分段（Advance 前冲）**：多段转向第 1 段强制沿原航向直行（模拟舵效响应前冲），从第 2 段起均分剩余角度；
- **极速截断**：指令航速超出船表设计极速（Max Speed）时，自动截断（Clamp）在最大极速执行。

### 2. 实体级水下鱼雷航迹建模 (Torpedo Objects)
发射的水下鱼雷必须作为独立实体写入 `Units` 与 `Objects` 数组：
- **命名与类型**：`IdNum: "U045..."`，`UnitType: "Torpedo"`，`UnitClass: "TORP"`；
- **航迹链**：`PastWaypointArray1` 记录从发射点 $(X_0, Y_0)$ 至当前位置 $(X_t, Y_t)$ 的 12 元素航路点链；
- **扇面危险区宽度**：
  - **宽扇面（Wide Spread）**：危险区宽度 **`1,500 码`**；
  - **标准扇面（Standard Spread）**：危险区宽度 **`1,000 码`**；
  - **窄扇面（Narrow Spread）**：危险区宽度 **`500 码`**。

### 3. PC 桌面端与 Android 端双端 100% 互通红线
- **顶层时间模型**：顶层 `Time` 必须严格为 `TimeState` 对象：
  ```json
  "Time": {
    "CurrentTurnTime": "YYYY-MM-DD HH:MM:SS",
    "CurrentPositionTime": "YYYY-MM-DD HH:MM:SS",
    "CurrentTurnInterval": { "Minutes": 2, "Seconds": 0 }
  }
  ```
- **19 字符时间戳**：所有航路点时间与单位时间字段一律使用完整的 `YYYY-MM-DD HH:MM:SS` 格式；
- **空对象化**：未移动单位或空集合必须写 `{}`（空对象），严禁写 `[]`；
- **航迹起点闭环**：`PastWaypointArray1[0]` 必须保留 T0 起点坐标；
- **单位存活时间**：`PositionTimeDeleted` 统一设定为远未来时间（`1943-11-14 23:00:00`）。

### 4. 双盲感知阵列规范 (PerceptionArray)
- **初次捕获**：`ShowAsSide: Unknown`, `ShowAsType: Unknown`, `ShowCourseSpeed: false`, `ShowName: false`；
- **连续跟踪 $\ge 2$ 回合**：`ShowAsSide: Red/Blue`, `ShowAsType: Destroyer/Cruiser/Battleship`, `ShowCourseSpeed: true`（显示动态矢量线），`ShowName: false`（严格隐去具体舰名）；
- **失去接触**：直接移除 `PerceptionArray`（置为 `None`）。

---

## 📡 第二部分：侦察与探测判定体系

1. **国际海事精确换算基准**：
   $$\mathbf{1\text{ NM} = 1,852\text{ 米} = 2,025.37\text{ 码 (Yards)}} \quad (1852 / 0.9144)$$
2. **雷达探测双重约束**：
   $$\mathbf{\text{有效雷达探测距离} = \min(\text{Table Z4 NOTES 硬件指标}, \text{Chart D3 双方尺寸交叉几何地平线})}$$
3. **火炮闪光与物理几何地平线**：
   - Chart D1 为上层建筑识别距离，**真实物理几何地平线以 Chart D3 雷达视距表为准**；
   - 火炮闪光与目视探测有效视距：
     $$\mathbf{\text{有效视距} = \min(\text{Chart D5 闪光表}, \text{Chart D3 几何地平线})}$$
     - 6″ 及以上重炮闪光：`22,000 码`（10.86 NM）；
     - 小口径火炮闪光：`17,500 码`（8.64 NM）；
     - 未开火战舰夜间常规目视极限仅 2.5 ~ 4.2 NM（Chart D2 Code 8）。

---

## ⚔️ 第三部分：火炮火控与集火解算体系

1. **单回合射速法则 (ROF)**：穿深表所列 ROF 为 2 分钟回合单管弹数，单回合发射总弹数：
   $$\text{发射弹数} = \lfloor \text{ROF} \times \text{参战可用门数} \rfloor \quad (\text{严禁再乘以 2})$$
2. **新目标首轮射速减半**：首回合射击新目标或切换目标时，射速折半（$\lfloor \text{ROF} \times 0.5 \times \text{门数} \rfloor$），且火控修正 $-2$。
3. **火炮射界核验 (Chart G1)**：
   - 战列舰艉部 #3 炮塔存在前向 $0^\circ \sim 60^\circ$ 死角；
   - 巡洋舰/驱逐舰艉部炮塔存在前向 $0^\circ \sim 30^\circ$ 死角；
   - 只有处于射界内的火炮才计入参战门数。
4. **过度集中射击修正 (Chart H1.6)**：
   - 当 $N$ 艘舰艇在同回合集火同一目标时，**所有 $N$ 艘射击舰在火控中全员均承受 $-(N - 1)$ 的过度集中射击惩罚**，而非仅后射舰承受。
5. **雷达盲射修正 (Chart H1.1e)**：火控修正 $-5$，忽略烟雾修正，火控表强制查 Narrow（窄舷）列。

---

## 🛡️ 第四部分：法定穿甲等级、过穿检定与战损体系

每次命中在计算 DP 点数前，必须强制完成穿甲等级（Penetration Class）裁决：

```
【命中部位】 (Chart J1/J2) ──> 查目标该部位有效装甲厚度
      ↓
【装甲 ≤ 0.5"（薄弱/无装甲目标）】 ──> 查 Chart K3 (UNARMORED):
  • AP / SAP: 01-20 Class A (引爆) / 21-00 Class B (过穿未爆)
  • COM: 01-70 Class A / 71-00 Class B
  • HE: 01-90 Class A / 91-00 Class B
      ↓
【装甲 > 0.5"（装甲目标）】 ──> 查 Chart K1 / K2:
  • 穿深 < 装甲: Class C (未穿透)
  • 装甲 ≤ 穿深 ≤ 2×装甲: Class A (穿透引爆)
  • 穿深 > 2×装甲 (情况 X): 查 Chart K2 检定过穿 (AP 01-30 Class A / 31-00 Class B)
```

1. **穿甲等级对伤害计算（Chart K4）的法定影响**：
   - **Class A（穿透引爆）**：造成最大全额爆炸伤害，按 D100 掷骰分档计算高额 DP，DE 触发率最高；
   - **Class B（过穿未引爆）**：炮弹直接穿出舰体，**只造成 Chart K4 Class B 列的固定贯穿结构伤（无需掷骰分档）**，DE 触发率减半；
   - **Class C（未穿透）**：仅造成外板冲击伤。
2. **关键损伤效应 (DE) 与内嵌全量闭环**：
   - 触发 DE 后立即查 Table L3，若触发次生 DE（如 DE 100 弹药库殉爆、DE 107 卡死、DE 152 起火 Severity 20、*606 结构损毁、*615 电路受损），必须**立即全量投骰闭环结算具体受损炮塔编号与系统数值**，严禁留下未决描述。
3. **Tier 总体损伤评级**：累计战损每跨越一个 10% 门槛，按船表实印检定率独立投 D100；触发后查 Table L3 G 栏，带 `*` 号 DE 全舰唯一且自低向高逐级判定。
