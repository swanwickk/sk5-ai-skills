import json

def read_scn(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_scn(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

def mk_unit(id_num_str, name, unit_type, x, y, course, speed, side="Red", track_num=1000,
            unit_class="", text_tags=None, position_time_created="",
            position_time_deleted=""):
    return {
        "IdNum": id_num_str,
        "Side": side,
        "TrackNumber": track_num,
        "Name": name,
        "Number": 1,
        "UnitClass": unit_class,
        "UnitType": unit_type,
        "X": int(round(x)),
        "Y": int(round(y)),
        "ShowSunk": False,
        "IsActiveRadar": False,
        "IsActiveSonar": False,
        "PositionTimeCreated": position_time_created,
        "PositionTimeDeleted": position_time_deleted,
        "Speed": int(speed * 1000),
        "Course": int(course * 1000),
        "Range": -100000,
        "PastWaypointArray": {},  # 空集合必须写 {}（写 [] 桌面版会崩溃；键名无后缀，PC实测）
        "FutureWaypointArray": {},
        "TextTags": text_tags or {
            "TagAltitude": False,
            "TagCallsign": False,
            "TagClass": False,
            "TagCourseSpeed": True,
            "TagDepth": False,
            "TagName": True,
            "TagTrackNum": False,
            "TagUnitType": False,
            "AdditionalText": ""
        }
    }

def create_waypoint(x, y, time_str, speed_kt=0, leg_heading=0):
    # PC对象格式（2026-09-03实测，键序按字母序）：Course=执行航速x1000, Speed=该leg航向x1000（与数组语义互换）
    return {"AltitudeDepth": 0, "Ascent": 0, "AssignedAltDepth": 0, "Course": int(round(speed_kt * 1000)),
            "Descent": 0, "IsTurnTime": True, "Name": "", "Number": 1,
            "PositionTime": time_str, "Speed": int(round(leg_heading * 1000)),
            "X": int(round(x)), "Y": int(round(y))}
