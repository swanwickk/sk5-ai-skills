#!/usr/bin/env python3
"""
SK5 战舰本地冷数据库查询工具 (SK5 Database CLI)
用法：
  python3 sk5_db.py list [--country ...] [--hull ...] [--team ...]
  python3 sk5_db.py get <舰名> [--format md|json|card] [--out /path]
  python3 sk5_db.py search <全文关键词>
  python3 sk5_db.py query [--min-gun 14] [--min-dp 1000] [--country IJN]
  python3 sk5_db.py stats
"""
import sys, os, sqlite3, json, argparse

DB_PATH = "./database/ships.db"
BASE_DIR = "./database"

def get_conn():
    if not os.path.exists(DB_PATH):
        print(f"Error: 数据库文件不存在 {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cmd_list(args):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT id, name_zh, name_en, country, hull_type, class_code, year_variant, total_dp, max_speed, main_gun_mount, team FROM ships WHERE 1=1"
    params = []
    if args.country:
        query += " AND (country LIKE ? OR country LIKE ?)"
        params.extend([f"%{args.country}%", f"%{args.country}%"])
    if args.hull:
        query += " AND hull_type = ?"
        params.append(args.hull.upper())
    if args.team:
        query += " AND team LIKE ?"
        params.append(f"%{args.team}%")
    query += " ORDER BY country, hull_type, total_dp DESC, name_zh"
    c.execute(query, params)
    rows = c.fetchall()
    
    print(f"\n🚢 检索到 {len(rows)} 艘战舰：\n")
    print(f"{'ID':<3} | {'中文舰名':<6} | {'英文舰名':<16} | {'国别':<6} | {'舰型':<4} | {'总DP':<5} | {'航速':<4} | {'主炮配置':<24} | {'所属编制'}")
    print("-" * 95)
    for r in rows:
        print(f"{r['id']:<3} | {r['name_zh']:<6} | {r['name_en']:<16} | {r['country']:<6} | {r['hull_type']:<4} | {r['total_dp']:<5} | {r['max_speed']:<4} | {r['main_gun_mount']:<24} | {r['team']}")
    print()

def cmd_get(args):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM ships WHERE name_zh = ? OR name_en LIKE ? OR name_zh LIKE ? LIMIT 1", (args.name, f"%{args.name}%", f"%{args.name}%"))
    row = c.fetchone()
    if not row:
        print(f"❌ 未找到战舰: {args.name}", file=sys.stderr)
        sys.exit(1)
    
    if args.format == "md":
        content = row['md_content']
    elif args.format == "json":
        content = row['json_content']
    else: # card summary
        card = json.loads(row['json_content'])
        print(f"\n================ 战舰速览: {row['name_zh']} ({row['name_en']}) ================")
        print(f"国别: {row['country']} | 舰型: {row['hull_type']} | 舰级: {row['class_code']} | 年代: {row['year_variant']}")
        print(f"总DP: {row['total_dp']} | 航速: {row['max_speed']} KTS | 目标尺寸: {row['target_size']} | DCR: {row['dcr']}")
        print(f"主炮: {row['main_gun_mount']} (口径 {card['primary_gun']['bore_inch']}\", DF {card['primary_gun']['damage_factor']}, ROF {card['primary_gun']['max_rof']})")
        print(f"装甲 (1H~9V): {list(card['armor_matrix_inches'].values())}")
        print(f"MD 文件: {row['md_filename']}")
        print("====================================================================\n")
        return

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已保存至 {args.out}")
    else:
        print(content)

def cmd_search(args):
    conn = get_conn()
    c = conn.cursor()
    query = """
    SELECT s.id, s.name_zh, s.name_en, s.country, s.hull_type, s.class_code, s.total_dp, s.main_gun_mount, s.team
    FROM ships_fts f
    JOIN ships s ON f.rowid = s.id
    WHERE ships_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """
    c.execute(query, (args.keyword, args.limit))
    rows = c.fetchall()
    print(f"\n🔍 全文搜索 '{args.keyword}' 命中 {len(rows)} 条结果：\n")
    print(f"{'ID':<3} | {'中文舰名':<6} | {'英文舰名':<16} | {'国别':<6} | {'舰型':<4} | {'总DP':<5} | {'主炮配置':<24} | {'所属编制'}")
    print("-" * 85)
    for r in rows:
        print(f"{r['id']:<3} | {r['name_zh']:<6} | {r['name_en']:<16} | {r['country']:<6} | {r['hull_type']:<4} | {r['total_dp']:<5} | {r['main_gun_mount']:<24} | {r['team']}")
    print()

def cmd_query(args):
    conn = get_conn()
    c = conn.cursor()
    sql = "SELECT id, name_zh, name_en, country, hull_type, total_dp, max_speed, main_gun_mount, main_gun_caliber FROM ships WHERE 1=1"
    params = []
    if args.country:
        sql += " AND country LIKE ?"
        params.append(f"%{args.country}%")
    if args.hull:
        sql += " AND hull_type = ?"
        params.append(args.hull.upper())
    if args.min_gun:
        sql += " AND main_gun_caliber >= ?"
        params.append(float(args.min_gun))
    if args.min_dp:
        sql += " AND total_dp >= ?"
        params.append(int(args.min_dp))
    if args.min_speed:
        sql += " AND max_speed >= ?"
        params.append(float(args.min_speed))
    if args.radar:
        sql += " AND radar_fc_bonus > 0"
    sql += " ORDER BY main_gun_caliber DESC, total_dp DESC"
    c.execute(sql, params)
    rows = c.fetchall()
    print(f"\n📊 复合条件筛选命中 {len(rows)} 艘战舰：\n")
    print(f"{'ID':<3} | {'中文舰名':<6} | {'英文舰名':<16} | {'国别':<6} | {'舰型':<4} | {'总DP':<5} | {'航速':<4} | {'主炮':<6} | {'主炮配置'}")
    print("-" * 80)
    for r in rows:
        print(f"{r['id']:<3} | {r['name_zh']:<6} | {r['name_en']:<16} | {r['country']:<6} | {r['hull_type']:<4} | {r['total_dp']:<5} | {r['max_speed']:<4} | {r['main_gun_caliber']}″   | {r['main_gun_mount']}")
    print()

def cmd_stats(args):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT count(*) as total, count(distinct country) as countries, count(distinct hull_type) as hulls FROM ships")
    base = c.fetchone()
    print(f"\n📦 SK5 战舰冷数据库统计：")
    print(f"• 战舰总数: {base['total']} 艘")
    print(f"• 国家数量: {base['countries']} 个")
    print(f"• 舰种数量: {base['hulls']} 种\n")
    
    print("按国家与舰型分布：")
    c.execute("SELECT country, hull_type, count(*) as cnt, sum(total_dp) as sum_dp FROM ships GROUP BY country, hull_type ORDER BY country, cnt DESC")
    for r in c.fetchall():
        print(f"  - {r['country']:<6} {r['hull_type']:<4}: {r['cnt']:>2} 艘 (总DP: {r['sum_dp']:>6})")
    
    print("\n按参战编制分布：")
    c.execute("SELECT team, count(*) as cnt FROM ships GROUP BY team ORDER BY cnt DESC")
    for r in c.fetchall():
        print(f"  - {r['team']:<10}: {r['cnt']:>2} 艘")
    print()

def main():
    parser = argparse.ArgumentParser(description="SK5 战舰冷数据库管理与查询工具")
    subparsers = parser.add_subparsers(dest="subcmd", help="子命令")

    # list
    p_list = subparsers.add_parser("list", help="列出战舰")
    p_list.add_argument("--country", "-c", help="按国别筛选")
    p_list.add_argument("--hull", "-u", help="按舰型筛选(BB/CA/CL/DD)")
    p_list.add_argument("--team", "-t", help="按编制分队筛选")

    # get
    p_get = subparsers.add_parser("get", help="提取指定战舰船表")
    p_get.add_argument("name", help="中文或英文舰名")
    p_get.add_argument("--format", "-f", choices=["md", "json", "card"], default="card", help="输出格式(md/json/card)")
    p_get.add_argument("--out", "-o", help="输出到文件路径")

    # search
    p_search = subparsers.add_parser("search", help="全文关键词搜索")
    p_search.add_argument("keyword", help="搜索关键词")
    p_search.add_argument("--limit", "-n", type=int, default=20, help="返回条数上限")

    # query
    p_query = subparsers.add_parser("query", help="复合数值条件筛选")
    p_query.add_argument("--country", "-c", help="国别")
    p_query.add_argument("--hull", "-u", help="舰型")
    p_query.add_argument("--min-gun", "-g", type=float, help="最小主炮口径(英寸)")
    p_query.add_argument("--min-dp", "-d", type=int, help="最小总DP")
    p_query.add_argument("--min-speed", "-s", type=float, help="最小航速(节)")
    p_query.add_argument("--radar", "-r", action="store_true", help="要求配备火控雷达")

    # stats
    subparsers.add_parser("stats", help="数据库统计摘要")

    args = parser.parse_args()
    if not args.subcmd:
        parser.print_help()
        sys.exit(0)

    if args.subcmd == "list":
        cmd_list(args)
    elif args.subcmd == "get":
        cmd_get(args)
    elif args.subcmd == "search":
        cmd_search(args)
    elif args.subcmd == "query":
        cmd_query(args)
    elif args.subcmd == "stats":
        cmd_stats(args)

if __name__ == "__main__":
    main()
