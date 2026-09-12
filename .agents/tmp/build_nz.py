#!/usr/bin/env python3
"""Build the New Zealand trip (id 8) for user sakyaer from the xlsx plan."""
import json
import os
import sys

sys.path.insert(0, "/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp")
from mcp import call, session  # noqa: E402

TRIP = 8
DAY = {  # date -> day id
    "09-24": 33, "09-25": 34, "09-26": 35, "09-27": 36, "09-28": 37, "09-29": 38,
    "09-30": 39, "10-01": 40, "10-02": 41, "10-03": 42, "10-04": 43, "10-05": 44,
    "10-06": 45, "10-07": 46,
}
CAT = {"hotel": 1, "restaurant": 2, "attraction": 3, "shopping": 4, "transport": 5,
       "activity": 6, "cafe": 7, "beach": 8, "nature": 9, "other": 10}

# (day key, title, day notes)
DAYS = [
    ("09-24", "奥克兰 · 落地 · 试婚纱 · 市区", """【落地第一天：先办事+倒时差】
1. 11:15 落地奥克兰国际航站楼，入境+取行李约 1h；国际→国内航站楼步行约 10min（绿线步道）。次日 JQ227 从国内航站楼 D 出发，今晚先办线上值机。
2. 奥克兰机场假日酒店有免费机场班车；住市区的话优先 Uber 或 AT 公交，市中心停车极贵。
3. 试婚纱建议放下午（上午先补觉倒时差，飞了 11h+ 状态很差，试纱拍照容易肿）。
4. 市区 2h 逛完：Queen St → Britomart → Viaduct Harbour 海港边。新西兰餐厅 21:00 后基本打烊，晚饭别拖太晚。
5. 顺手在市区超市（Countdown / New World）买电话卡和零食，比机场便宜 30% 以上。"""),

    ("09-25", "奥克兰 ✈️ 基督城 → 蒂卡波湖", """【南岛第一天：时差+长途驾驶，量力而行】
1. 07:15 JQ227 奥克兰→基督城，落地取车（驾照原件 + NZTA 翻译件必须随身，租车公司会复印存档）。
2. 基督城→蒂卡波湖约 3h / 230km。SH8 路况好，但新西兰是左行，注意：单车道桥（One Lane Bridge）、环岛必须让右、让行标志一律停车。
3. 沿途 Geraldine / Fairlie 加油+午餐；Fairlie Bakehouse 是南岛最出名的派店，排队也值。
4. 约翰山（Mt John）自驾上山有 Road User Fee（约 NZ$8/车，门口自助刷卡），山顶俯瞰整片蒂卡波湖；Astro Café 白天营业，是 9 月底看库克山视角最好的咖啡馆。
5. 好牧羊人教堂免费，17:00 后旅行团散去，光线也最好。
6. 晚上暗夜保护区观星：Dark Sky Project 是唯一持牌运营方，需提前 3–4 周订（旺季更早）。9 月底夜间 0–5℃，羽绒服+帽子+手套必备，手电要用红光模式。"""),

    ("09-26", "蒂卡波湖 → 普卡基湖 → 库克山", """【牛奶蓝湖+进山：这一天是最漂亮的公路段】
1. 蒂卡波→普卡基湖约 1h。Peters Lookout 是拍「普卡基湖+库克山」最经典的机位，一定要停（就在公路边，注意来车）。
2. 普卡基湖游客中心旁有 Mt Cook Alpine Salmon 三文鱼店，可买生鱼片样板坐在湖边吃，约 10:00–17:00。
3. 普卡基湖→库克山村走 SH80 约 50min。进村第一站先去 DOC Visitor Centre 拿免费步道地图（园区手机信号极弱，提前下好离线地图）。
4. 下午到的话可先走 Kea Point（2h 往返）或 Tasman Glacier View（40min 往返，约 300 级台阶）；胡克谷留给第二天更从容。
5. 今夜住 Twizel：最近的补给镇（4 Square 超市），餐厅选择少、18:00 前吃晚饭；Twizel 是 Aoraki Mackenzie 暗夜区核心，晚上出门抬头就是银河。"""),

    ("09-27", "库克山 · 直升机 + 冰川船 → 瓦纳卡", """【库克山重头戏：直升机和冰川船要错开时段】
1. 直升机（INFLITE，从库克山机场起飞）和冰川船都高度依赖天气，取消率不低。建议直升机排上午、冰川船排下午，互为备份；若直升机取消可当场改期或改签。
2. 冰川船（Glacier Explorers）含 1.5km 步行到湖边（约 25min，碎石坡），必须穿防滑鞋；湖上风大温度低，羽绒服+墨镜+防晒霜三件套。出发前 30min 到隐士酒店一楼 Activities Desk 报到。
3. 冰川船运营季约 9 月–次年 6 月，6/21–8/31 停运；旺季（12–3 月）要提前 2–3 个月订，9 月底相对好订但也别拖。
4. 胡克谷步道 10km 往返约 3–4h，全程平缓、3 座吊桥，终点 Hooker Lake 拍库克山倒影。9 月底可能有残雪和结冰，早晨更滑，带登山杖更稳。
5. 库克山→瓦纳卡约 2.5h（经 Twizel、Omarama）。Omarama Hot Tubs 是著名的私人木桶温泉，顺路泡 1h 非常解乏（需提前订位）。"""),

    ("09-28", "瓦纳卡 → 皇后镇", """【瓦纳卡：湖、树、桑拿、打枪一天全包】
1. 孤独的树（That Wanaka Tree）在湖西南岸，日出/日落逆光剪影最出片，停车后走 3min。白天人多，早上 7 点前几乎没人。
2. 湖边桑拿首推 The Sauna Wānaka（Outlet 湖畔，80–90℃ 木柴桑拿 + 冰湖跳水，60–70min 一场，需提前网上订时段）。如果前一晚住 Lake Hāwea，也可以去 The Secret Sauna（就在 Lake Hāwea 岸边，共享场 NZ$32/人/小时，15min 车程）。
3. 环湖骑车：Wanaka → Lake Hāwea 段最平缓、风景最好；镇上多家租车店（半天约 NZ$40–60），也可只骑 Outlet 湖滨段。
4. 打枪射击在 Cardrona Valley 的 Real Guns（皇后镇↔瓦纳卡之间，距瓦纳卡 13min）。基础套餐含 20 发 .22 半自动 + 10 发霰弹打飞盘，可现场加购 .50 BMG。必须带护照或新西兰驾照原件，提前 15min 签到，穿平底闭趾鞋、不要穿迷彩。
5. 瓦纳卡→皇后镇走 Crown Range 皇冠山脉比绕 Cromwell 近约 20min，但连续发卡弯+陡坡，注意低挡下坡；春季仍可能遇冰雪，出发前查 NZTA 路况。"""),

    ("09-29", "皇后镇 · 蒸汽船 + 天空缆车", """【皇后镇经典两条线：蒸汽船+天空缆车】
1. TSS Earnslaw 蒸汽船 + 瓦尔特峰农场：RealNZ 是唯一运营方，含往返蒸汽船（单程 45min）+ 剪羊毛/牧羊犬表演 + 上午茶或下午茶，全程约 3h45m。夏季班次约 09:00 / 11:00 / 13:00 / 15:00。农场只能坐船到，无公路。
2. 建议 TSS 排上午的班次（约 10:00 出发），下午接 Skyline，晚上回家吃饭，节奏最顺。
3. Skyline 缆车 + Luge：线上买「Gondola + 6 Luge」比现场便宜。Luge 票上有首次乘坐时段，晚太多会被卡住。缆车 2024 年已换新舱（10 人/舱、速度快 3 倍），排队问题基本解决。
4. 山顶观景台朝西，是皇后镇看日落最好的位置；9 月底日落约 19:45，18:30 上山顶最稳。山顶 Market Kitchen 咖啡比 Stratosfare 自助便宜很多。
5. 停车：Skyline 基站在镇中心上坡，车位紧张，建议停 Lakeview 或 Boundary St 停车场再步行 8min。"""),

    ("09-30", "皇后镇 → 格林奇诺骑马 · 箭镇", """【格林奇诺+箭镇：最美公路+动物+淘金史】
1. 小鹿公园 Deer Park Heights 必须提前官网预约（票只提前 7 天开售，每天最多 80 台车，常售罄）。按车收费 NZ$75/车（含司机，最多 8 座），预约时必须填车牌号——所以要等租到车、拿到车牌后再订。
2. 小鹿公园 10 月（春季）开放 08:00–20:00，18:00 前必须离场，超时自动罚 NZ$100。只能开车进（禁止步行、骑行、出租车、Uber、旅游团），且入口已搬到新位置，别只信 Google Maps 的老导航。带一枚 NZ$2 硬币买饲料喂鹿和羊驼。
3. 格林奇诺骑马：Dart Stables（镇中心，老牌）半天团约 2.5–3h，沿 Rees / Dart 河谷；需提前订，初学者可选 1h 体验。
4. 皇后镇→格林奇诺 46km 沿 Lake Wakatipu 湖景公路约 1h，号称新西兰最美公路之一，早上去云少光线最好。
5. 箭镇 Arrowtown：Buckingham St 主街 1h 逛完，华人矿工聚居地遗址（Chinese Settlement）值得看；注意 10 月是初春，箭镇著名的秋色在 4 月，不是现在。
6. 《指环王》取景地：格林奇诺一带的 Paradise、Dart River（Isengard 场景）都在路上，可顺路停。"""),

    ("10-01", "皇后镇还车 ✈️ 奥克兰", """【皇后镇收官+飞奥克兰】
1. Shotover Jet：唯一能进 Shotover 峡谷的喷射快艇，全程约 25min，含 360° 旋转。建议订上午 09:30–11:00 场次，之后才有时间购物和还车。
2. 到达方式二选一：自驾到 Arthurs Point 河基（提前 30min 签到）；或在皇后镇 Station Building 集合搭免费班车（约 10:00 / 11:00 / 12:00 / 14:00 / 15:00），需在「Transport Required」里选 Yes。
3. 还车：10.1 航班 JQ298 17:30 起飞，建议 15:30 前还车，预留加油、验车、大件行李托运时间。皇后镇机场很小但旺季排队长。
4. 新西兰国内航班对液体无限制，但锂电池、充电宝、无人机电池必须随身，不能托运。
5. 奥克兰落地后到圣马修教堂附近住宿：机场→市中心 Uber 约 NZ$45–60 / 30–40min；也可坐 Airport Link 或 SkyDrive。"""),

    ("10-02", "奥克兰 · 圣马修教堂婚礼", """【婚礼日：奥克兰市中心】
1. 圣马修教堂（St Matthew's in the City）在市中心 Wellesley St / Hobson St 交界，周末市中心停车极难，建议全家 Uber 或提前订附近 Wilson 停车楼。
2. 教堂仪式一般需提前 30–45min 到场；花艺、摄影、牧师档期务必提前一天再确认一次进场时间。
3. 10 月是奥克兰初春，天气一天四季，户外拍摄一定备伞+备用室内场地（教堂旁的 Albert Park 是天然备选外景地）。
4. 下午溜达：Albert Park（教堂上坡即到）→ Britomart 红砖街区 → Viaduct Harbour 海港。
5. 婚礼晚餐务必提前订位，周五/周六奥克兰热门餐厅满座率极高；新西兰餐厅普遍不允许自带酒水。"""),

    ("10-03", "奥克兰 · 机动日", """【奥克兰机动日：四个方案按天气选】
1. 方案 A（首推）：怀赫科岛 Waiheke。Fullers360 渡轮 40min 直达，岛上有 20 多家酒庄 + 沙滩，可租车或坐 hop-on hop-off 巴士，一日游刚好。
2. 方案 B：德文波特 Devonport，渡轮仅 12min，维多利亚山（Mt Victoria）看奥克兰天际线，半日足够。
3. 方案 C（雨天）：天空塔 Sky Tower + SkyWalk，或奥克兰战争纪念博物馆。
4. 方案 D（自驾）：Piha / Muriwai 黑沙滩，Muriwai 的塘鹅（Gannet）栖息地 10 月正是筑巢季，几千只同时在场。
5. 若次日凌晨或上午要赶飞机，今天就住在机场附近或提前订好送机，别留到当天早上。"""),

    ("10-04", "北京返程 ✈️ / 奥克兰 → 汤加里罗", """【北京方向返程 + 北岛自驾前置说明】
1. 11:10 新航 SQ4284 奥克兰→新加坡，国际航班建议提前 3h 到机场，即 08:00 前抵达。
2. 新西兰生物安检是全世界最严之一：蜂蜜、肉类、鲜果、木质品、用过的登山鞋（鞋底泥土）一律申报，不申报罚款 NZ$400 起。
3. 液体/免税品在安检后买；酒类随身限带 3 瓶（每瓶 1.125L 以内）。
4. 奥克兰→汤加里罗约 4.5–5h / 330km（SH1 转 SH46），建议中途在 Hamilton 或 Taupo 休息加油；也可从奥克兰飞 Taupo 再租车，省 4h 车程。
5. 汤加里罗高山穿越是 A→B 单线：Mangatepopo 起、Ketetahi 终，两端公路相距 20km，无法走回起点，因此必须提前订 shuttle 接驳。
6. 停车场限制：每年 10 月 26 日–次年 4 月 30 日，两端停车场执行 4 小时最长停车限制。10/5 去刚好在限制开始前，但仍强烈建议坐接驳车。
7. 顺序：先在 DOC 官网订步道时段 → 拿到 booking number → 再订 shuttle（接驳公司会要你的 DOC 编号）。"""),

    ("10-05", "汤加里罗高山穿越（19.4km / 7–8h）", """【汤加里罗高山穿越 + 塔拉纳基】
1. 汤加里罗高山穿越 19.4km，7–8h，累计爬升约 800m。经典节点：Mangatepopo Saddle → Red Crater（红色火山口）→ Emerald Lakes（翡翠湖）→ Blue Lake → Ketetahi 瀑布。
2. 建议坐 06:00–07:30 的早班接驳车，13:00 前必须过 Red Crater，否则天黑前走不出来。返程接驳车约 13:00–16:00 在 Ketetahi 等。
3. 体力一般或天气不好，可改走 Tama Lakes（往返 5–6h）或 Lower Tama，风景同样震撼但强度减半。
4. 塔拉纳基（Mt Taranaki / Egmont National Park）在完全另一个方向，距汤加里罗约 3h 车程。两天一夜想同时拿下两地非常赶，建议二选一或延长到 3 天。
5. 塔拉纳基经典线路：Pouakai Crossing（单程 8h，需接驳）或 Mangorei Track 往返 Pouakai Tarns 拍「雪山倒影」（往返约 5h，是塔拉纳基最经典的机位）。
6. 山上无补给、无信号：每人至少带 2L 水 + 高热量食物 + 防风防雨外层。Emerald Lakes 与 Ketetahi 的水含高浓度矿物质，不可饮用。
7. 山区天气变化极快，出发前一晚查 NIWA 三日预报；遇大风/大雨/能见度差应果断放弃并改期。"""),

    ("10-06", "北岛徒步第二天 · 塔拉纳基", """【北岛徒步第二天】
1. 汤加里罗第二天可选：Round the Mountain Track 局部 / Taranaki Falls（往返 2h，轻松）/ Tama Lakes。
2. 若改去塔拉纳基：本日主要用于转场（约 3h 车程）+ 傍晚轻松步道，第二天再上 Pouakai。
3. 返回奥克兰需再 4.5–5h 车程；也可从 New Plymouth 或 Taupo 飞奥克兰，省时间。
4. 索道/缆车不适用，全部靠走；带足水和防晒，山区紫外线极强。"""),

    ("10-07", "深圳返程 ✈️ 奥克兰 → 香港", """【深圳方向返程】
1. 14:25 国泰 CX198 奥克兰→香港，21:05 到港。建议 11:00 前到机场，预留生物安检排队时间（队伍经常 40min+）。
2. 香港→深圳：CX198 落地后可乘机场快线到九龙站，再转深圳湾/福田口岸巴士；或直接在机场坐跨境巴士。
3. 新西兰离境不退税（GST 不退），但安检后免税店商品可买。
4. 出发前再确认一次签证/免签与入境最新政策，以及随身行李的锂电池规定。"""),
]

