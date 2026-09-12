#!/usr/bin/env python3
"""Fill booking info (official URL, lead time, price, caveats) into the NZ trip."""
import json
import sys

sys.path.insert(0, "/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp")
from mcp import call, session  # noqa: E402

TRIP = 8

# name-substring -> patch for the place
PLACE_PATCHES = {
    "暗夜保护区观星": {
        "website": "https://www.darkskyproject.co.nz/",
        "notes": "🎫 预订官网：darkskyproject.co.nz（唯一持牌运营方）\n⏰ 建议提前：3–4 周，旺季更早\n💰 参考价：以官网为准（预算 NZ$400 / 2 人）\n⚠️ 9 月底夜间 0–5℃，羽绒服+帽子+手套必备；手电用红光模式",
    },
    "库克山机场（INFLITE 直升机）": {
        "website": "https://www.mtcookskiplanes.com/",
        "notes": "🎫 预订官网：mtcookskiplanes.com（Mount Cook Ski Planes & Helicopters by INFLITE）\n⏰ 建议提前：尽早锁定上午场；天气取消可当场改期\n💰 参考价：Tasman Taster 25min NZ$379／Glacier Highlights 45min NZ$649／Grand Circle 55min NZ$7949→749/人\n⚠️ 高度依赖天气，建议与冰川船互为备份（直升机上午、冰川船下午）",
    },
    "隐士酒店 The Hermitage": {
        "website": "https://www.hermitage.co.nz/experience/glacier-explorers",
        "notes": "🎫 预订官网：hermitage.co.nz/experience/glacier-explorers\n⏰ 旺季提前 2–3 个月；9 月底相对好订但也别拖\n💰 参考价：成人（15+）NZ$209/人，10 月 1 日起 NZ$219；全程约 2h45\n⚠️ 出发前 30min 到隐士酒店一楼 Activities Desk 报到；含 1.5km 碎石坡步行，穿防滑鞋；湖上风大，羽绒服+墨镜+防晒",
    },
    "Omarama Hot Tubs": {
        "website": "https://www.hottubsomarama.co.nz/",
        "notes": "🎫 预订官网：hottubsomarama.co.nz（在线订位）\n⏰ 需提前订位\n💰 参考价：约 NZ$120 / 90min 私人木桶（2 人）\n⚠️ 顺路泡 1h 解乏，库克山→瓦纳卡途经",
    },
    "The Sauna Wānaka": {
        "website": "https://www.thesaunawanaka.co.nz/",
        "notes": "🎫 预订官网：thesaunawanaka.co.nz（在线订时段）\n⏰ 需提前网上订，60–70min 一场\n💰 参考价：私场约 NZ$220/h（最多 7 人，第三方价，以官网为准）\n⚠️ Outlet 湖畔，80–90℃ 木柴桑拿 + 冰湖跳水；前一晚若住 Lake Hāwea 可改 The Secret Sauna（NZ$32/人/h，15min 车程）",
    },
    "Real Guns 射击": {
        "website": "https://www.realguns.nz/",
        "notes": "🎫 预订官网：realguns.nz（1081 Cardrona Valley Road）\n⏰ 提前 15min 签到；需预约\n💰 参考价：以官网为准（预算 NZ$300）\n⚠️ 必须带护照或新西兰驾照原件；穿平底闭趾鞋、不要穿迷彩；基础套餐 20 发 .22 + 10 发霰弹打飞盘，可现场加购",
    },
    "TSS Earnslaw": {
        "website": "https://www.realnz.com/en/experiences/tss-earnslaw-walter-peak-experiences/",
        "notes": "🎫 预订官网：realnz.com（唯一运营方）\n⏰ 建议订上午班次（约 10:00 出发），下午接 Skyline\n💰 参考价：以官网为准（预算 NZ$700）\n⚠️ 含往返蒸汽船（单程 45min）+ 剪羊毛/牧羊犬表演 + 茶点，全程约 3h45；农场只能坐船到，无公路",
    },
    "Skyline Queenstown": {
        "website": "https://queenstown.skyline.co.nz/book-now/",
        "notes": "🎫 预订官网：queenstown.skyline.co.nz/book-now\n⏰ 线上买「Gondola + Luge」比现场便宜；Luge 票含首次乘坐时段，别订太晚\n💰 参考价：Gondola+3 Luge 成人 NZ$99（高峰）/NZ$69（标准）\n⚠️ 山顶观景台朝西，9 月底日落约 19:45，18:30 上山最稳；停车紧张，停 Lakeview/Boundary St 步行 8min",
    },
    "Deer Park Heights": {
        "website": "https://deerparkheights.co.nz/book-now/",
        "notes": "🎫 预订官网：deerparkheights.co.nz/book-now\n⏰ 最多可提前 30 天订，每天最多 80 台车，常售罄\n💰 参考价：NZ$75/车（含司机，最多 8 座）\n⚠️ 预约必须填车牌号→租车拿到车牌后再订；只能开车进（禁步行/骑行/出租车/Uber）；18:00 前必须离场，超时罚 NZ$100；带一枚 NZ$2 硬币买饲料；入口已搬新位置，别只信 Google Maps 老导航",
    },
    "Dart Stables 骑马": {
        "name": "Lighthorse Adventures 骑马（格林奇诺）",
        "website": "https://www.lighthorseadventures.com/",
        "notes": "🎫 预订官网：lighthorseadventures.com（2 Swamp Road, Glenorchy）\n⏰ 需提前订\n💰 参考价：以官网为准（预算 NZ$500）\n⚠️ ⚠️ Dart Stables 已停业，原址现为 Lighthorse Adventures；Dart 河谷 20min 体验到全天线路；备选 High Country Horses（highcountryhorses.nz）；初学者选短程体验",
    },
    "Shotover Jet": {
        "website": "https://www.shotoverjet.com/prices/",
        "notes": "🎫 预订官网：shotoverjet.com（每日 9:30–16:00 发船）\n⏰ 建议订 09:30–11:00 场次，之后才有时间购物+还车\n💰 参考价：成人 NZ$199 / 儿童（5–15）NZ$109 / 家庭（2大2小）NZ$507\n⚠️ 全程约 25min 含 360° 旋转；提前 30min 签到（Arthurs Point 河基自驾）或选 Station Building 免费班车（约 10:00/11:00/12:00/14:00/15:00，订票时 Transport Required 选 Yes）",
    },
    "Mangatepopo 起点停车场": {
        "website": "https://www.doc.govt.nz/parks-and-recreation/places-to-go/central-north-island/places/tongariro-national-park/things-to-do/tracks/tongariro-alpine-crossing/",
        "notes": "🎫 DOC 官方页：doc.govt.nz（Tongariro Alpine Crossing）\n⏰ 10/5 在强制预约季（10/26–4/30）之前：坐接驳车的 DOC 预约免费且必须；自驾无需\n💰 参考价：DOC 预约免费\n⚠️ 5–10 月仍属冬季路线：Red Crater 段可能有冰雪，属「专家级」路段；出发前一晚查 DOC 路况+NIWA 预报，天气差果断改 Tama Lakes；A→B 单线 19.4km，两端相距 20km",
    },
    "Ketetahi 终点": {
        "website": "https://www.tongariroexpeditions.com/",
        "notes": "🎫 接驳预订：tongariroexpeditions.com（10 月起 6:30/7:30/8:30 发车）\n⏰ 订完 DOC 预约再订接驳（要填 DOC 编号）\n💰 参考价：单程 NZ$65/人起\n⚠️ 返程接驳约 13:00–16:00 在 Ketetahi 等；13:00 前必须过 Red Crater",
    },
    "怀赫科岛 Waiheke Island": {
        "website": "https://www.fullers.co.nz/booking/",
        "notes": "🎫 渡轮预订：fullers.co.nz/booking（Fullers360，40min 直达）\n⏰ 机动日方案，提前 1–2 天订即可；也可现场购票\n💰 参考价：现场成人约 NZ$46.50 单程\n⚠️ 岛上 20+ 酒庄 + 沙滩，可租车或 hop-on hop-off 巴士，一日游刚好",
    },
    "圣马修教堂 St Matthew's": {
        "website": "https://www.stmatthews.nz/",
        "notes": "⛪ 官网：stmatthews.nz（132–134 Hobson St, Auckland CBD）\n⏰ 仪式提前 30–45min 到场；花艺/摄影/牧师档期提前一天再确认\n⚠️ 周末市中心停车极难，全家 Uber 或订附近 Wilson 停车楼；Albert Park 是备选外景地",
    },
}

