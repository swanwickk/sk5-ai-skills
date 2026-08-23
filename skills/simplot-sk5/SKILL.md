---
name: SimPlot SK5 海战兵棋推演
version: "1.2.0"
description: "生成/编辑 SimPlot2 存档，专为 Seekrieg 5 (SK5) 规则定制。SK5 2分钟回合、标准舵75%/急舵50%转向距离衰减、先直行前冲后转角的渐进尾迹；含桌面版光栅地图协议（TypeOfMap=1 + txt MAP/SCALE）。"
---

# SimPlot Seekrieg 5 (SK5) 推演存档工具

生成、读取、编辑 SimPlot2 桌面兵棋针对 **Seekrieg 5 (SK5)** 规则的推演存档文件。

## SK5 移动引擎机制

脚本内部的机动引擎完全贴合 SK5 物理表现：
1. **时间标尺**：每回合固定为 **2 分钟**。
2. **折扣与速度剥离**：舰艇转向时，存档与UI面板的**轮机标定航速（Speed字段）不变**，但计算坐标偏移时应用了距离折扣。
   - ≤ 15°：实际移动距离不缩减（100%）。
   - > 15°：标准舵实际移动距离折算 75%，急舵折算 50%。
3. **渐进分段（Progressive Turns）与前冲（Advance）**：
   - 尾迹按转向角度大小切分为 1~5 段平滑弧线。
   - **核心物理机制**：所有多段转向，**第一段强制沿原航向直行（模拟舵效响应期间的船体前冲）**，从第二段起，将剩余需转过的角度平均分配至各段。完美契合约 45° 的最大单段战术偏转角极限。

## 桌面版地图协议（经反编译 + 用户工作存档验证）⭐

SimPlot2 桌面版光栅地图加载方式（`MercatorRaster.LoadMapData`）：

```
Scenario.TypeOfMap = 1
Scenario.MapFileName = "地图.txt"      # 指向配套 txt
```

txt 文件（**必须 Windows CRLF 换行**）：
```
MAP=地图图片.jpg
SCALE=20.3          <- 每海里像素数 (px per NM)，Double
```

**换算公式**（图片左上角像素(0,0) = 世界坐标(0,0)）：
```
worldX = px_x / SCALE * 100000       # 1 NM = 100000 存档单位
worldY = -px_y / SCALE * 100000      # px_y 从上往下为正；南纬为负
```

**坑**：
- SCALE 是"每海里像素数"，不是"每像素海里数"——写反会差 200 多倍，地图显示异常/单位全跑图外。用 `px/nm = 图片宽度px / 地图实际海里宽度` 计算。
- txt 必须 CRLF（`\r\n`），用 `write_raster_map_txt` 生成。
- 所有**空数组必须写 `{}`（dict）**，写 `[]` 桌面版直接崩溃/打不开。Units 的 PastWaypointArray1/FutureWaypointArray1、Overlays、Formations 同理。
- 单位坐标必须与地图同一世界坐标系（按上述公式由像素换算），不能凭空按剧本航向放。

## 工作流与脚本调用

### 地图（`scripts/sk5_map_tool.py`）
```python
import sys; sys.path.insert(0, 'scripts')
from sk5_map_tool import write_raster_map_txt, px_to_world, mk_unit, make_scenario_save, write_scenario_save

# 1) 生成地图配套 txt（CRLF）
write_raster_map_txt("Ironbottom_Sound_Map.jpg", 20.3, "地图.txt")

# 2) 像素 -> 世界坐标（锚定单位位置）
wx, wy = px_to_world(px_x, px_y, 20.3)

# 3) 构造单位（传感器/机场/航路点参数齐全）
u = mk_unit("S001", "华盛顿", "Battleship", wx, wy, side="Blue", speed_kt=30.0, course_deg=270, sensor_array=True)

# 4) 组装完整存档
save = make_scenario_save("第二次瓜岛海战", [u, ...], "地图.txt", turn_minutes=2)
write_scenario_save(save, "out.json")
```

### 移动推进（`scripts/simplot_sk5_cmd.py`）
```python
import simplot_sk5_cmd as cmd
cmd.process_turn(unit_data, 30.0, 90.0, False, "12:02:00")
# 参数: 单位dict, 计划航速(节), 计划航向(度), 是否急舵, 当前时间戳
```
引擎自动计算前冲、分配转角、折扣距离，并写入 `PastWaypointArray1` 中间节点画出圆滑尾迹。

### 关键单位字段（与工作存档逐字段一致）
- 舰船：`Speed/Course ×1000` 定点整数，`Range=-100000`，`WpDistance=0`，`PastWaypointArray1={}`（未动）或真实航路点数组（已动）。
- 航路点元素：`["", x, y, 0,0, alt,0,0,0, 1, true, "时间"]`
- 机场/登陆点（Installation/Reference Point）：**无 Speed/Course** 等机动字段；TextTags 里 TagCourseSpeed=False。
- 雷达舰：`SensorArray` 三通道 FC L / M / S（MaxRange 按舰定）。
- 机场可加 `PerceptionArray` 让对方看到（ShowAsType="Airfield" 等）。

## 完整存档结构（Referee 模式）

顶层 keys 顺序：`File="Referee"`、`SimPlot Version="2.3"`、`IsIntegerFile=True`、`Scenario`、`TypeOfGame=0`、`Time`、`Turns`、`Overlays={}`、`Objects=[单位ID列表]`、`Units=[单位dict]`、`Formations={}`。

## 验证清单

生成后自查：
1. txt 为 CRLF、SCALE = 像素/海里（非倒数）。
2. 所有空数组为 `{}` 而非 `[]`。
3. 单位坐标由 px→world 公式得到，与地图同坐标系。
4. 中文名（舰名/剧本名）正常保留（ensure_ascii=False）。
5. 舰船有 Speed/Course，机场/登陆点没有。