# (day key, name, lat, lng, category, address, note)
PLACES = [
    # Day 1
    ("09-24", "奥克兰机场（国际到达）", -37.0082, 174.7850, "transport", "Auckland Airport, Mangere, Auckland 2022", "11:15 落地，入境+取行李约 1h；国际→国内航站楼步行约 10min（绿线步道）"),
    ("09-24", "奥克兰机场假日酒店", -37.0085, 174.7905, "hotel", "2 Ascot Road, Mangere, Auckland 2022", "🏨 住奥克兰 1 晚；有免费机场班车。同程预订，8/24 前可免费退"),
    ("09-24", "试婚纱（市区婚纱店）", -36.8485, 174.7633, "shopping", "Queen St, Auckland CBD", "试纱建议放下午，上午先补觉倒时差"),
    ("09-24", "皇后大街 Queen St", -36.8482, 174.7630, "shopping", "Queen Street, Auckland CBD", "市区逛街起点"),
    ("09-24", "Britomart 布里托马特区", -36.8444, 174.7680, "attraction", "Britomart, Auckland CBD", ""),
    ("09-24", "Viaduct Harbour 高架桥港", -36.8420, 174.7639, "attraction", "Viaduct Harbour, Auckland CBD", "海港边散步；餐厅 21:00 后基本打烊"),
    ("09-24", "Countdown / New World 超市", -36.8460, 174.7660, "shopping", "Auckland CBD", "买电话卡和零食，比机场便宜 30%+"),
    # Day 2
    ("09-25", "奥克兰机场（JQ227 国内出发）", -37.0082, 174.7850, "transport", "Auckland Airport Domestic, Mangere", "JQ227 07:15 起飞，国内航站楼 D；建议 05:15 前到"),
    ("09-25", "基督城机场（取车）", -43.4894, 172.5322, "transport", "Christchurch Airport, Harewood, Christchurch 8053", "取车：驾照原件 + NZTA 翻译件，租车公司会复印存档"),
    ("09-25", "杰拉尔丁 Geraldine", -44.0922, 171.2438, "restaurant", "Geraldine, Canterbury", "中途加油+午餐"),
    ("09-25", "Fairlie Bakehouse", -44.0986, 170.8280, "restaurant", "74 Main Street, Fairlie 7925", "南岛最出名的派店，排队也值"),
    ("09-25", "蒂卡波湖 Lake Tekapo", -44.0048, 170.4780, "nature", "Lake Tekapo, Mackenzie District", "基督城→蒂卡波湖 约 3h / 230km，SH8 路况好"),
    ("09-25", "约翰山观景台 Mt John", -43.9855, 170.4650, "attraction", "Mt John Observatory, Lake Tekapo", "自驾上山 Road User Fee 约 NZ$8/车（自助刷卡）；Astro Café 白天营业"),
    ("09-25", "好牧羊人教堂", -44.0041, 170.4767, "attraction", "Church of the Good Shepherd, Lake Tekapo", "免费；17:00 后旅行团散去，光线最好"),
    ("09-25", "暗夜保护区观星 Dark Sky Project", -44.0025, 170.4794, "activity", "Dark Sky Project, 1 Motuariki Lane, Lake Tekapo", "唯一持牌运营方，需提前 3–4 周订；夜间 0–5℃，手电用红光模式"),
    # Day 3
    ("09-26", "普卡基湖 Lake Pukaki", -44.1667, 170.1333, "nature", "Lake Pukaki, Mackenzie District", "蒂卡波→普卡基湖约 1h"),
    ("09-26", "Peters Lookout", -44.1937, 170.1368, "attraction", "Peters Lookout, Lake Pukaki", "📍拍「普卡基湖+库克山」最经典机位，就在公路边，注意来车"),
    ("09-26", "Mt Cook Alpine Salmon", -44.1858, 170.1327, "restaurant", "Lake Pukaki Visitor Centre, State Highway 8", "🍣 生鱼片样板，可坐湖边吃；约 10:00–17:00"),
    ("09-26", "库克山村 DOC Visitor Centre", -43.7345, 170.0957, "attraction", "DOC Aoraki/Mt Cook Visitor Centre, 1 Larch Grove", "拿免费步道地图；园区手机信号极弱，提前下好离线地图"),
    ("09-26", "Kea Point 步道", -43.7200, 170.0950, "activity", "Kea Point Track, Aoraki/Mount Cook", "往返 2h"),
    ("09-26", "Tasman Glacier View", -43.6950, 170.1830, "activity", "Tasman Glacier View, Mount Cook National Park", "往返 40min，约 300 级台阶"),
    ("09-26", "Twizel 特维泽尔", -44.2575, 170.1027, "other", "Twizel, Canterbury 7901", "最近的补给镇（4 Square 超市），18:00 前吃晚饭；暗夜区核心"),
    # Day 4
    ("09-27", "库克山机场（INFLITE 直升机）", -43.7650, 170.1330, "activity", "Mount Cook Airport, Mount Cook National Park", "上午场：直升机；高度依赖天气，取消率不低"),
    ("09-27", "隐士酒店 The Hermitage（冰川船报到）", -43.7333, 170.0914, "activity", "89 Terrace Road, Mount Cook National Park 7999", "下午场：Glacier Explorers；出发前 30min 到一楼 Activities Desk 报到"),
    ("09-27", "胡克谷步道 Hooker Valley Track", -43.7167, 170.1000, "activity", "White Horse Hill Campground, Hooker Valley Track", "10km 往返约 3–4h，3 座吊桥，终点 Hooker Lake 拍库克山倒影；9 月底有残雪结冰"),
    ("09-27", "Omarama Hot Tubs", -44.4878, 169.9697, "activity", "Omarama Hot Tubs, 29 Omarama Ave, Omarama 9412", "私人木桶温泉，顺路泡 1h，需提前订位"),
    ("09-27", "瓦纳卡 Lake Wanaka / Lake Hāwea", -44.6960, 169.1400, "nature", "Lake Wanaka, Otago", "库克山→瓦纳卡约 2.5h（经 Twizel、Omarama）"),
    # Day 5
    ("09-28", "孤独的树 That Wanaka Tree", -44.7000, 169.1300, "attraction", "That Wanaka Tree, Lake Wanaka", "湖西南岸，日出/日落逆光剪影最出片；早上 7 点前几乎没人"),
    ("09-28", "The Sauna Wānaka", -44.6900, 169.1400, "activity", "Outlet, Lake Wanaka", "80–90℃ 木柴桑拿 + 冰湖跳水，60–70min 一场，需提前订时段"),
    ("09-28", "Real Guns 射击（Cardrona Valley）", -44.8600, 168.9800, "activity", "Cardrona Valley Road, Wanaka", "基础套餐 20 发 .22 + 10 发霰弹；必须带护照原件，提前 15min 签到，穿平底闭趾鞋、不穿迷彩"),
    ("09-28", "皇冠山脉公路 Crown Range Road", -44.9300, 168.8500, "other", "Crown Range Road, Otago", "比绕 Cromwell 近约 20min；连续发卡弯+陡坡，注意低挡下坡，出发前查 NZTA 路况"),
    ("09-28", "皇后镇 Queenstown", -45.0312, 168.6626, "other", "Queenstown, Otago 9300", "🏨 住皇后镇 3 晚"),
    ("09-28", "Lakeview 停车场", -45.0322, 168.6600, "transport", "Lakeview Car Park, Queenstown", "🅿️ 皇后镇中心便宜停车场：2.5 刀/小时，18:00 后免费"),
    # Day 6
    ("09-29", "TSS Earnslaw 蒸汽船码头", -45.0330, 168.6578, "activity", "Steamer Wharf, 88 Beach Street, Queenstown", "RealNZ 唯一运营方；含往返蒸汽船（单程 45min）+ 农场表演 + 茶点，约 3h45m，建议约 10:00 班次"),
    ("09-29", "瓦尔特峰高原农场 Walter Peak", -45.1000, 168.5600, "activity", "Walter Peak High Country Farm, Lake Wakatipu", "剪羊毛/牧羊犬表演；只能坐船到，无公路"),
    ("09-29", "Skyline Queenstown 天空缆车", -45.0290, 168.6560, "activity", "📍Skyline Queenstown, Brecon Street, Queenstown", "线上买「Gondola + 6 Luge」比现场便宜；山顶朝西，看日落最好，9 月底日落约 19:45"),
    # Day 7
    ("09-30", "Deer Park Heights 小鹿公园", -45.0100, 168.6300, "activity", "Deer Park Heights, Queenstown 9371", "必须提前官网预约（提前 7 天开售，每天最多 80 台车）；NZ$75/车，预约需填车牌，18:00 前离场"),
    ("09-30", "格林奇诺 Glenorchy", -44.8500, 168.3860, "other", "Glenorchy, Otago", "皇后镇→格林奇诺 46km 沿 Lake Wakatipu 湖景公路约 1h，号称新西兰最美公路之一"),
    ("09-30", "Dart Stables 骑马", -44.8520, 168.3890, "activity", "Dart Stables, 45 Mull Street, Glenorchy 9350", "半天团约 2.5–3h，沿 Rees / Dart 河谷；需提前订，初学者可选 1h 体验"),
    ("09-30", "天堂镇 Paradise", -44.7000, 168.3600, "nature", "Paradise, Glenorchy", "《指环王》Isengard 场景一带，Dart River 在路上可顺路停"),
    ("09-30", "箭镇 Arrowtown", -44.9380, 168.8330, "other", "Arrowtown, Otago 9302", "Buckingham St 主街 1h 逛完；注意 10 月是初春，秋色在 4 月"),
    ("09-30", "华人矿工聚居地 Chinese Settlement", -44.9400, 168.8300, "attraction", "Chinese Settlement, Arrowtown", "华人淘金历史遗址，值得看"),
    # Day 8
    ("10-01", "Shotover Jet", -44.9880, 168.6810, "activity", "📍Shotover Jet, Arthurs Point, Queenstown", "唯一能进 Shotover 峡谷的喷射快艇，约 25min 含 360° 旋转；建议订 09:30–11:00 场次"),
    ("10-01", "皇后镇机场（还车）", -45.0211, 168.7392, "transport", "Queenstown Airport, Frankton, Queenstown 9300", "JQ298 17:30 起飞，建议 15:30 前还车；锂电池/充电宝必须随身"),
    ("10-01", "奥克兰机场（到达）", -37.0082, 174.7850, "transport", "Auckland Airport, Mangere, Auckland 2022", "机场→市中心 Uber 约 NZ$45–60 / 30–40min；也可坐 Airport Link 或 SkyDrive"),
    ("10-01", "圣马修教堂附近住宿", -36.8500, 174.7660, "hotel", "Wellesley Street West, Auckland CBD", "🏨 住奥克兰圣马修教堂附近 2 晚"),
    # Day 9
    ("10-02", "圣马修教堂 St Matthew's in the City", -36.8509, 174.7652, "attraction", "St Matthew's in the City, Wellesley St / Hobson St, Auckland CBD", "上午婚礼仪式；提前 30–45min 到场，周末市中心停车极难，建议全家 Uber"),
    ("10-02", "Albert Park 阿尔伯特公园", -36.8504, 174.7684, "nature", "Albert Park, Auckland CBD", "教堂上坡即到，户外拍摄的天然备选外景地"),
    ("10-02", "Britomart 红砖街区", -36.8444, 174.7680, "attraction", "Britomart, Auckland CBD", ""),
    ("10-02", "Viaduct Harbour 海港", -36.8420, 174.7639, "attraction", "Viaduct Harbour, Auckland CBD", ""),
    ("10-02", "婚礼晚餐（需提前订位）", -36.8460, 174.7670, "restaurant", "Auckland CBD", "周五/周六热门餐厅满座率极高；新西兰餐厅普遍不允许自带酒水"),
    # Day 10
    ("10-03", "怀赫科岛 Waiheke Island", -36.8000, 175.1000, "nature", "Waiheke Island, Auckland", "方案 A（首推）：Fullers360 渡轮 40min 直达，20+ 酒庄 + 沙滩，一日游刚好"),
    ("10-03", "德文波特 Devonport", -36.8300, 174.7950, "attraction", "Devonport, Auckland 0624", "方案 B：渡轮仅 12min，维多利亚山看奥克兰天际线，半日足够"),
    ("10-03", "天空塔 Sky Tower", -36.8485, 174.7633, "attraction", "Sky Tower, Victoria Street West, Auckland CBD", "方案 C（雨天）：Sky Tower + SkyWalk"),
    ("10-03", "奥克兰战争纪念博物馆", -36.8605, 174.7750, "attraction", "Auckland War Memorial Museum, Parnell, Auckland", "方案 C（雨天）"),
    ("10-03", "Piha 皮哈黑沙滩", -36.9500, 174.4700, "beach", "Piha, Auckland 0772", "方案 D（自驾）"),
    ("10-03", "Muriwai 塘鹅栖息地", -36.8280, 174.4340, "nature", "Muriwai Gannet Colony, Muriwai 0881", "方案 D：10 月正是筑巢季，几千只塘鹅同时在场"),
    # Day 11
    ("10-04", "奥克兰机场（SQ4284 出发）", -37.0082, 174.7850, "transport", "Auckland Airport International, Mangere", "SQ4284 11:10 起飞（北京方向）；国际航班提前 3h，08:00 前抵达"),
    ("10-04", "汉密尔顿 Hamilton", -37.7870, 175.2793, "other", "Hamilton, Waikato", "北岛自驾中途休息+加油"),
    ("10-04", "陶波湖 Taupo", -38.6857, 176.0702, "nature", "Lake Taupo, Waikato", "休息加油；也可从奥克兰飞 Taupo 再租车，省 4h 车程"),
    ("10-04", "汤加里罗国家公园 Tongariro", -39.1428, 175.5797, "nature", "Tongariro National Park, Manawatu-Whanganui", "奥克兰→汤加里罗约 4.5–5h / 330km（SH1 转 SH46）"),
    # Day 12
    ("10-05", "Mangatepopo 起点停车场", -39.1428, 175.5797, "activity", "Mangatepopo Road End, Tongariro National Park", "建议坐 06:00–07:30 早班接驳车；A→B 单线，两端相距 20km 无法走回起点"),
    ("10-05", "Red Crater 红色火山口", -39.1300, 175.6500, "nature", "Red Crater, Tongariro Alpine Crossing", "13:00 前必须通过，否则天黑前走不出来"),
    ("10-05", "Emerald Lakes 翡翠湖", -39.1250, 175.6550, "nature", "Emerald Lakes, Tongariro Alpine Crossing", "水含高浓度矿物质，不可饮用"),
    ("10-05", "Blue Lake 蓝湖", -39.1180, 175.6650, "nature", "Blue Lake, Tongariro Alpine Crossing", ""),
    ("10-05", "Ketetahi 终点", -39.0960, 175.6700, "activity", "Ketetahi Road End, Tongariro National Park", "返程接驳车约 13:00–16:00 在此等"),
    ("10-05", "塔拉纳基山 Mt Taranaki", -39.2960, 174.0630, "nature", "Egmont National Park, Taranaki", "在完全另一个方向，距汤加里罗约 3h 车程；两天一夜同时拿下两地非常赶，建议二选一或延长到 3 天"),
    # Day 13
    ("10-06", "Taranaki Falls 步道", -39.2100, 175.5400, "activity", "Taranaki Falls, Tongariro National Park", "往返 2h，轻松"),
    ("10-06", "Tama Lakes 步道", -39.1800, 175.5900, "activity", "Tama Lakes, Tongariro National Park", "往返 5–6h，风景震撼强度减半"),
    ("10-06", "Mangorei Track / Pouakai Tarns", -39.1000, 174.0500, "activity", "Mangorei Road End, Egmont National Park", "往返约 5h，拍「雪山倒影」塔拉纳基最经典机位；两天一夜建议二选一"),
    ("10-06", "新普利茅斯 New Plymouth", -39.0556, 174.0750, "other", "New Plymouth, Taranaki", "可从此飞奥克兰省时间"),
    # Day 14
    ("10-07", "奥克兰机场（CX198 出发）", -37.0082, 174.7850, "transport", "Auckland Airport International, Mangere", "CX198 14:25 起飞（深圳方向）；建议 11:00 前到机场，生物安检排队长"),
]