# todo name-substring -> patch
TODO_PATCHES = {
    "Dark Sky Project 观星预订": {
        "description": "官网 https://www.darkskyproject.co.nz/ ｜ 提前 3–4 周 ｜ 9 月底夜間 0–5℃ 带羽绒服，红光手电",
    },
    "库克山直升机 INFLITE 预订": {
        "description": "官网 https://www.mtcookskiplanes.com/ ｜ 25min NZ$379 起，订上午场 ｜ 天气取消可改期，与冰川船互为备份",
    },
    "塔斯曼冰川船": {
        "description": "官网 https://www.hermitage.co.nz/experience/glacier-explorers ｜ 成人 NZ$209（10/1 起 219）｜ 出发前 30min 隐士酒店一楼报到，防滑鞋",
    },
    "TSS 蒸汽船": {
        "description": "官网 https://www.realnz.com/en/experiences/tss-earnslaw-walter-peak-experiences/ ｜ 订约 10:00 班次 ｜ 全程 3h45，农场只通船",
    },
    "Skyline 缆车": {
        "description": "官网 https://queenstown.skyline.co.nz/book-now/ ｜ Gondola+3 Luge 成人 NZ$99（高峰）/69（标准）｜ Luge 含首乘时段，别订太晚",
    },
    "Deer Park Heights 小鹿公园预约": {
        "description": "官网 https://deerparkheights.co.nz/book-now/ ｜ 最多提前 30 天订，NZ$75/车 ｜ 必须填车牌号→租车后再订；18:00 前离场，超时罚 NZ$100",
    },
    "格林奇诺骑马 Dart Stables 预订": {
        "name": "格林奇诺骑马预订（Lighthorse Adventures）",
        "description": "⚠️ Dart Stables 已停业。改订 https://www.lighthorseadventures.com/（原址，Dart 河谷）；备选 https://highcountryhorses.nz/ ｜ 初学者选短程体验",
    },
    "Shotover Jet 预订": {
        "description": "官网 https://www.shotoverjet.com/prices/ ｜ 成人 NZ$199，9:30–16:00 发船 ｜ 订 09:30–11:00 场；免费班车在订票时选 Transport Required=Yes",
    },
    "Real Guns 射击预约": {
        "description": "官网 https://www.realguns.nz/ ｜ 提前 15min 签到 ｜ 必须带护照/驾照原件；平底闭趾鞋，不穿迷彩",
    },
    "The Sauna Wānaka 桑拿订时段": {
        "description": "官网 https://www.thesaunawanaka.co.nz/ ｜ 私场约 NZ$220/h（至 7 人，第三方价）｜ Outlet 湖畔，60–70min 一场",
    },
    "Omarama Hot Tubs 温泉订位": {
        "description": "官网 https://www.hottubsomarama.co.nz/ ｜ 约 NZ$120/90min 私人木桶（2 人）｜ 库克山→瓦纳卡顺路",
    },
    "汤加里罗：DOC 官网订步道时段": {
        "description": "DOC 页 https://www.doc.govt.nz/parks-and-recreation/places-to-go/central-north-island/places/tongariro-national-park/things-to-do/tracks/tongariro-alpine-crossing/ ｜ 坐接驳车需免费 DOC 预约（10/5 在 10/26 强制季之前）｜ 接驳 https://www.tongariroexpeditions.com/ 单程 NZ$65 起，先订 DOC 再订接驳 ｜ 5–10 月属冬季路线，查冰雪路况",
    },
}

