import json, subprocess, time

HUI = "https://api.huiniao.top/interface/home/lotteryHistory?type=qlc&page=1&limit=30"


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


def parse_hui(j):
    out = []
    try:
        rows = j["data"]["data"]["list"]
    except Exception:
        return out
    for d in rows:
        try:
            reds = [int(d[k]) for k in ["one", "two", "three", "four", "five", "six", "seven"]]
            spec = int(d["eight"])
            if len(reds) != 7 or any(n < 1 or n > 30 for n in reds) or spec < 1 or spec > 30:
                continue
            out.append({"issue": str(d["code"]), "reds": reds, "special": spec, "date": d.get("day", "")})
        except Exception:
            pass
    return out


def main():
    path = "qilecai.json"
    data = json.load(open(path, encoding="utf-8"))
    existing = {x["issue"]: x for x in data.get("draws", [])}
    added = 0
    try:
        rows = parse_hui(http_get(HUI))
        for d in rows:
            if d["issue"] not in existing:
                existing[d["issue"]] = d
                added += 1
        source = "api.huiniao.top (type=qlc)"
    except Exception as e:
        print("huiniao 失败:", repr(e))
        source = "huiniao拉取失败，使用内置数据"

    new_draws = sorted(existing.values(), key=lambda x: x["issue"], reverse=True)
    data["draws"] = new_draws
    data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    data["source"] = source
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("新增", added, "期 | 共", len(new_draws), "期 | 最新", new_draws[0]["issue"])


if __name__ == "__main__":
    main()