# (type, title, day key, end day key|None, time, end time, flight meta, endpoints, notes)
FLIGHTS = [
    ("flight", "CX113 香港 → 奥克兰（深圳出发组）", "09-24", 33, "11:15",
     {"airline": "国泰航空", "flight_number": "CX113", "departure_airport": "HKG", "arrival_airport": "AKL"},
     [("from", 0, "香港国际机场", "HKG", "2026-09-23", "21:10", "Asia/Hong_Kong"),
      ("to", 1, "奥克兰机场", "AKL", "2026-09-24", "11:15", "Pacific/Auckland")],
     "9.23 晚上 21:10 香港出发，9.24 上午 11:15 落地奥克兰（深圳出发组）"),
    ("flight", "SQ801 北京 → 新加坡 → 奥克兰（北京出发组）", "09-24", 33, "22:15",
     {"airline": "新加坡航空", "flight_number": "SQ801", "departure_airport": "PEK", "arrival_airport": "AKL"},
     [("from", 0, "北京首都国际机场", "PEK", "2026-09-24", "00:05", "Asia/Shanghai"),
      ("stop", 1, "新加坡樟宜机场", "SIN", "2026-09-24", "", "Asia/Singapore"),
      ("to", 2, "奥克兰机场", "AKL", "2026-09-24", "22:15", "Pacific/Auckland")],
     "9.24 凌晨 00:05 北京出发，9.24 晚上 22:15 落地奥克兰（北京出发组）"),
    ("flight", "JQ227 奥克兰 → 基督城", "09-25", 34, "07:15",
     {"airline": "捷星航空", "flight_number": "JQ227", "departure_airport": "AKL", "arrival_airport": "CHC"},
     [("from", 0, "奥克兰机场（国内航站楼 D）", "AKL", "2026-09-25", "07:15", "Pacific/Auckland"),
      ("to", 1, "基督城机场", "CHC", "2026-09-25", "", "Pacific/Auckland")],
     "境内小机票。落地基督城机场取车"),
    ("flight", "JQ298 皇后镇 → 奥克兰", "10-01", 40, "17:30",
     {"airline": "捷星航空", "flight_number": "JQ298", "departure_airport": "ZQN", "arrival_airport": "AKL"},
     [("from", 0, "皇后镇机场", "ZQN", "2026-10-01", "17:30", "Pacific/Auckland"),
      ("to", 1, "奥克兰机场", "AKL", "2026-10-01", "", "Pacific/Auckland")],
     "境内小机票。皇后镇机场很小但旺季排队长"),
    ("flight", "SQ4284 奥克兰 → 新加坡", "10-04", 43, "11:10",
     {"airline": "新加坡航空", "flight_number": "SQ4284", "departure_airport": "AKL", "arrival_airport": "SIN"},
     [("from", 0, "奥克兰机场", "AKL", "2026-10-04", "11:10", "Pacific/Auckland"),
      ("to", 1, "新加坡樟宜机场", "SIN", "2026-10-04", "", "Asia/Singapore")],
     "北京方向返程；国际航班建议提前 3h 到机场，即 08:00 前抵达"),
    ("flight", "CX198 奥克兰 → 香港（深圳返程）", "10-07", 46, "14:25",
     {"airline": "国泰航空", "flight_number": "CX198", "departure_airport": "AKL", "arrival_airport": "HKG"},
     [("from", 0, "奥克兰机场", "AKL", "2026-10-07", "14:25", "Pacific/Auckland"),
      ("to", 1, "香港国际机场", "HKG", "2026-10-07", "21:05", "Asia/Hong_Kong")],
     "21:05 到港。香港→深圳：机场快线到九龙站转口岸巴士，或机场直接坐跨境巴士"),
]

