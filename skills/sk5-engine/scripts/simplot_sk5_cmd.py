import math
import sk5_scn_tool

def calculate_sk5_move(current_x, current_y, current_heading, ordered_speed, ordered_heading, is_hard_rudder=False):
    diff = ordered_heading - current_heading
    diff = (diff + 180) % 360 - 180
    abs_diff = abs(diff)

    if abs_diff <= 15:
        coefficient = 1.0
    else:
        coefficient = 0.5 if is_hard_rudder else 0.75

    if abs_diff <= 10:
        segments = 1
    elif abs_diff <= 45:
        segments = 2
    elif abs_diff <= 90:
        segments = 3
    elif abs_diff <= 135:
        segments = 4
    else:
        segments = 5

    total_dist = (ordered_speed * coefficient / 30.0) * 100000.0
    dist_per_segment = total_dist / segments

    headings = []
    if segments == 1:
        headings.append(ordered_heading)
    else:
        # 首段前冲 (Advance)
        headings.append(current_heading)
        turning_segments = segments - 1
        angle_increment = diff / turning_segments
        for i in range(1, segments):
            headings.append(current_heading + angle_increment * i)

    waypoints = []
    cur_x, cur_y = current_x, current_y

    for hdg in headings:
        hdg_norm = hdg % 360
        rad = math.radians(hdg_norm)
        dx = dist_per_segment * math.sin(rad)
        dy = dist_per_segment * math.cos(rad)
        cur_x += dx
        cur_y += dy
        waypoints.append((cur_x, cur_y, hdg_norm))

    return waypoints, cur_x, cur_y, headings[-1]

def process_turn(unit_dict, ordered_speed, ordered_heading, is_hard_rudder, turn_time_str,
                 round_start_str=None):
    """turn_time_str=回合末时刻. 每腿时间戳在[round_start,turn_time]内等分展开并截断到整分；
    航迹点Course=执行航速x1000, Speed=该leg航向x1000（PC实测，与数组语义互换）"""
    from datetime import datetime, timedelta
    current_x = unit_dict.get("X", 0)
    current_y = unit_dict.get("Y", 0)
    current_heading = unit_dict.get("Course", 0) / 1000.0

    waypoints, end_x, end_y, end_course = calculate_sk5_move(
        current_x, current_y, current_heading, ordered_speed, ordered_heading, is_hard_rudder
    )

    unit_dict["X"] = int(round(end_x))
    unit_dict["Y"] = int(round(end_y))
    unit_dict["Course"] = int(end_course * 1000)
    unit_dict["Speed"] = int(ordered_speed * 1000)

    if "PastWaypointArray" not in unit_dict or not isinstance(unit_dict["PastWaypointArray"], list) or len(unit_dict["PastWaypointArray"]) == 0:
        unit_dict["PastWaypointArray"] = [
            sk5_scn_tool.create_waypoint(current_x, current_y, unit_dict.get("PositionTimeCreated", turn_time_str))
        ]

    n = len(waypoints)
    t_end = datetime.strptime(turn_time_str, "%Y-%m-%d %H:%M:%S")
    t_start = datetime.strptime(round_start_str, "%Y-%m-%d %H:%M:%S") if round_start_str else t_end
    for i, wp in enumerate(waypoints, 1):
        # ponytail: 截断到整分在腿数>3时可能撞戳, 届时改秒级
        t = (t_start + (t_end - t_start) * i / n).replace(second=0, microsecond=0)
        unit_dict["PastWaypointArray"].append(
            sk5_scn_tool.create_waypoint(wp[0], wp[1], t.strftime("%Y-%m-%d %H:%M:%S"),
                                         ordered_speed, wp[2])
        )

    return unit_dict
