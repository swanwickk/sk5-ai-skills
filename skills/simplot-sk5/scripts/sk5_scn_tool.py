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
        "PastWaypointArray1": {},  # 空数组必须写 {}（写 [] 桌面版会崩溃）
        "FutureWaypointArray1": {},
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

def create_waypoint(x, y, time_str):
    return ["", int(round(x)), int(round(y)), 0, 0, 0, 0, 0, 0, 1, True, time_str]