CAR = ("car", "南岛租车（基督城机场取车 → 皇后镇机场还车）", "09-25", 40,
       "基督城机场取车，皇后镇机场还车。驾照原件 + NZTA 翻译件必须随身，租车公司会复印存档")

# (day key, name, category, price, note)
BUDGET = [
    ("09-24", "往返大机票（国际段 2 人）", "flights", 16000, "香港/北京往返奥克兰：CX113、SQ801、SQ4284、CX198。提前定可退改"),
    ("09-25", "境内小机票（JQ227 + JQ298）", "flights", 1800, "奥克兰→基督城、皇后镇→奥克兰"),
    ("09-25", "南岛租车（8 天）", "transport", 3600, "基督城机场取车 → 皇后镇机场还车"),
    ("09-25", "油费（南岛 8 天）", "fuel", 1200, "基督城→蒂卡波→库克山→瓦纳卡→皇后镇"),
    ("09-24", "住宿（14 晚）", "accommodation", 14000, "奥克兰 1 晚 + 南岛 6 晚 + 皇后镇 3 晚 + 奥克兰 2 晚 + 北岛 2 晚"),
    ("09-24", "婚礼相关（摄影师+化妆师、教堂、拍摄团队、牧师）", "fees", 30000, "已预订 ✅。提前一天再确认进场时间"),
    ("09-24", "试婚纱", "shopping", 800, "9/24 下午市区试纱"),
    ("09-24", "电话卡（2 张）", "other", 300, "不要买同一运营商，以防信号不佳"),
    ("09-24", "纽币现金兑换", "other", 1000, "建议现金 500 纽币/人；小镇、礼品店、酒店押金需现金"),
    ("09-24", "境外旅游保险", "health", 600, "出发前购买"),
    ("09-25", "Dark Sky Project 观星", "activities", 400, "唯一持牌运营方，需提前 3–4 周订"),
    ("09-27", "库克山直升机（INFLITE）", "activities", 1400, "上午场；高度依赖天气，直升机取消可当场改期"),
    ("09-27", "塔斯曼冰川船 Glacier Explorers", "activities", 400, "下午场；出发前 30min 到隐士酒店一楼 Activities Desk 报到"),
    ("09-27", "Omarama Hot Tubs 温泉", "activities", 200, "私人木桶温泉，需提前订位"),
    ("09-28", "The Sauna Wānaka 桑拿", "activities", 160, "80–90℃ 木柴桑拿 + 冰湖跳水，需提前订时段"),
    ("09-28", "Real Guns 射击", "activities", 300, "基础套餐 20 发 .22 + 10 发霰弹；必须带护照原件"),
    ("09-29", "TSS 蒸汽船 + 瓦尔特峰农场", "activities", 700, "RealNZ 唯一运营方，全程约 3h45m，建议约 10:00 班次"),
    ("09-29", "Skyline 缆车 + Luge", "activities", 400, "线上买「Gondola + 6 Luge」比现场便宜"),
    ("09-30", "Deer Park Heights 小鹿公园", "activities", 75, "按车收费 NZ$75/车（含司机，最多 8 座），预约需填车牌"),
    ("09-30", "格林奇诺骑马 Dart Stables", "activities", 500, "半天团约 2.5–3h，需提前订"),
    ("10-01", "Shotover Jet 喷射快艇", "activities", 400, "约 25min 含 360° 旋转，建议订 09:30–11:00 场次"),
    ("10-04", "汤加里罗 shuttle 接驳", "activities", 200, "A→B 单线必须订接驳；先在 DOC 官网订步道时段拿 booking number"),
    ("10-05", "北岛住宿 + 餐食", "accommodation", 1500, "汤加里罗 / 新普利茅斯 2 晚"),
    ("10-01", "餐饮（14 天）", "food", 6000, "小镇餐厅 18:00 前吃晚饭，21:00 后基本打烊"),
    ("10-01", "停车费", "parking", 200, "皇后镇 Lakeview 停车场 NZ$2.5/小时，18:00 后免费"),
]

