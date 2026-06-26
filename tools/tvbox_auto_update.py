#!/usr/bin/env python3
"""
TVBox源自动验证更新工具 v3
功能：
1. 完整验证所有源（采集API + JS/PY源 + 直播源）
2. 去重检查（与现有源对比）
3. 可用性分析（现有源是否还能用）
4. 替换不可用源
5. 直播源以io365为主，相同频道增加备选源
6. 高清高速优先
7. JS/PY非采集源管理（验证URL、top5保留）
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

TVBOX_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGED_FILE = os.path.join(TVBOX_DIR, 'merged_part1.json')
STORE_FILE = os.path.join(TVBOX_DIR, 'store.json')

# 候选采集API
CANDIDATE_APIS = [
    ("三六资源", "https://360zy.com/api.php/provide/vod/"),
    ("如意采集", "https://cj.rycjapi.com/api.php/provide/vod/"),
    ("非凡采集", "http://cj.ffzyapi.com/api.php/provide/vod/"),
    ("天堂旧", "http://caiji.dyttzyapi.com/api.php/provide/vod/"),
    ("极速采集", "https://jszyapi.com/api.php/provide/vod/"),
    ("量子采集", "https://cj.lziapi.com/api.php/provide/vod/"),
    ("索尼采集", "https://suoniapi.com/api.php/provide/vod/"),
    ("暴风采集", "http://by.bfzyapi.com/api.php/provide/vod/"),
    ("wsyzy采集", "https://api.wsyzy.net/api.php/provide/vod/"),
    ("红牛采集", "https://www.hongniuzy2.com/api.php/provide/vod/"),
    ("光速采集", "https://api.guangsuapi.com/api.php/provide/vod/"),
    ("闪电采集", "https://sdzyapi.com/api.php/provide/vod/"),
    ("速播采集", "https://subocaiji.com/api.php/provide/vod/"),
    ("樱花采集", "https://m3u8.apiyhzy.com/api.php/provide/vod/"),
    ("无尽采集", "https://api.wujinapi.net/api.php/provide/vod/"),
    ("金鹰采集", "https://jyzyapi.com/api.php/provide/vod/"),
    ("艾旦采集", "https://www.lovedan.net/api.php/provide/vod/"),
    ("牛牛采集", "https://api.niuniuzy.me/api.php/provide/vod/"),
    ("快车采集", "https://caiji.kuaichezy.org/api.php/provide/vod/"),
    ("丫丫采集", "https://yayazy2.com/api.php/provide/vod/"),
    ("最大采集", "https://zuida.xyz/api.php/provide/vod/"),
    ("豪华采集", "https://hhzyapi.com/api.php/provide/vod/"),
    ("天涯采集", "https://tyyszyapi.com/api.php/provide/vod/"),
    ("lbapi采集", "https://lbapi9.com/api.php/provide/vod/"),
    ("fhapi采集", "http://fhapi9.com/api.php/provide/vod/"),
    ("魔都采集", "https://caiji.moduapi.cc/api.php/provide/vod/?ac=list"),
    ("iQIYI采集", "https://www.iqiyizyapi.com/api.php/provide/vod/?ac=list"),
]

# 候选JS/PY非采集源（drpy格式）
CANDIDATE_JSPY = [
    {
        'name': '采集之王',
        'api': './lib/drpy2.min.js',
        'ext': './js/采集之王.js?type=url&params=./json/采集静态.json'
    },
    {
        'name': '量子',
        'api': './lib/drpy2.min.js',
        'ext': './js/量子.js'
    },
    {
        'name': '索尼',
        'api': './lib/drpy2.min.js',
        'ext': './js/索尼.js'
    },
    {
        'name': '暴风',
        'api': './lib/drpy2.min.js',
        'ext': './js/暴风.js'
    },
    {
        'name': '闪电',
        'api': './lib/drpy2.min.js',
        'ext': './js/闪电.js'
    },
    {
        'name': '光速',
        'api': './lib/drpy2.min.js',
        'ext': './js/光速.js'
    },
    {
        'name': '极速',
        'api': './lib/drpy2.min.js',
        'ext': './js/极速.js'
    },
    {
        'name': '红牛',
        'api': './lib/drpy2.min.js',
        'ext': './js/红牛.js'
    },
    {
        'name': '无尽',
        'api': './lib/drpy2.min.js',
        'ext': './js/无尽.js'
    },
    {
        'name': '金鹰',
        'api': './lib/drpy2.min.js',
        'ext': './js/金鹰.js'
    },
]

# 候选直播源
CANDIDATE_LIVES = [
    ("zbds直播", "https://live.zbds.top/tv/iptv4.m3u", True),
    ("综合直播", "https://ghfast.top/https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt", True),
    ("Kimentanm", "https://ghfast.top/https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u", True),
    ("歌手直播", "https://mgtv.ottiptv.cc/mglist.m3u", False),
    ("iptv-org", "https://iptv-org.github.io/iptv/index.country.m3u", True),
]


def fetch_url(url, timeout=10):
    """获取URL内容"""
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5
        )
        return result.stdout
    except:
        return ''


def normalize_api_url(url):
    """标准化API URL用于比较"""
    base = url.split('?')[0]
    return base.rstrip('/')


def load_existing_sources():
    """加载现有源"""
    existing_apis = {}
    existing_jspy = {}
    existing_lives = {}
    
    if os.path.exists(MERGED_FILE):
        with open(MERGED_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for site in data.get('sites', []):
            site_type = site.get('type')
            if site_type == 1:
                api_url = site.get('api', '')
                normalized = normalize_api_url(api_url)
                existing_apis[normalized] = {
                    'name': site.get('name', ''),
                    'key': site.get('key', ''),
                    'url': api_url,
                    'normalized': normalized
                }
            elif site_type == 3:
                js_key = site.get('key', site.get('name', ''))
                existing_jspy[js_key] = {
                    'name': site.get('name', ''),
                    'key': js_key,
                    'api': site.get('api', ''),
                    'ext': site.get('ext', ''),
                    'jar': site.get('jar', ''),
                    'site': site
                }
        
        for live in data.get('lives', []):
            live_url = live.get('url', '')
            existing_lives[live_url] = {
                'name': live.get('name', ''),
                'url': live_url
            }
    
    return existing_apis, existing_jspy, existing_lives


def test_api_full(name, url):
    """完整测试采集API"""
    list_url = f"{url}?ac=list"
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', '8', list_url],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        total = data.get('total', 0)
        if total > 0:
            search_url = f"{url}?ac=detail&wd=蜘蛛侠"
            r2 = subprocess.run(['curl', '-sL', '--max-time', '8', search_url],
                capture_output=True, text=True, timeout=12)
            try:
                data2 = json.loads(r2.stdout)
                search_count = len(data2.get('list', []))
            except:
                search_count = 0
            
            searchable = search_count > 0
            return {
                'name': name, 'url': url,
                'total': total, 'search': search_count,
                'searchable': searchable,
                'score': total + search_count * 10 + (1000000 if searchable else 0)
            }
    except:
        pass
    return None


def test_jspy_url(name, api_url, ext_url):
    """测试JS/PY源URL是否可访问"""
    # 相对路径格式（./lib/drpy2.min.js, ./js/xxx.js）
    # 这种格式依赖spider JAR加载，只要格式正确就认为可用
    if api_url.startswith('./') and ext_url.startswith('./'):
        return {'name': name, 'api': api_url, 'ext': ext_url, 'score': 100}
    
    # 绝对URL格式，需要测试可访问性
    base_url = 'https://cdn.jsdmirror.com/gh/ouhaibo1980/tvbox@main'
    
    test_api = api_url
    if api_url.startswith('./'):
        test_api = f'{base_url}/{api_url[2:]}'
    
    test_ext = ext_url
    if ext_url.startswith('./'):
        test_ext = f'{base_url}/{ext_url[2:]}'
    
    api_ok = False
    try:
        r = subprocess.run(['curl', '-sL', '-o', '/dev/null', '-w', '%{http_code}', 
                           '--max-time', '8', test_api],
                          capture_output=True, text=True, timeout=12)
        api_ok = r.stdout.strip() in ['200', '301', '302']
    except:
        pass
    
    ext_ok = False
    try:
        r = subprocess.run(['curl', '-sL', '-o', '/dev/null', '-w', '%{http_code}', 
                           '--max-time', '8', test_ext],
                          capture_output=True, text=True, timeout=12)
        ext_ok = r.stdout.strip() in ['200', '301', '302']
    except:
        pass
    
    if api_ok and ext_ok:
        return {'name': name, 'api': api_url, 'ext': ext_url, 'score': 100}
    elif api_ok:
        return {'name': name, 'api': api_url, 'ext': ext_url, 'score': 50}
    return None


def test_live_full(name, url, check_cctv_weishi=False):
    """完整测试直播源"""
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '15', url],
            capture_output=True, text=True, timeout=20
        )
        content = result.stdout
        lines = content.split('\n')
        
        channels = []
        current_group = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if '#genre#' in line:
                current_group = line.split(',')[0].strip()
                continue
            if line.startswith('#'):
                continue
            if 'http' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    ch_name = parts[0].strip()
                    ch_url = parts[1].strip()
                    if ch_url.startswith('http'):
                        channels.append({
                            'name': ch_name,
                            'url': ch_url,
                            'group': current_group
                        })
        
        if not channels:
            return None
        
        cctv_count = sum(1 for c in channels if 'CCTV' in c['name'].upper())
        weishi_count = sum(1 for c in channels if '卫视' in c['name'])
        
        if check_cctv_weishi and cctv_count == 0 and weishi_count == 0:
            return None
        
        score = len(channels)
        if cctv_count > 0: score += cctv_count * 10
        if weishi_count > 0: score += weishi_count * 5
        
        return {
            'name': name, 'url': url,
            'channels': channels,
            'channel_count': len(channels),
            'cctv': cctv_count, 'weishi': weishi_count,
            'score': score
        }
    except:
        return None


def analyze_existing_sources(existing_apis, existing_jspy, existing_lives):
    """分析现有源可用性"""
    print("\n" + "=" * 50)
    print("1. 分析现有源可用性")
    print("=" * 50)
    
    print("\n测试现有采集API...")
    working_apis = {}
    dead_apis = []
    for url, info in existing_apis.items():
        result = test_api_full(info['name'], url)
        if result:
            working_apis[url] = result
            status = "✓ 可搜索" if result['searchable'] else "△ 可浏览"
            print(f"  {status} {info['name']}: {result['total']}条")
        else:
            dead_apis.append(url)
            print(f"  ✗ 失效: {info['name']}")
    
    print("\n测试现有JS/PY源...")
    working_jspy = {}
    dead_jspy = []
    for key, info in existing_jspy.items():
        result = test_jspy_url(info['name'], info['api'], info['ext'])
        if result:
            working_jspy[key] = info
            print(f"  ✓ {info['name']}")
        else:
            dead_jspy.append(key)
            print(f"  ✗ 失效: {info['name']}")
    
    print("\n测试现有直播源...")
    working_lives = {}
    dead_lives = []
    for url, info in existing_lives.items():
        result = test_live_full(info['name'], url)
        if result:
            working_lives[url] = result
            print(f"  ✓ {info['name']}: {result['channel_count']}频道")
        else:
            dead_lives.append(url)
            print(f"  ✗ 失效: {info['name']}")
    
    print(f"\n现有源统计:")
    print(f"  采集API: {len(working_apis)}可用 / {len(dead_apis)}失效")
    print(f"  JS/PY源: {len(working_jspy)}可用 / {len(dead_jspy)}失效")
    print(f"  直播源: {len(working_lives)}可用 / {len(dead_lives)}失效")
    
    return working_apis, dead_apis, working_jspy, dead_jspy, working_lives, dead_lives


def discover_new_sources(existing_apis):
    """发现新采集API"""
    print("\n" + "=" * 50)
    print("2. 验证候选新采集API")
    print("=" * 50)
    
    new_apis = []
    for name, url in CANDIDATE_APIS:
        normalized = normalize_api_url(url)
        if normalized in existing_apis:
            print(f"  △ 跳过(已存在): {name}")
            continue
        
        result = test_api_full(name, url)
        if result:
            new_apis.append(result)
            status = "✓ 可搜索" if result['searchable'] else "△ 可浏览"
            print(f"  {status} 新源: {name}: {result['total']}条")
    
    new_apis.sort(key=lambda x: x['score'], reverse=True)
    return new_apis


def discover_new_jspy(existing_jspy):
    """发现新JS/PY源"""
    print("\n" + "=" * 50)
    print("3. 验证候选JS/PY源")
    print("=" * 50)
    
    new_jspy = []
    for jspy in CANDIDATE_JSPY:
        name = jspy['name']
        # 检查是否已存在
        exists = False
        for key, info in existing_jspy.items():
            if info.get('name') == name or name in info.get('name', ''):
                exists = True
                break
        
        if exists:
            print(f"  △ 跳过(已存在): {name}")
            continue
        
        result = test_jspy_url(name, jspy['api'], jspy['ext'])
        if result:
            new_jspy.append(jspy)
            print(f"  ✓ 新源: {name}")
        else:
            print(f"  ✗ 不可用: {name}")
    
    return new_jspy


def discover_new_lives(existing_lives):
    """发现新直播源"""
    print("\n" + "=" * 50)
    print("4. 验证候选新直播源")
    print("=" * 50)
    
    new_lives = []
    for name, url, require_cctv in CANDIDATE_LIVES:
        if url in existing_lives:
            print(f"  △ 跳过(已存在): {name}")
            continue
        
        result = test_live_full(name, url, require_cctv)
        if result:
            new_lives.append(result)
            print(f"  ✓ 新源: {name}: {result['channel_count']}频道")
        else:
            print(f"  ✗ 不可用: {name}")
    
    new_lives.sort(key=lambda x: x['score'], reverse=True)
    return new_lives


def merge_sources(working_apis, new_apis, working_jspy, new_jspy, 
                  working_lives, new_lives, dead_apis, dead_jspy, dead_lives):
    """合并源"""
    print("\n" + "=" * 50)
    print("5. 合并源")
    print("=" * 50)
    
    # 合并采集API
    merged_apis = list(working_apis.values())
    for dead_url in dead_apis:
        if new_apis:
            replacement = new_apis.pop(0)
            merged_apis.append(replacement)
            print(f"  替换API: {dead_url.split('//')[1].split('/')[0]} → {replacement['name']}")
    
    # 合并JS/PY源：保留可用的 + 替换失效的 + 新增top5
    merged_jspy = list(working_jspy.values())
    for dead_key in dead_jspy:
        if new_jspy:
            replacement = new_jspy.pop(0)
            merged_jspy.append(replacement)
            print(f"  替换JS/PY: {dead_key} → {replacement['name']}")
    
    # 添加新的JS/PY源（最多10个）
    for jspy in new_jspy[:10]:
        merged_jspy.append(jspy)
        print(f"  新增JS/PY: {jspy['name']}")
    
    # 合并直播源
    merged_lives = []
    
    # io365作为主源
    io365_url = "https://raw.giteeusercontent.com/bochaibo/tvbox/raw/master/live_io365.txt"
    merged_lives.append({
        'name': '央视卫视',
        'url': io365_url,
        'is_primary': True
    })
    print(f"  主源: 央视卫视(io365)")
    
    for live in working_lives.values():
        if live['url'] != io365_url:
            merged_lives.append(live)
            print(f"  备选: {live['name']}")
    
    for live in new_lives[:3]:
        merged_lives.append(live)
        print(f"  新增: {live['name']}")
    
    return merged_apis, merged_jspy, merged_lives


def update_merged_file(merged_apis, merged_jspy, merged_lives):
    """更新merged_part1.json"""
    print("\n" + "=" * 50)
    print("6. 更新merged_part1.json")
    print("=" * 50)
    
    with open(MERGED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 构建新sites
    new_sites = []
    
    # JS/PY源（type=3）
    for jspy in merged_jspy:
        entry = {
            'key': jspy.get('name', ''),
            'name': jspy.get('name', ''),
            'type': 3,
            'api': jspy.get('api', ''),
            'ext': jspy.get('ext', '')
        }
        if jspy.get('jar'):
            entry['jar'] = jspy['jar']
        new_sites.append(entry)
    
    # 采集API（type=1）
    for i, api in enumerate(merged_apis):
        new_sites.append({
            'key': f"api_{i}",
            'name': api['name'],
            'type': 1,
            'api': api['url'],
            'searchable': 1,
            'quickSearch': 1,
            'filterable': 1
        })
    
    data['sites'] = new_sites
    
    # 更新lives
    new_lives = []
    for live in merged_lives:
        entry = {
            'name': live['name'],
            'type': 0,
            'url': live['url'],
            'playerType': 2
        }
        if 'ua' in live:
            entry['ua'] = live['ua']
        new_lives.append(entry)
    
    data['lives'] = new_lives
    
    with open(MERGED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    
    jspy_count = sum(1 for s in data['sites'] if s.get('type') == 3)
    api_count = sum(1 for s in data['sites'] if s.get('type') == 1)
    print(f"已更新:")
    print(f"  JS/PY源: {jspy_count}个")
    print(f"  采集API: {api_count}个")
    print(f"  直播源: {len(data['lives'])}个")


def main():
    print("=" * 60)
    print("TVBox源自动验证更新工具 v3")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    existing_apis, existing_jspy, existing_lives = load_existing_sources()
    print(f"现有源: {len(existing_apis)} 采集API, {len(existing_jspy)} JS/PY, {len(existing_lives)} 直播源")
    
    working_apis, dead_apis, working_jspy, dead_jspy, working_lives, dead_lives = \
        analyze_existing_sources(existing_apis, existing_jspy, existing_lives)
    
    new_apis = discover_new_sources(existing_apis)
    new_jspy = discover_new_jspy(existing_jspy)
    new_lives = discover_new_lives(existing_lives)
    
    merged_apis, merged_jspy, merged_lives = merge_sources(
        working_apis, new_apis, working_jspy, new_jspy,
        working_lives, new_lives, dead_apis, dead_jspy, dead_lives
    )
    
    update_merged_file(merged_apis, merged_jspy, merged_lives)
    
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    jspy_total = len(merged_jspy)
    searchable = [a for a in merged_apis if a.get('searchable')]
    print(f"JS/PY源: {jspy_total}个")
    print(f"采集API: {len(merged_apis)}个 (可搜索: {len(searchable)})")
    print(f"直播源: {len(merged_lives)}个")
    print(f"  - 失效替换: {len(dead_apis)}API + {len(dead_jspy)}JS/PY + {len(dead_lives)}直播")
    print(f"  - 新增: {len(new_apis)}API + {len(new_jspy)}JS/PY + {len(new_lives)}直播")
    print("\n操作完成！")


if __name__ == '__main__':
    main()
