# -*- coding: utf-8 -*-
# GitHub Action 每日自动运行：抓取中彩网官方最新开奖，合并进 ssq.json
import urllib.request, json, datetime, re, os

URL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&pageNo=1&pageSize=30"

def fetch():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.cwl.gov.cn/"
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main():
    data = fetch()
    result = data.get("result") or []
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ssq.json")
    try:
        cur = json.load(open(path, encoding="utf-8"))
    except Exception:
        cur = {"updated": "", "source": "中彩网官方接口 findDrawNotice", "draws": []}
    existing = {d["code"]: d for d in cur.get("draws", [])}
    for x in result:
        code = str(x.get("code", ""))
        if not re.match(r"^20\d{4}$", code):
            continue
        reds = str(x.get("red", "")).split(",")
        if len([r for r in reds if r.strip()]) != 6:
            continue
        blue = str(x.get("blue", ""))
        if not blue.isdigit():
            continue
        existing[code] = {
            "code": code,
            "red": str(x.get("red", "")),
            "blue": blue.zfill(2),
            "date": str(x.get("date", ""))
        }
    draws = sorted(existing.values(), key=lambda d: d["code"], reverse=True)
    out = {
        "updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "source": "中彩网官方接口 findDrawNotice",
        "draws": draws
    }
    open(path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=0))
    print("更新后共", len(draws), "期，最新", draws[0]["code"] if draws else "无")

if __name__ == "__main__":
    main()