PACKING = [
    ("护照 + 签证", "证件"),
    ("驾照原件 + NZTA 翻译件（最后一页贴照片+签名）", "证件"),
    ("身份证", "证件"),
    ("境外旅游保险单", "证件"),
    ("机票 / 酒店 / 租车确认单", "证件"),
    ("纽币现金 500/人", "证件"),
    ("电话卡（不同运营商）", "电子"),
    ("充电宝 / 锂电池（必须随身，不可托运）", "电子"),
    ("转换插头（新西兰 I 型）", "电子"),
    ("相机 + 备用电池", "电子"),
    ("手机充电线", "电子"),
    ("红光手电（观星用）", "装备"),
    ("羽绒服（9 月底南岛夜间 0–5℃）", "衣物"),
    ("防风防雨外层", "衣物"),
    ("帽子 + 手套", "衣物"),
    ("快干内层 / 排汗衣", "衣物"),
    ("泳衣（桑拿 / 温泉）", "衣物"),
    ("防晒霜（山区紫外线极强）", "洗漱"),
    ("墨镜", "装备"),
    ("防滑登山鞋（冰川船碎石坡、胡克谷残雪）", "装备"),
    ("登山杖", "装备"),
    ("雨伞", "装备"),
    ("常用药品 + 创可贴", "洗漱"),
    ("水壶（2L 容量，徒步用）", "装备"),
    ("高热量零食（汤加里罗穿越）", "食品"),
    ("婚礼礼服 / 正装", "婚礼"),
    ("婚纱（试纱后确认）", "婚礼"),
    ("相机备用存储卡", "电子"),
]