# budget name-substring -> patch
BUDGET_PATCHES = {
    "格林奇诺骑马 Dart Stables": {
        "name": "格林奇诺骑马（Lighthorse Adventures）",
        "note": "⚠️ Dart Stables 已停业，改 Lighthorse Adventures（原址）或 High Country Horses；价格以官网为准",
    },
    "库克山直升机": {
        "note": "mtcookskiplanes.com：25min NZ$379 / 45min NZ$649 / 55min NZ$749 每人，订上午场",
    },
    "塔斯曼冰川船": {
        "note": "hermitage.co.nz：成人 NZ$209/人（10/1 起 NZ$219），2 人约 NZ$418",
    },
    "Skyline 缆车": {
        "note": "queenstown.skyline.co.nz：Gondola+3 Luge 成人 NZ$99（高峰）/NZ$69（标准），线上买便宜",
    },
    "Shotover Jet": {
        "note": "shotoverjet.com：成人 NZ$199 / 儿童 NZ$109 / 家庭 NZ$507，订 09:30–11:00 场",
    },
}

# Day 7 (id 39) notes: fix the Dart Stables line
DAY7_NEW_ITEM3 = "3. 格林奇诺骑马：Dart Stables 已停业，原址现为 Lighthorse Adventures（lighthorseadventures.com），Dart 河谷 20min 体验到全天线路；备选 High Country Horses（highcountryhorses.nz）。需提前订，初学者选短程体验。"


