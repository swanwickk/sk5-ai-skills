"""
sk5_map_tool.py —— SimPlot2 桌面版光栅地图协议（经验证，反向工程自用户工作存档）

协议要点（桌面 MercatorRaster.LoadMapData）：
  1) 场景 Scenario.TypeOfMap = 1, Scenario.MapFileName = "<xxx>.txt"
  2) txt 文件（Windows CRLF 换行）:
         MAP=图片文件名.jpg
         SCALE=20.3          <- 像素/海里 (px per NM)，Double
  3) 图片锚点：图片左上角(px 0,0) 对应世界坐标 (0,0)
  4) 换算公式:
         worldX = px_x / SCALE * 100000      (NM * 100000 = 存档单位)
         worldY = -px_y / SCALE * 100000     (px_y 从上往下为正；南纬为负)
     反向:
         px_x = worldX / 100000 * SCALE
         px_y = -worldY / 100000 * SCALE

注意：SCALE 是"每海里像素数"，不是"每像素海里数"（反向会错 208 倍）。
      空数组一律写 {} (dict)，写 [] 会导致桌面崩溃/打不开。
"""
import json
import math


# ---------------------------------------------------------------------------
# 1. 光栅地图 txt 生成
# ---------------------------------------------------------------------------
def write_raster_map_txt(image_filename, scale_px_per_nm, out_txt_path,
                         cities=None, countries=None):
    """
    生成桌面可读的光栅地图配套 txt（Windows CRLF）。
    image_filename : 图片文件名（与 txt 同目录）
    scale_px_per_nm: 每海里像素数 (px / NM)
    cities/countries: 可选 [(名称, px_x, px_y), ...] 会写成 CITY=/COUNTRY= 行
    """
    lines = [f"MAP={image_filename}", f"SCALE={scale_px_per_nm}"]
    for name, px, py in (cities or []):
        lines.append(f"CITY={name}|{px}|{py}")
    for name, px, py in (countries or []):
        lines.append(f"COUNTRY={name}|{px}|{py}")
    # Windows CRLF
    text = "\r\n".join(lines) + "\r\n"
    with open(out_txt_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return out_txt_path


# ---------------------------------------------------------------------------
# 2. 像素 <-> 世界坐标换算
# ---------------------------------------------------------------------------
def px_to_world(px_x, px_y, scale_px_per_nm):
    """px -> (worldX, worldY) 存档单位 (1 NM = 100000)"""
    wx = px_x / scale_px_per_nm * 100000.0
    wy = -px_y / scale_px_per_nm * 100000.0
    return wx, wy


def world_to_px(world_x, world_y, scale_px_per_nm):
    """worldX/worldY(存档单位) -> (px_x, px_y) 图像像素"""
    px_x = world_x / 100000.0 * scale_px_per_nm
    px_y = -world_y / 100000.0 * scale_px_per_nm
    return px_x, px_y


# ---------------------------------------------------------------------------
# 3. 经纬度 -> 世界坐标（等距圆柱近似，两个已知锚点定标）
# ---------------------------------------------------------------------------
def make_geo_converter(anchor_a, anchor_b):
    """
    用两个地理锚点建立 (经度,纬度)->世界坐标 的线性映射。
    anchor_a / anchor_b: (lat_deg, lon_deg, world_x, world_y)
    说明：这是等距圆柱近似（地图通常就是这种投影），小范围内足够精确。
    例：Savo(159.82E,9.13S) + Henderson(160.05E,9.43S)，已知各自在世界坐标的位置。
    """
    lat_a, lon_a, wx_a, wy_a = anchor_a
    lat_b, lon_b, wx_b, wy_b = anchor_b

    kx = (wx_b - wx_a) / (lon_b - lon_a)
    ox = wx_a - kx * lon_a
    ky = (wy_b - wy_a) / (lat_b - lat_a)
    oy = wy_a - ky * lat_a

    def to_world(lat_deg, lon_deg):
        return kx * lon_deg + ox, ky * lat_deg + oy

    return to_world


# ---------------------------------------------------------------------------
# 4. 单位构造（严格匹配工作存档字段）
# ---------------------------------------------------------------------------
SENSOR_DEFAULT = [
    {"Tag": "", "Label": "FC L", "MinRange": 0.0, "MaxRange": 15.0,
     "StartAngle": 0.0, "ArcAngle": 0.0, "ArcColor": "&h00FFFF00",
     "IsFilled": False, "IsVisible": False},
    {"Tag": "", "Label": "M", "MinRange": 0.0, "MaxRange": 14.0,
     "StartAngle": 0.0, "ArcAngle": 0.0, "ArcColor": "&h00FFFF00",
     "IsFilled": False, "IsVisible": False},
    {"Tag": "", "Label": "S", "MinRange": 0.0, "MaxRange": 8.0,
     "StartAngle": 0.0, "ArcAngle": 0.0, "ArcColor": "&h00FFFF00",
     "IsFilled": False, "IsVisible": False},
]


def mk_unit(id_num_str, name, unit_type, x, y, side="Red", track_num=1000,
            speed_kt=None, course_deg=None, is_installation=False,
            text_tags_course_speed=None, sensor_array=False,
            position_time_created="1942-11-14 23:00:00",
            position_time_deleted="1943-11-14 23:00:00"):
    """
    构造 SimPlot 单位 dict（字段与桌面工作存档完全一致）。
    speed_kt / course_deg 传入则生成 Speed/Course(×1000) 等机动字段；
    is_installation=True 则不生成机动字段（机场/登陆点等无速度）。
    sensor_array=True 附加雷达 SensorArray（FC/M/S 三通道）。
    """
    unit = {
        "IdNum": id_num_str,
        "Side": side,
        "TrackNumber": track_num,
        "Name": name,
        "Number": 1,
        "UnitClass": "",
        "UnitType": unit_type,
        "X": int(round(x)),
        "Y": int(round(y)),
        "ShowSunk": False,
        "IsActiveRadar": False,
        "IsActiveSonar": False,
        "PositionTimeCreated": position_time_created,
        "PositionTimeDeleted": position_time_deleted,
    }
    if not is_installation:
        unit["Speed"] = int(round((speed_kt or 0) * 1000))
        unit["Course"] = int(round((course_deg or 0) * 1000))
        unit["Range"] = -100000
        unit["WpDistance"] = 0
        unit["PastWaypointArray1"] = {}
        unit["FutureWaypointArray1"] = {}
    unit["TextTags"] = {
        "TagAltitude": False,
        "TagCallsign": False,
        "TagClass": False,
        "TagCourseSpeed": bool(text_tags_course_speed) if text_tags_course_speed is not None else (not is_installation),
        "TagDepth": False,
        "TagName": True,
        "TagTrackNum": False,
        "TagUnitType": False,
        "AdditionalText": "",
    }
    if sensor_array:
        unit["SensorArray"] = [dict(s) for s in SENSOR_DEFAULT]
    return unit


def mk_waypoint(world_x, world_y, time_str):
    """PastWaypointArray1 元素: ["", x, y, 0,0, alt,0,0,0, 1, true, time]"""
    return ["", int(round(world_x)), int(round(world_y)), 0, 0, 0, 0, 0, 0, 1, True, time_str]


# ---------------------------------------------------------------------------
# 5. 完整场景存档构造（严格匹配工作存档顶层结构）
# ---------------------------------------------------------------------------
def make_scenario_save(scenario_name, units, map_file_name, time_str="1942-11-14 23:00:00",
                       turn_minutes=2, last_id=None, start_track=1000):
    """
    构造完整 Referee 存档 dict。
    units: [mk_unit(...) 产生的 dict, ...]
    map_file_name: 光栅地图 txt 文件名（如 "第三次所罗门海战.txt"）
    """
    objects = [u["IdNum"] for u in units]
    n = len(units)
    return {
        "File": "Referee",
        "SimPlot Version": "2.3",
        "IsIntegerFile": True,
        "Scenario": {
            "ScenarioName": scenario_name,
            "LastId": last_id if last_id is not None else n,
            "CurrentTrackNumber": start_track + n,
            "CurrentPlayerTrackNumber": 9000,
            "Phase": 0,
            "TypeOfMap": 1,
            "MapFileName": map_file_name,
        },
        "TypeOfGame": 0,
        "Time": {
            "CurrentTurnTime": time_str,
            "CurrentPositionTime": time_str,
            "CurrentTurnInterval": {"Minutes": turn_minutes, "Seconds": 0},
        },
        "Turns": [{
            "TurnTime": time_str,
            "TurnInterval": {"Minutes": turn_minutes, "Seconds": 0},
        }],
        "Overlays": {},
        "Objects": objects,
        "Units": units,
        "Formations": {},
    }


def write_scenario_save(data, out_path):
    """写出场景存档（ensure_ascii=False 保留中文，indent=1 便于 diff）"""
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return out_path
