import json, subprocess, time

CWL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=kl8&pageNo=1&pageSize=30"


def http_get(url, headers=None, retry=4):
    h = ["User-Agent: Mozilla/5.0"] + (headers or [])
    last = None
    for _ in range(retry):
        try:
            args = ["curl", "-s", "--max-time", "25"]
            for x in h:
                args += ["-H", x]
            args.append(url)
            r = subprocess.run(args, capture_output=True, text=True)
            if not r.stdout.strip():
                raise ValueError("空响应")
            return json.loads(r.stdout)
        except Exception as e:
            last = e
            time.sleep(2)
    raise last


def parse_cwl(j):
    out = []
    try:
        rows = j["result"]
    except Exception:
        return out
    for d in rows:
        try:
            reds = [int(x) for x in d["red"].split(",")]
            if len(reds) != 20 or any(n < 1 or n > 80 for n in reds):
                continue
            date = d.get("date", "").split("(")[0]
            out.append({"issue": str(d["code"]), "reds": reds, "date": date})
        except Exception:
            pass
    return out


def main():
    path = "kuaile8.json"
    data = json.load(open(path, encoding="utf-8"))
    existing = {x["issue"]: x for x in data.get("draws", [])}
    added = 0
    try:
        rows = parse_cwl(http_get(CWL, ["Referer: https://www.cwl.gov.cn/"]))
        for d in rows:
            if d["issue"] not in existing:
                existing[d["issue"]] = d
                added += 1
        source = "www.cwl.gov.cn (name=kl8)"
    except Exception as e:
        print("中彩网 失败:", repr(e))
        source = "中彩网拉取失败，使用内置数据"

    new_draws = sorted(existing.values(), key=lambda x: x["issue"], reverse=True)
    data["draws"] = new_draws
    data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    data["source"] = source
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("新增", added, "期 | 共", len(new_draws), "期 | 最新", new_draws[0]["issue"])


if __name__ == "__main__":
    main()
