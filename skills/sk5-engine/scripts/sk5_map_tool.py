import sys, os

def write_raster_map_txt(map_jpg_filename, scale_px_per_nm, out_txt_path):
    \"\"\"
    生成 SimPlot2 桌面版光栅地图配套 txt 文件。
    \"\"\"
    lines = [
        f\"MAP={map_jpg_filename}\",
        f\"SCALE={scale_px_per_nm:.4f}\"
    ]
    with open(out_txt_path, 'wb') as f:
        f.write(\"\\r\\n\".join(lines).encode('utf-8') + b\"\\r\\n\")

def px_to_world(px_x, px_y, scale_px_per_nm):
    \"\"\"
    图片像素坐标 -> SimPlot2 世界坐标换算
    \"\"\"
    world_x = (px_x / scale_px_per_nm) * 100000.0
    world_y = -(px_y / scale_px_per_nm) * 100000.0
    return int(round(world_x)), int(round(world_y))

def world_to_px(world_x, world_y, scale_px_per_nm):
    \"\"\"
    SimPlot2 世界坐标 -> 图片像素坐标换算
    \"\"\"
    px_x = (world_x / 100000.0) * scale_px_per_nm
    px_y = -(world_y / 100000.0) * scale_px_per_nm
    return px_x, px_y
