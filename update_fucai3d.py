import json, subprocess, time, os

HUI = "https://api.huiniao.top/interface/home/lotteryHistory?type=fcsd&page=1&limit=30"
CWL = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=3d&pageNo=1&pageSize=30"


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
            nums = [int(d["one"]), int(d["two"]), int(d["three"])]
            if any(n < 0 or n > 9 for n in nums):
                continue
            out.append({"code": str(d["code"]), "red": ",".join(map(str, nums)),
                        "blue": "", "date": d.get("day", "")})
        except Exception:
            pass
    return out


def parse_cwl(j):
    out = []
    try:
        rows = j["result"]
    except Exception:
        return out
    for d in rows:
        try:
            nums = [int(x) for x in d["red"].split(",")]
            if len(nums) != 3 or any(n < 0 or n > 9 for n in nums):
                continue
            date = d.get("date", "").split("(")[0]
            out.append({"code": str(d["code"]), "red": ",".join(map(str, nums)),
                        "blue": "", "date": date})
        except Exception:
            pass
    return out


def main():
    path = "fucai3d.json"
    data = json.load(open(path, encoding="utf-8"))
    existing = {x["code"]: x for x in data["draws"]}
    added = 0
    sources = []
    # 主源 huinitao（海外 CI 可访问）
    try:
        rows = parse_hui(http_get(HUI))
        if rows:
            sources.append("huinitao")
            for d in rows:
                if d["code"] not in existing:
                    existing[d["code"]] = d
                    added += 1
    except Exception as e:
        print("huinitao 失败:", repr(e))
    # 兜底 中彩网（仅本地/中国网络可达，Actions 可能 403，仅作补充）
    try:
        rows2 = parse_cwl(http_get(CWL, ["Referer: https://www.cwl.gov.cn/"]))
        if rows2:
            sources.append("中彩网")
            for d in rows2:
                if d["code"] not in existing:
                    existing[d["code"]] = d
                    added += 1
    except Exception as e:
        print("中彩网 失败:", repr(e))
    new_draws = sorted(existing.values(), key=lambda x: x["code"], reverse=True)
    data["draws"] = new_draws
    data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    data["source"] = "api.huiniao.top (type=fcsd) + 中彩网兜底"
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print("来源:", sources, "| 新增", added, "期 | 共", len(new_draws), "期 | 最新", new_draws[0]["code"])


if __name__ == "__main__":
    main()