TODOS = [
    ("婚礼相关预订（摄影师+化妆师、教堂、拍摄团队、牧师）", "婚礼", "2026-09-20", 3),
    ("往返大机票", "机票", "2026-09-20", 3),
    ("境内小机票（JQ227 / JQ298）", "机票", "2026-09-20", 3),
    ("南岛租车", "交通", "2026-09-20", 3),
    ("驾照 + 翻译件（最后一页贴照片+签名）", "证件", "2026-09-20", 3),
    ("买电话卡（互相不要买同一运营商）", "通讯", "2026-09-22", 2),
    ("新西兰纽币兑换（现金 500 纽币/人）", "现金", "2026-09-22", 2),
    ("出发前买境外旅游保险", "保险", "2026-09-22", 3),
    ("Dark Sky Project 观星预订（提前 3–4 周）", "预约项目", "2026-09-18", 3),
    ("库克山直升机 INFLITE 预订（上午场）", "预约项目", "2026-09-18", 3),
    ("塔斯曼冰川船 Glacier Explorers 预订（下午场）", "预约项目", "2026-09-18", 3),
    ("TSS 蒸汽船 + 瓦尔特峰农场 RealNZ 预订（约 10:00 班次）", "预约项目", "2026-09-20", 2),
    ("Skyline 缆车 + 6 Luge 线上购票", "预约项目", "2026-09-22", 1),
    ("Deer Park Heights 小鹿公园预约（租到车拿到车牌后再订）", "预约项目", "2026-09-25", 3),
    ("格林奇诺骑马 Dart Stables 预订", "预约项目", "2026-09-20", 2),
    ("Shotover Jet 预订（09:30–11:00 场次）", "预约项目", "2026-09-22", 2),
    ("Real Guns 射击预约", "预约项目", "2026-09-22", 2),
    ("The Sauna Wānaka 桑拿订时段", "预约项目", "2026-09-22", 1),
    ("Omarama Hot Tubs 温泉订位", "预约项目", "2026-09-22", 1),
    ("汤加里罗：DOC 官网订步道时段 → 再订 shuttle 接驳", "预约项目", "2026-09-25", 2),
    ("婚礼前一天再确认花艺/摄影/牧师进场时间", "婚礼", "2026-10-01", 3),
    ("查 NZTA 路况（Crown Range 春季可能冰雪）", "交通", "2026-09-28", 1),
    ("查 NIWA 三日天气预报（汤加里罗出发前一晚）", "徒步", "2026-10-04", 3),
]


