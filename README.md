# TVBox 配置源

> 个人自用TVBox配置，仅供学习交流使用

## 配置地址

**Gitee（国内推荐）：**
```
https://raw.giteeusercontent.com/bochaibo/tvbox/raw/master/store.json
```

**GitHub（备用）：**
```
https://gh-proxy.com/https://raw.githubusercontent.com/yczzwy/tvbox/main/store.json
```

## 源列表

### 采集API（type=1，支持搜索）
| 名称 | 说明 |
|------|------|
| 三六资源 | 首页菜单，资源丰富 |
| 如意采集 | 可搜索 |
| 非凡采集 | 可搜索 |
| 天堂旧 | 可搜索 |
| lbapi采集 | 可搜索 |
| fhapi采集 | 可搜索 |
| 魔都采集 | 可搜索 |
| iQIYI采集 | 可搜索 |
| 其他13个 | 可浏览 |

### JS/PY源（type=3，浏览专用）
| 名称 | 说明 |
|------|------|
| 360影视 | drpy源 |
| 大师兄影视 | drpy源 |
| 电影先生 | drpy源 |
| 豆瓣 | drpy源 |
| 爱看 | drpy源 |
| 荐片 | drpy源 |
| 奇优 | drpy源 |
| 影探 | drpy源 |
| 采集之王 | drpy源 |

### 直播源
| 名称 | 频道数 | 说明 |
|------|--------|------|
| 央视卫视 | 688 | io365源，央视+卫视+地方 |
| 综合直播(咪咕) | 310 | 咪咕源 |
| tv | 624 | nxog源 |

## 文件说明

```
├── store.json              # 多仓配置入口
├── merged_part1.json       # 主配置文件
├── live_io365.txt          # io365直播源（央视卫视）
├── live_migu.txt           # 咪咕直播源
├── live_cctv_weishi.txt    # iptv-org直播源（备用）
├── tools/
│   └── tvbox_auto_update.py  # 源验证更新工具
└── sources/                # 源文件目录
```

## 工具使用

```bash
# 验证并更新源
cd tools
python3 tvbox_auto_update.py
```

## 更新日志

- 2026-06-26: 初始化配置，添加采集API和JS/PY源
- 2026-06-26: 添加央视卫视直播源（688频道）
- 2026-06-26: 同步到GitHub（yczzwy/tvbox）

## 免责声明

1. **本仓库仅供个人学习交流使用**，不提供任何资源存储服务
2. **所有资源均来自互联网**，本仓库不对其内容负责
3. **请于24小时内删除**，如有侵权请联系删除
4. **本仓库与任何第三方无关**，不代表任何组织或平台的观点
5. **使用本配置产生的一切后果由使用者自行承担**

## 许可证

MIT License

---

*最后更新: 2026-06-26*
