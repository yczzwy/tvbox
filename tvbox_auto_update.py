#!/usr/bin/env python3
"""
TVBox源自动验证更新工具 (Debug模式)
功能：
1. 验证已知采集API的可用性
2. 验证已知直播源的可用性
3. 按评分排序选出top5
4. 保存为本地子仓JSON文件
5. 更新store.json指向本地文件
"""

import json
import os
import subprocess
import sys
from datetime import datetime

TVBOX_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_FILE = os.path.join(TVBOX_DIR, 'store.json')
LOCAL_SOURCES_DIR = os.path.join(TVBOX_DIR, 'local_sources')

# 待验证的采集API
APIS_TO_TEST = [
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

# 待验证的直播源
LIVES_TO_TEST = [
    ("综合直播", "https://ghfast.top/https://raw.githubusercontent.com/develop202/migu_video/refs/heads/main/interface.txt"),
    ("Kimentanm", "https://ghfast.top/https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u"),
    ("歌手直播", "https://mgtv.ottiptv.cc/mglist.m3u"),
    ("虎牙一起看", "https://sub.ottiptv.cc/huyayqk.m3u"),
    ("斗鱼一起看", "https://sub.ottiptv.cc/douyuyqk.m3u"),
    ("B站直播", "https://sub.ottiptv.cc/bililive.m3u"),
    ("YY轮播", "https://sub.ottiptv.cc/yylunbo.m3u"),
    ("zbds直播", "https://live.zbds.top/tv/iptv4.m3u"),
    ("iptv-org", "https://iptv-org.github.io/iptv/index.country.m3u"),
]


def test_api(name, url, keyword='蜘蛛侠'):
    """测试采集API"""
    print(f"  测试: {name}", end=" ")
    
    # 测试list
    list_url = f"{url}?ac=list"
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', '8', list_url],
            capture_output=True, text=True, timeout=12)
        data = json.loads(r.stdout)
        total = data.get('total', 0)
        if total > 0:
            # 测试搜索
            search_url = f"{url}?ac=detail&wd={keyword}"
            r2 = subprocess.run(['curl', '-sL', '--max-time', '8', search_url],
                capture_output=True, text=True, timeout=12)
            try:
                data2 = json.loads(r2.stdout)
                search_count = len(data2.get('list', []))
            except:
                search_count = 0
            
            searchable = search_count > 0
            if searchable:
                print(f"✓ 可搜索 ({total}条)")
            else:
                print(f"△ 可浏览 ({total}条)")
            
            return {
                'name': name, 'url': url,
                'total': total, 'search': search_count,
                'searchable': searchable,
                'score': total + search_count * 10 + (1000000 if searchable else 0)
            }
        else:
            print("✗ 无数据")
    except:
        print("✗ 失败")
    return None


def test_live(name, url):
    """测试直播源"""
    print(f"  测试: {name}", end=" ")
    try:
        result = subprocess.run(
            ['curl', '-sL', '--max-time', '10', url],
            capture_output=True, text=True, timeout=15
        )
        content = result.stdout
        lines = content.split('\n')
        channels = sum(1 for l in lines if l.strip() and not l.startswith('#') and ('m3u8' in l or 'http' in l))
        has_cctv = 'CCTV' in content.upper()
        has_weishi = '卫视' in content
        
        if channels > 0:
            score = channels
            if has_cctv: score *= 2
            if has_weishi: score *= 2
            
            suffix = []
            if has_cctv: suffix.append('央视')
            if has_weishi: suffix.append('卫视')
            info = f"({channels}ch-{'+'.join(suffix)})" if suffix else f"({channels}ch)"
            print(f"✓ {info}")
            
            return {
                'name': f"{name}{info}", 'url': url,
                'channels': channels, 'cctv': has_cctv, 'weishi': has_weishi,
                'score': score
            }
        else:
            print("✗ 无频道")
    except:
        print("✗ 失败")
    return None


def save_local_sources(api_results, live_results, top_n=5):
    """保存top N源为本地JSON文件"""
    print("\n" + "=" * 50)
    print(f"保存top {top_n}源为本地文件")
    print("=" * 50)
    
    os.makedirs(LOCAL_SOURCES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存采集API源
    api_top = api_results[:top_n]
    api_config = {
        'spider': '',
        'sites': [
            {'key': f"api_{i}", 'name': api['name'], 'type': 1,
             'api': api['url'], 'searchable': 1, 'quickSearch': 1, 'filterable': 1}
            for i, api in enumerate(api_top)
        ]
    }
    api_file = os.path.join(LOCAL_SOURCES_DIR, f'api_top{top_n}_{timestamp}.json')
    with open(api_file, 'w', encoding='utf-8') as f:
        json.dump(api_config, f, ensure_ascii=False, indent=2)
    
    print(f"\n采集API源: {os.path.basename(api_file)}")
    for api in api_top:
        print(f"  - {api['name']} ({api['total']}条)")
    
    # 保存直播源
    live_top = live_results[:top_n]
    live_config = {
        'lives': [
            {'name': live['name'], 'type': 0, 'url': live['url'], 'playerType': 2}
            for live in live_top
        ]
    }
    live_file = os.path.join(LOCAL_SOURCES_DIR, f'live_top{top_n}_{timestamp}.json')
    with open(live_file, 'w', encoding='utf-8') as f:
        json.dump(live_config, f, ensure_ascii=False, indent=2)
    
    print(f"\n直播源: {os.path.basename(live_file)}")
    for live in live_top:
        print(f"  - {live['name']}")
    
    return api_file, live_file


def update_store_json(api_file, live_file):
    """更新store.json"""
    print("\n" + "=" * 50)
    print("更新store.json")
    print("=" * 50)
    
    with open(STORE_FILE, 'r', encoding='utf-8') as f:
        store = json.load(f)
    
    new_entries = [
        {"name": "新发现采集API", "url": f"file://{api_file}"},
        {"name": "新发现直播源", "url": f"file://{live_file}"}
    ]
    
    existing_urls = [u['url'] for u in store.get('urls', [])]
    added = 0
    for entry in new_entries:
        if entry['url'] not in existing_urls:
            store['urls'].append(entry)
            added += 1
    
    with open(STORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(store, f, ensure_ascii=False, separators=(',', ':'))
    
    print(f"添加 {added} 个新仓库，当前共 {len(store['urls'])} 个")


def main():
    print("=" * 60)
    print("TVBox源自动验证更新工具 (Debug模式)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试采集API
    print("\n" + "=" * 50)
    print("验证采集API")
    print("=" * 50)
    api_results = []
    for name, url in APIS_TO_TEST:
        result = test_api(name, url)
        if result:
            api_results.append(result)
    
    api_results.sort(key=lambda x: x['score'], reverse=True)
    
    # 测试直播源
    print("\n" + "=" * 50)
    print("验证直播源")
    print("=" * 50)
    live_results = []
    for name, url in LIVES_TO_TEST:
        result = test_live(name, url)
        if result:
            live_results.append(result)
    
    live_results.sort(key=lambda x: x['score'], reverse=True)
    
    # 保存top 5
    api_file, live_file = save_local_sources(api_results, live_results, top_n=5)
    
    # 更新store.json
    update_store_json(api_file, live_file)
    
    # 汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)
    searchable = [a for a in api_results if a.get('searchable')]
    print(f"采集API: {len(api_results)}可用 (可搜索: {len(searchable)})")
    print(f"直播源: {len(live_results)}可用")
    print(f"\n文件保存在: {LOCAL_SOURCES_DIR}")
    print("\n操作完成！")


if __name__ == '__main__':
    main()
