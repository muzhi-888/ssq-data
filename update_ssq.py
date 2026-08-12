# -*- coding: utf-8 -*-
# GitHub Action 每日自动运行：抓取开奖并合并进 ssq.json
# 数据源：huiniao.top（海外/国内均可访问，免费）为主，中彩网官方接口兜底（仅国内网络可用）
import urllib.request, json, datetime, re, os

HUI_NIAO = "https://api.huiniao.top/interface/home/lotteryHistory?type=ssq&page=1&limit=60"
CWL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&pageNo=1&pageSize=60"

def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def parse_huiniao(data):
    out = []
    for x in (data.get("data", {}).get("data", {}).get("list", []) or []):
        try:
            reds = [str(x["one"]), str(x["two"]), str(x["three"]),
                    str(x["four"]), str(x["five"]), str(x["six"])]
        except Exception:
            continue
        if len([r for r in reds if r.strip()]) != 6:
            continue
        code = str(x.get("code", ""))
        if not re.match(r"^20\d{4}$", code):
            continue
        blue = str(x.get("seven", ""))
        if not blue.isdigit():
            continue
        out.append({"code": code, "red": ",".join(reds),
                    "blue": blue.zfill(2), "date": str(x.get("day", ""))})
    return out

def parse_cwl(data):
    out = []
    for x in (data.get("result") or []):
        code = str(x.get("code", ""))
        if not re.match(r"^20\d{4}$", code):
            continue
        reds = str(x.get("red", "")).split(",")
        if len([r for r in reds if r.strip()]) != 6:
            continue
        blue = str(x.get("blue", ""))
        if not blue.isdigit():
            continue
        out.append({"code": code, "red": str(x.get("red", "")),
                    "blue": blue.zfill(2), "date": str(x.get("date", ""))})
    return out

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssq.json")
    try:
        cur = json.load(open(path, encoding="utf-8"))
    except Exception:
        cur = {"updated": "", "source": "", "draws": []}
    existing = {d["code"]: d for d in cur.get("draws", [])}
    sources, fetched = [], []
    try:
        req = urllib.request.Request(HUI_NIAO, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
        print("HUINIAO_HTTP", getattr(r, "status", "?"), "LEN", len(raw))
        print("HUINIAO_RAW", raw[:600])
        data = json.loads(raw)
        fetched = parse_huiniao(data)
        if fetched:
            sources.append("huiniao.top")
    except Exception as e:
        print("huiniao 失败:", repr(e))
    if not fetched:
        try:
            fetched = parse_cwl(http_get(CWL, {"User-Agent": "Mozilla/5.0",
                                               "Referer": "https://www.cwl.gov.cn/"}))
            if fetched:
                sources.append("cwl.gov.cn")
        except Exception as e:
            print("cwl 失败:", repr(e))
    for d in fetched:
        existing[d["code"]] = d
    draws = sorted(existing.values(), key=lambda d: d["code"], reverse=True)
    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "source": " + ".join(sources) if sources else "无可用源",
        "draws": draws
    }
    open(path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=0))
    print("来源:", sources, "| 更新后共", len(draws), "期，最新",
          draws[0]["code"] if draws else "无")

if __name__ == "__main__":
    main()