def main():
    s = session()
    frm = int(os.environ.get("FROM_STEP", "1"))

    # 1. day titles + notes
    if frm <= 1:
        for i, (key, title, notes) in enumerate(DAYS):
            call("update_day", {"tripId": TRIP, "dayId": DAY[key], "title": title, "notes": notes},
                 sid=s, rid=1000 + i)
            print(f"day {key} ok", file=sys.stderr)

    # 2. places, created already assigned to their day
    resume = int(os.environ.get("PLACE_FROM", "0"))
    ids = json.load(open("/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp/place-ids.json")) \
        if resume and os.path.exists("/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp/place-ids.json") else []
    if frm <= 2:
        for i, (key, name, lat, lng, cat, addr, note) in enumerate(PLACES):
            if i < resume:
                continue
            payload = {"tripId": TRIP, "dayId": DAY[key], "name": name,
                       "lat": lat, "lng": lng, "category_id": CAT[cat]}
            if addr:
                payload["address"] = addr
            if note:
                payload["place_notes"] = note
            r = call("create_and_assign_place", payload, sid=s, rid=2000 + i)
            pid = (r.get("place") or {}).get("id")
            ids.append(pid)
            print(f"place {pid} d{DAY[key]} {name}", file=sys.stderr)
        json.dump(ids, open("/Users/sakyaer/AILife/TravelProject/TREK/.agents/tmp/place-ids.json", "w"))

    # 3. flights
    if frm <= 3:
        for i, (typ, title, key, dayid, t, meta, eps, notes) in enumerate(FLIGHTS):
            endpoints = [{"role": r, "sequence": q, "name": n, "code": c,
                          **({"local_date": d} if d else {}), **({"local_time": lt} if lt else {}),
                          "timezone": tz}
                         for (r, q, n, c, d, lt, tz) in eps]
            call("create_transport", {
                "tripId": TRIP, "type": typ, "title": title, "start_day_id": dayid,
                "reservation_time": t, "status": "confirmed",
                "metadata": meta, "endpoints": endpoints, "notes": notes,
            }, sid=s, rid=3000 + i)
            print(f"flight {title} ok", file=sys.stderr)

        # 4. car rental
        typ, title, key, dayid, notes = CAR
        call("create_transport", {
            "tripId": TRIP, "type": typ, "title": title,
            "start_day_id": DAY[key], "end_day_id": dayid, "status": "confirmed", "notes": notes,
        }, sid=s, rid=3050)
        print("car ok", file=sys.stderr)

    # 5. accommodations — link the hotel places created above
    if frm <= 5:
        def find(sub):
            for i, p in enumerate(PLACES):
                if sub in p[1]:
                    return ids[i]
            raise KeyError(sub)

        accom = [
            ("假日酒店", "09-24", "09-25", "15:00", "10:00"),
            ("Lake Vista", "09-25", "09-26", "15:00", "10:00"),
            ("Wendz", "09-26", "09-27", "15:00", "10:00"),
            ("Lake Hāwea", "09-27", "09-28", "15:00", "10:00"),
            ("皇后镇 Queenstown", "09-28", "10-01", "15:00", "10:00"),
            ("圣马修教堂附近住宿", "10-01", "10-03", "15:00", "10:00"),
        ]
        for i, (sub, a, b, ci, co) in enumerate(accom):
            try:
                pid = find(sub)
            except KeyError:
                print(f"skip accom {sub}", file=sys.stderr)
                continue
            call("create_accommodation", {
                "tripId": TRIP, "place_id": pid, "start_day_id": DAY[a], "end_day_id": DAY[b],
                "check_in": ci, "check_out": co,
            }, sid=s, rid=4000 + i)
            print(f"accom {sub} ok", file=sys.stderr)

    # 6. budget
    if frm <= 6:
        for i, (key, name, cat, price, note) in enumerate(BUDGET):
            call("create_budget_item_with_members", {
                "tripId": TRIP, "name": name, "category": cat,
                "total_price": price, "note": note,
            }, sid=s, rid=5000 + i)
            print(f"budget {name} ok", file=sys.stderr)

    # 7. packing
    if frm <= 7:
        call("bulk_import_packing", {
            "tripId": TRIP,
            "items": [{"name": n, "category": c} for n, c in PACKING],
        }, sid=s, rid=6000)
        print("packing ok", file=sys.stderr)

    # 8. todos
    if frm <= 8:
        for i, (name, cat, due, prio) in enumerate(TODOS):
            call("create_todo", {
                "tripId": TRIP, "name": name, "category": cat,
                "due_date": due, "priority": prio,
            }, sid=s, rid=7000 + i)
            print(f"todo {name} ok", file=sys.stderr)

    print("DONE")


if __name__ == "__main__":
    main()
