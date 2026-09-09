---
name: sk5-simplot-format
description: SimPlot2 .scn存档格式规范：双端互通、航迹点对象、序列化红线。
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sk5, simplot, scn, 存档, format]
---

# SimPlot2 存档写入格式规范 (sk5-simplot-format)

**仅在写入/修改 .scn 存档时加载本技能。推演判定逻辑见 sk5-engine。**

---

## 🔴 HALT 级（违反即存档拒载，必须返工）

1. **字段名无后缀**：`PastWaypointArray` / `FutureWaypointArray`，严禁 `*Array1`（`grep -c Array1` 必须为 0）。
2. **航迹点必须是 12 键对象**，严禁 12 元素数组。键序（字母序）：`AltitudeDepth, Ascent, AssignedAltDepth, Course, Descent, IsTurnTime, Name, Number, PositionTime, Speed, X, Y`。
3. **C/S 语义互换**：对象 `Course` = 航速×1000，`Speed` = 航向×1000（例：35kt 航向 30° → `Course:35000, Speed:30000`）。`Number:1, IsTurnTime:true, Name:""` 恒定。
4. **腿时间戳不重复**：同回合多腿按等分展开截断到整分（2段 → `:25/:26`），严禁同回合两点同一时间戳。
5. **空集合写 `{}`**，严禁 `[]`。
6. **序列化**：紧凑 JSON（`separators=(',',':')`，`ensure_ascii=False`，`sort_keys=True`），全文件单行，末尾 `CRLF`（`\r\n`）单换行，无 BOM。

## 🟡 CHECK 级（易错须核验）

7. **顶层 Time 必须为 TimeState 对象**：
   ```json
   "Time": {
     "CurrentTurnTime": "YYYY-MM-DD HH:MM:SS",
     "CurrentPositionTime": "YYYY-MM-DD HH:MM:SS",
     "CurrentTurnInterval": { "Minutes": 2, "Seconds": 0 }
   }
   ```
8. **19 字符时间戳**：所有时间字段一律 `YYYY-MM-DD HH:MM:SS`。
9. **航迹起点闭环**：`PastWaypointArray[0]` 必须保留 T0 起点坐标。
10. **Turns 原样保留**：PC 推进 Time 时不碰 Turns，写档时原样保留。
11. **Objects 按 Units 重建**：`Objects[i] == Units[i].IdNum` 逐项对齐。
12. **PositionTimeDeleted** 统一设远未来时间（`1943-11-14 23:00:00`）。
13. **PerceptionArray**：有感知数据的单位保留，值为 None 的单位**删键**（PC 原档无此键即无 null）；静态单位无航迹键原样保留，严禁补。

## ⚪ REF 级（按需查阅）

14. **鱼雷实体**：`IdNum: "U045..."`, `UnitType: "Torpedo"`, `UnitClass: "TORP"`，航迹链同上规范。
15. **双盲感知阵列**：初次 `ShowAsSide/ShowAsType: Unknown`；连续跟踪≥2回合 `ShowCourseSpeed: true, ShowName: false`；失联删 PerceptionArray 键。
16. **PC 端排查优先序**：① 字段名无后缀 → ② 航迹点 12 键对象 → ②b PerceptionArray → ③ TrackNumber 全局唯一 → ④ 清私有字段 → ⑤ Turns 保留 → ⑥ Objects 重建 → ⑦ 序列化 → ⑧ 仍失败走 App 中转。

---

## 照明弹存档标绘

照明弹落点以参考点实体标出（`IdNum: Rxxx` + `TextTags.AdditionalText` 标注 "照明区2500x1500码"）。
