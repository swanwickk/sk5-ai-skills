import sys, json, math

NM_TO_YD = 2025.37

def distance_yards(x1, y1, x2, y2):
    dx = (x2 - x1) / 100000.0
    dy = (y2 - y1) / 100000.0
    return math.hypot(dx, dy) * NM_TO_YD

def distance_nm(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1) / 100000.0

def bearing_degrees(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
