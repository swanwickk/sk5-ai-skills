#!/usr/bin/env python3
"""
SK5 距离计算器 —— 从SimPlot存档或手动输入计算所有蓝→红距离

用法:
  # 从存档JSON计算（自动提取所有战斗单位）
  python3 sk5_distances.py savefile.json

  # 手动输入（逗号分隔: 名称,side,x,y,ts,ship_type,search_radar）
  python3 sk5_distances.py --manual \
    "Washington,Blue,137300,-543749,3,BB,CXAM-1" \
    "S.Dakota,Blue,236000,-543749,3,BB,SG/SC-2" \
    "Benham,Blue,-158800,-543749,0,DD,SG" \
    "川内,Red,-152099,212169,1,CL,None" \
    "敷波,Red,-95487,293020,0,DD,None"

  # 筛选输出
  python3 sk5_distances.py savefile.json --max-dist 20000
  python3 sk5_distances.py savefile.json --only-radar
"""
import json, math, sys

NM_TO_YD = 1852 / 0.9144  # 2025.37 yards per NM（国际海事标准）
JSON_SCALE = 100000

D3 = {
    -1:{0:15300,1:17100,2:18800,3:20900},
     0:{0:19000,1:21700,2:23400,3:25500},
     1:{0:23500,1:25200,2:27000,3:29000},
     2:{0:27800,1:29600,2:31300,3:33400},
     3:{0:31500,1:33200,2:34900,3:37000},
}

D2C8 = {
    -1:{0:3100,1:3400,2:3800,3:4300},
     0:{0:3900,1:4300,2:4700,3:5200},
     1:{0:4800,1:5200,2:5600,3:6000},
     2:{0:5800,1:6200,2:6600,3:7100},
     3:{0:6700,1:7000,2:7400,3:7900},
}

TYPE_TS = {'DD':-1,'CL':1,'CA':2,'CB':3,'BB':3,
           'Destroyer':-1,'Cruiser':1,'Battleship':3}

def d_nm(x1,y1,x2,y2):
    return math.sqrt((x1-x2)**2+(y1-y2)**2)

def parse_save(filepath):
    with open(filepath) as f:
        data = json.load(f)
    units = []
    for u in data.get('Units',[]):
        name,side = u.get('Name',''),u.get('Side','')
        spd,utype = u.get('Speed',0),u.get('UnitType','')
        if side not in ('Blue','Red'): continue
        if utype in ('Installation','Reference Point','Surface Ship'): continue
        if spd<=0 or not name: continue
        units.append({'name':name,'side':side,
            'x':u['X']/JSON_SCALE,'y':u['Y']/JSON_SCALE,'speed':spd//1000})
    return units

def parse_manual(args):
    units = []
    for a in args:
        p = a.split(',')
        if len(p)<6: print(f"跳过: {a}"); continue
        units.append({'name':p[0].strip(),'side':p[1].strip(),
            'x':int(p[2])/JSON_SCALE,'y':int(p[3])/JSON_SCALE,
            'ts':int(p[4]),'ship_type':p[5].strip(),
            'search_radar':p[6].strip() if len(p)>6 else 'None'})
    return units

def get_ts(u):
    return u.get('ts', TYPE_TS.get(u.get('ship_type',''),0))

def run(units, max_dist=None, only_radar=False):
    blue=[u for u in units if u['side']=='Blue']
    red=[u for u in units if u['side']=='Red']
    if not blue or not red: print("缺少蓝方或红方"); return

    pairs=[]
    for b in blue:
        for r in red:
            d=d_nm(b['x'],b['y'],r['x'],r['y'])
            dy=d*NM_TO_YD
            pairs.append((dy,d,b,r))
    pairs.sort()

    if max_dist: pairs=[p for p in pairs if p[0]<=max_dist]

    print(f"\n蓝→红 距离矩阵")
    print(f"{'蓝方':>14} {'红方':>8} {'码':>10} {'NM':>8}")
    for dy,d,b,r in pairs:
        print(f"  {b['name']:>12} → {r['name']:<6} {dy:>10,.0f} {d:>8.3f}")

    if not only_radar:
        # 目视（夜间Code7有月光）
        print(f"\n目视侦察（Code7）:")
        vis=False
        for dy,d,b,r in pairs:
            obs=get_ts(b); tgt=get_ts(r)
            rng=D2C8.get(obs,{}).get(tgt,4000)*0.90
            if r.get('speed',0)>29: rng*=1.20
            if dy<=rng:
                print(f"  ✓ {b['name']}→{r['name']}: {dy:,.0f}≤{rng:,.0f}")
                vis=True
        if not vis: print("  无接触")

    # 雷达
    print(f"\n雷达侦察（Search Radar + D3）:")
    rad=False
    for dy,d,b,r in pairs:
        sr=b.get('search_radar',b.get('ts',''))
        if 'search_radar' not in b and 'ts' not in b: continue
        if b.get('search_radar','None')=='None' and 'ts' not in b: continue
        sr_val=b.get('search_radar','')
        if sr_val=='None' or not sr_val: continue
        obs=get_ts(b); tgt=get_ts(r)
        d3=D3.get(obs,{}).get(tgt,0)
        if dy<=d3:
            print(f"  ✓ {b['name']}({sr_val})→{r['name']}: {dy:,.0f}≤D3[{obs}][{tgt}]={d3:,}")
            rad=True
    if not rad: print("  无接触")

if __name__=='__main__':
    if len(sys.argv)<2: print(__doc__); sys.exit(1)
    units=parse_manual(sys.argv[2:]) if sys.argv[1]=='--manual' else parse_save(sys.argv[1])
    if not units: print("无有效单位"); sys.exit(1)

    print("单位清单:")
    for u in units:
        sr=u.get('search_radar',''); ts=u.get('ts','?'); st=u.get('ship_type','')
        extra=f" [{sr}]" if sr and sr!='None' else ""
        spd=u.get('speed','')
        spd_str=f" {spd}kts" if spd else ""
        print(f"  [{u['side']}] {u['name']:>12} ({st}) TS={ts}{extra} ({u['x']:.3f},{u['y']:.3f}){spd_str}")

    max_d=int(sys.argv[sys.argv.index('--max-dist')+1]) if '--max-dist' in sys.argv else None
    only_r='--only-radar' in sys.argv
    run(units, max_d, only_r)