def main():
    s = session()
    summary = call("get_trip_summary", {"tripId": TRIP}, sid=s, rid=1)

    def find(lst, key, field="name"):
        for it in lst:
            if key in it.get(field, ""):
                return it
        raise KeyError(key)

    # places
    places = [a["place"] for d in summary["days"] for a in d["assignments"]]
    seen = set()
    for key, patch in PLACE_PATCHES.items():
        p = find(places, key)
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        body = {"tripId": TRIP, "placeId": p["id"]}
        body.update(patch)
        call("update_place", body, sid=s, rid=100 + len(seen))
        print(f"place {p['id']} [{p['name']}] <- {patch.get('name', key)}", file=sys.stderr)

    # todos
    for i, (key, patch) in enumerate(TODO_PATCHES.items()):
        t = find(summary["todos"], key)
        body = {"tripId": TRIP, "itemId": t["id"]}
        body.update(patch)
        call("update_todo", body, sid=s, rid=300 + i)
        print(f"todo {t['id']} [{t['name'][:20]}]", file=sys.stderr)

    # budget
    for i, (key, patch) in enumerate(BUDGET_PATCHES.items()):
        b = find(summary["budget"]["items"], key)
        body = {"tripId": TRIP, "itemId": b["id"]}
        body.update(patch)
        call("update_budget_item", body, sid=s, rid=500 + i)
        print(f"budget {b['id']} [{b['name'][:20]}]", file=sys.stderr)

    # day 7 notes
    day7 = find(summary["days"], "2026-09-30", "date")
    notes = day7["notes"]
    old = notes[notes.find("3. 格林奇诺骑马"):notes.find("4. 皇后镇→格林奇诺")].strip()
    new = notes.replace(old, DAY7_NEW_ITEM3)
    call("update_day", {"tripId": TRIP, "dayId": day7["id"], "notes": new}, sid=s, rid=700)
    print(f"day7 notes updated", file=sys.stderr)

    print("DONE")


if __name__ == "__main__":
    main()
