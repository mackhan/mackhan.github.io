"""使用统计：把埋点数据仓（mackhan/pa-stats）的 JSONL 聚合成统计页要的数字。

数据格式见 tauri-commerce 的 analytics 模块：每行一个事件
    {"app", "install_id", "kind", "app_version", "os", "ts"}
文件布局 data/<应用>/<年-月>.jsonl。

统计页是**公开**的，所以这里只产出聚合数字（设备数、活跃数、版本 / 系统分布、按天活跃），
任何安装 id 都不会出现在输出里。

只用标准库，兼容 Python 3.9。
"""
import datetime
import json
import os

TZ = datetime.timezone(datetime.timedelta(hours=8))   # 按北京时间切天
FIELDS = ("app", "install_id", "kind", "app_version", "os", "ts")


def load_events(data_dir):
    """读 data_dir/<应用>/*.jsonl 的全部事件；脏行、字段不全的行、接通测试事件（*_test）直接丢。"""
    out = []
    if not os.path.isdir(data_dir):
        return out
    for app in sorted(os.listdir(data_dir)):
        adir = os.path.join(data_dir, app)
        if not os.path.isdir(adir):
            continue
        for fn in sorted(os.listdir(adir)):
            if not fn.endswith(".jsonl"):
                continue
            with open(os.path.join(adir, fn), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(e, dict) or any(k not in e for k in FIELDS):
                        continue
                    if str(e["kind"]).endswith("_test"):
                        continue
                    out.append(e)
    return out


def _day(ts):
    return datetime.datetime.fromtimestamp(int(ts), TZ).date()


def _vkey(v):
    parts = []
    for x in str(v).split("-")[0].split("."):
        parts.append(int(x) if x.isdigit() else 0)
    return tuple(parts)


def _ranked(counter, key=None):
    """{名字: 数} → [[名字, 数], ...]，数多的在前；同数按 key（默认名字）排"""
    items = list(counter.items())
    items.sort(key=lambda kv: (-kv[1], key(kv[0]) if key else kv[0]))
    return [[k, v] for k, v in items]


def aggregate(events, today=None, days=30):
    """按应用聚合。today 用来定「最近 N 天」的窗口，默认今天（北京时间）。"""
    today = today or datetime.datetime.now(TZ).date()
    by_app = {}
    for e in events:
        by_app.setdefault(e["app"], []).append(e)

    apps = []
    for name, es in by_app.items():
        last_seen, latest = {}, {}            # install_id -> 最后活跃日 / (ts, 版本, 系统)
        per_day = {}
        kinds = {}
        for e in es:
            iid, ts, d = e["install_id"], int(e["ts"]), _day(e["ts"])
            if iid not in last_seen or d > last_seen[iid]:
                last_seen[iid] = d
            if iid not in latest or ts >= latest[iid][0]:
                latest[iid] = (ts, str(e["app_version"]), str(e["os"]))
            per_day.setdefault(d, set()).add(iid)
            kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1

        def active(n):
            start = today - datetime.timedelta(days=n - 1)
            return sum(1 for d in last_seen.values() if d >= start)

        versions, oses = {}, {}
        for _, ver, os_ in latest.values():
            versions[ver] = versions.get(ver, 0) + 1
            oses[os_] = oses.get(os_, 0) + 1
        daily = []
        for i in range(days - 1, -1, -1):
            d = today - datetime.timedelta(days=i)
            daily.append([d.isoformat(), len(per_day.get(d, ()))])

        apps.append({
            "name": name,
            "devices": len(last_seen),
            "active7": active(7),
            "active30": active(30),
            "events": len(es),
            # 版本新的排前面（同设备数时），看得出升级进度
            "versions": sorted(_ranked(versions), key=lambda kv: (-kv[1], tuple(-x for x in _vkey(kv[0])))),
            "os": _ranked(oses),
            "kinds": _ranked(kinds),
            "daily": daily,
        })
    apps.sort(key=lambda a: (-a["devices"], a["name"]))
    return {"generated": today.isoformat(), "days": days, "apps": apps}
