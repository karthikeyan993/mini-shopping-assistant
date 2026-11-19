"""A synthetic sports-store catalog, stock and orders. Deterministic (fixed seed), so everyone gets the same data.

Real brand names, invented product lines: this is demo data, not real products or prices.
"""
import random
from datetime import datetime, timedelta, timezone

SEED = 7

# The same navy trail shoe is listed twice. Each listing has its own price and inventory.
# Omitted size/store combinations on these two listings have zero pairs.
TRAIL_OFFERS = {
    "SS-TRS01-008-NAVY": {"price": 6190, "stock": {("41", "CentralWorld"): 4, ("42", "Central Ladprao"): 1}},
    "CE-TRS01-008-NAVY": {"price": 5490, "stock": {("42", "Online"): 3}},
}

STORES = ["CentralWorld", "Central Ladprao", "Central Rama 9", "Central Westgate", "Central Chiang Mai", "Online"]

COLORS = ["black", "white", "grey", "navy", "blue", "red", "green", "pink", "orange", "yellow", "purple", "beige"]
COLOR_TH = {"black": "สีดำ", "white": "สีขาว", "grey": "สีเทา", "navy": "สีกรมท่า", "blue": "สีน้ำเงิน", "red": "สีแดง",
            "green": "สีเขียว", "pink": "สีชมพู", "orange": "สีส้ม", "yellow": "สีเหลือง", "purple": "สีม่วง", "beige": "สีเบจ"}
BRAND_TH = {"Nike": "ไนกี้", "Adidas": "อาดิดาส", "Asics": "เอสิคส์", "Puma": "พูม่า", "New Balance": "นิวบาลานซ์",
            "Under Armour": "อันเดอร์ อาเมอร์", "Yonex": "โยเน็กซ์", "Speedo": "สปีโด้", "Arena": "อารีน่า",
            "Mizuno": "มิซูโน่", "Skechers": "สเก็ตเชอร์ส", "Hoka": "โฮก้า", "The North Face": "เดอะ นอร์ท เฟซ",
            "Columbia": "โคลัมเบีย", "Li-Ning": "หลี่หนิง", "Wilson": "วิลสัน", "Garmin": "การ์มิน", "Decathlon Kalenji": "คาเลนจิ"}

# category, sport, Thai name, brands, price range (THB), sizes, product lines, features (EN, TH)
CATEGORIES = [
    ("running shoes", "running", "รองเท้าวิ่ง", ["Nike", "Adidas", "Asics", "New Balance", "Hoka", "Puma"], (1890, 6990),
     ["39", "40", "41", "42", "43", "44"], ["Swift Run", "Cloud Glide", "Tempo Pro", "Daily Trainer", "Racer Lite", "Stride Max"],
     [("cushioned midsole for long runs", "พื้นนุ่ม วิ่งระยะไกลสบาย"), ("lightweight breathable mesh", "น้ำหนักเบา ระบายอากาศดี"),
      ("stability support for flat feet", "ช่วยซัพพอร์ตเท้าแบน"), ("responsive foam for tempo runs", "โฟมเด้ง เหมาะกับการวิ่งเร็ว")]),
    ("trail running shoes", "running", "รองเท้าวิ่งเทรล", ["Hoka", "Asics", "Columbia", "The North Face"],
     (2990, 7490), ["39", "40", "41", "42", "43", "44"], ["Ridge Trail", "Summit Grip", "Mud Runner", "Canyon"],
     [("grippy lugged outsole", "พื้นดอกยางเกาะถนน"), ("waterproof upper", "กันน้ำ"), ("rock plate protection", "กันหินกระแทก")]),
    ("training shoes", "training", "รองเท้าเทรนนิ่ง", ["Nike", "Adidas", "Puma", "Under Armour", "Skechers"],
     (1590, 4990), ["39", "40", "41", "42", "43", "44"], ["Gym Flex", "Power Lift", "Cross Base", "Studio"],
     [("flat stable base for lifting", "พื้นเรียบ มั่นคง ยกเวทได้"), ("flexible forefoot", "หน้าเท้ายืดหยุ่น")]),
    ("football boots", "football", "รองเท้าฟุตบอล", ["Nike", "Adidas", "Puma", "Mizuno"], (1990, 8990),
     ["39", "40", "41", "42", "43", "44"], ["Strike FG", "Velocity", "Control Pro", "Turf Master"],
     [("firm ground studs", "ปุ่มสำหรับสนามหญ้า"), ("soft touch upper for ball control", "หนังนุ่ม คุมบอลดี")]),
    ("badminton shoes", "badminton", "รองเท้าแบดมินตัน", ["Yonex", "Li-Ning", "Mizuno", "Asics"], (1490, 4990),
     ["39", "40", "41", "42", "43", "44"], ["Court Ace", "Power Cushion", "Quick Step"],
     [("non-marking gum sole", "พื้นยางไม่ทิ้งรอย"), ("lateral support for quick moves", "ซัพพอร์ตด้านข้าง เคลื่อนที่เร็ว")]),
    ("running t-shirt", "running", "เสื้อวิ่ง", ["Nike", "Adidas", "Under Armour", "Asics", "Decathlon Kalenji"], (390, 1590),
     ["XS", "S", "M", "L", "XL"], ["Dri Tee", "Aero Tee", "Breeze Top", "Pace Tee"],
     [("quick-dry fabric", "ผ้าแห้งเร็ว"), ("reflective details for night runs", "มีแถบสะท้อนแสง วิ่งกลางคืน")]),
    ("polo shirt", "golf", "เสื้อโปโล", ["Nike", "Adidas", "Puma", "Under Armour"], (790, 2490), ["S", "M", "L", "XL", "XXL"],
     ["Club Polo", "Fairway", "Classic Pique"],
     [("breathable pique cotton", "ผ้าฝ้ายปิเก้ ระบายอากาศ"), ("UV protection", "ป้องกันยูวี")]),
    ("training shorts", "training", "กางเกงขาสั้น", ["Nike", "Adidas", "Puma", "Under Armour"], (490, 1490),
     ["S", "M", "L", "XL"], ["Flex Short", "Core 7in", "Woven Short"],
     [("zip pocket", "มีกระเป๋าซิป"), ("stretch woven fabric", "ผ้ายืด")]),
    ("leggings", "yoga", "เลกกิ้ง", ["Nike", "Adidas", "Under Armour", "Puma"], (790, 2290), ["XS", "S", "M", "L"],
     ["Studio Tight", "High Rise", "Sculpt"],
     [("high waist, squat-proof", "เอวสูง ไม่โป๊เวลาย่อ"), ("sweat-wicking", "ระบายเหงื่อ")]),
    ("sports bra", "training", "สปอร์ตบรา", ["Nike", "Adidas", "Under Armour", "Puma"], (690, 1890), ["XS", "S", "M", "L"],
     ["Swoosh Support", "Power Bra", "Studio Bra"],
     [("medium support", "ซัพพอร์ตระดับกลาง"), ("high support for running", "ซัพพอร์ตสูง เหมาะกับการวิ่ง")]),
    ("running jacket", "running", "แจ็คเก็ตวิ่ง", ["Nike", "Adidas", "The North Face", "Columbia"], (1490, 4990),
     ["S", "M", "L", "XL"], ["Wind Runner", "Rain Shell", "Packable"],
     [("water-repellent", "กันละอองน้ำ"), ("packs into its pocket", "พับเก็บในกระเป๋าได้")]),
    ("hiking backpack", "hiking", "กระเป๋าเป้เดินป่า", ["The North Face", "Columbia", "Decathlon Kalenji"], (990, 4990),
     ["20L", "30L"], ["Trail Pack", "Daypack", "Summit"],
     [("hydration sleeve", "มีช่องใส่ถุงน้ำ"), ("rain cover included", "มีผ้าคลุมกันฝน")]),
    ("hiking socks", "hiking", "ถุงเท้าเดินป่า", ["Columbia", "The North Face", "Nike"], (190, 590), ["S", "M", "L"],
     ["Merino Crew", "Trek Sock"], [("cushioned merino wool", "ขนแกะเมอริโน นุ่ม"), ("blister protection", "ลดการเสียดสี")]),
    ("swimsuit", "swimming", "ชุดว่ายน้ำ", ["Speedo", "Arena"], (890, 2990), ["S", "M", "L", "XL"],
     ["Endurance", "Powerback", "Race Suit"], [("chlorine resistant", "ทนคลอรีน"), ("quick dry", "แห้งเร็ว")]),
    ("swim goggles", "swimming", "แว่นตาว่ายน้ำ", ["Speedo", "Arena"], (390, 1590), ["one size"],
     ["Vision", "Mirror Racer", "Anti-Fog"], [("anti-fog lenses", "เลนส์กันฝ้า"), ("UV protection", "ป้องกันยูวี")]),
    ("badminton racket", "badminton", "ไม้แบดมินตัน", ["Yonex", "Li-Ning"], (1290, 7990), ["3U", "4U"],
     ["Astrox", "Nanoflare", "Windstorm"], [("head-heavy for power", "หัวหนัก ตบแรง"), ("light and fast", "เบา ตีไว")]),
    ("tennis racket", "tennis", "ไม้เทนนิส", ["Wilson", "Yonex"], (2490, 9990), ["G2", "G3"],
     ["Pro Staff", "Ezone", "Clash"], [("control frame", "เฟรมเน้นคอนโทรล"), ("oversize head for beginners", "หน้าไม้ใหญ่ เหมาะมือใหม่")]),
    ("yoga mat", "yoga", "เสื่อโยคะ", ["Adidas", "Puma", "Decathlon Kalenji"], (490, 2490), ["one size"],
     ["Grip Mat", "Travel Mat", "Thick Mat"], [("non-slip surface", "ผิวกันลื่น"), ("6 mm thick cushioning", "หนา 6 มม. นุ่ม")]),
    ("water bottle", "hiking", "ขวดน้ำ", ["Nike", "The North Face", "Decathlon Kalenji"], (290, 1290), ["500ml", "750ml"],
     ["Hydro Steel", "Squeeze Bottle"], [("insulated, keeps cold 24h", "เก็บความเย็น 24 ชม."), ("leak-proof", "กันรั่ว")]),
    ("running watch", "running", "นาฬิกาวิ่ง", ["Garmin"], (5990, 19990), ["one size"],
     ["Forerunner", "Pace GPS"], [("GPS and heart rate", "มี GPS และวัดชีพจร"), ("10-day battery", "แบตอยู่ 10 วัน")]),
    ("cap", "running", "หมวก", ["Nike", "Adidas", "Under Armour"], (390, 990), ["one size"],
     ["Run Cap", "Aero Cap"], [("sweat band", "มีแถบซับเหงื่อ"), ("lightweight", "น้ำหนักเบา")]),
    ("swim cap", "swimming", "หมวกว่ายน้ำ", ["Speedo", "Arena"], (290, 790), ["junior", "adult"],
     ["Ripple", "Pool Fit", "Streamline"], [("silicone stretch fit", "ซิลิโคนยืดหยุ่น"),
      ("room for long hair", "มีพื้นที่สำหรับผมยาว"), ("textured inner grip", "ผิวด้านในช่วยให้กระชับ")]),
    ("goalkeeper gloves", "football", "ถุงมือผู้รักษาประตู", ["Adidas", "Puma", "Nike"], (690, 2990),
     ["7", "8", "9", "10"], ["Box Keeper", "Goal Line", "Match Grip"],
     [("latex grip palm", "ฝ่ามือลาเท็กซ์ยึดเกาะดี"), ("adjustable wrist strap", "สายรัดข้อมือปรับได้"),
      ("padded fingers", "บุนวมนิ้วมือ")]),
    ("shin guards", "football", "สนับแข้ง", ["Nike", "Puma", "Adidas"], (290, 1190), ["S", "M", "L"],
     ["Pitch Shield", "Match Shell", "Flex Guard"], [("slip-in shell", "แผ่นป้องกันแบบสอด"),
      ("foam backing", "บุโฟมด้านหลัง"), ("ventilated shell", "มีช่องระบายอากาศ")]),
]

GENDERS = {"sports bra": ["women"], "leggings": ["women"], "swimsuit": ["men", "women"],
           "swim cap": ["unisex"], "goalkeeper gloves": ["unisex"], "shin guards": ["unisex"]}


def _price(rng: random.Random, lo: int, hi: int) -> int:
    return int(rng.randint(lo // 100, hi // 100) * 100 - 10)  # prices end in 90, as in Thai retail


def products(seed: int = SEED) -> list[dict]:
    """One row per model, colour and banner (Supersports or Central)."""
    rng = random.Random(seed)
    rows: list[dict] = []
    for ci, (cat, sport, cat_th, brands, (lo, hi), sizes, lines, feats) in enumerate(CATEGORIES):
        code = "".join(w[0] for w in cat.split()).upper() + f"{ci:02d}"
        n_models = 30 if cat in ("running shoes", "running t-shirt", "training shoes") else 22
        for m in range(n_models):
            brand = rng.choice(brands)
            line = rng.choice(lines)
            name = f"{brand} {line} {rng.randint(1, 9)}"
            model_id = f"{code}-{m:03d}"
            gender = rng.choice(GENDERS.get(cat, ["men", "women", "unisex"]))
            price = _price(rng, lo, hi)
            f1, f2 = rng.sample(feats, k=min(2, len(feats)))
            desc = f"{name} {cat} for {sport}. {f1[0].capitalize()}; {f2[0]}."
            # About a third of products have a Thai description, like a bilingual catalog.
            desc_th = (f"{cat_th} {BRAND_TH.get(brand, brand)} {f1[1]} {f2[1]}" if rng.random() < 0.35 else "")
            for color in rng.sample(COLORS, k=rng.randint(2, 5)):
                banners = ["Supersports"] + (["Central"] if rng.random() < 0.2 else [])  # same item on two sites
                for banner in banners:
                    prefix = "SS" if banner == "Supersports" else "CE"
                    rows.append({
                        "product_id": f"{prefix}-{model_id}-{color.upper()}",
                        "model_id": model_id, "model_name": name, "banner": banner, "name": f"{name} · {color}",
                        "brand": brand, "category": cat, "category_th": cat_th, "sport": sport, "gender": gender,
                        "color": color, "price": price, "sizes": sizes, "description": desc, "description_th": desc_th,
                    })
    for row in rows:
        if row["product_id"] in TRAIL_OFFERS:
            row["price"] = TRAIL_OFFERS[row["product_id"]]["price"]
    return rows


def stock(rows: list[dict], seed: int = SEED) -> list[tuple]:
    """(product_id, size, store, qty). About a quarter of product rows are out of stock everywhere."""
    rng = random.Random(seed + 1)
    out = []
    for p in rows:
        sold_out = rng.random() < 0.25
        offer = TRAIL_OFFERS.get(p["product_id"])
        for size in p["sizes"]:
            for store in STORES:
                qty = 0 if sold_out or rng.random() < 0.55 else rng.randint(1, 12)
                if offer:
                    qty = offer["stock"].get((size, store), 0)
                out.append((p["product_id"], size, store, qty))
    return out


def orders(rows: list[dict], now: datetime | None = None, seed: int = SEED) -> tuple[list[tuple], list[tuple]]:
    """Recent orders, with baskets grouped by seller and sport. Account u4 has no purchases."""
    rng = random.Random(seed + 2)
    now = now or datetime.now(timezone.utc)
    order_rows, items = [], []
    by_seller_sport = {}
    for p in rows:
        by_seller_sport.setdefault((p["banner"], p["sport"]), []).append(p)
    pools = list(by_seller_sport.values())
    for n in range(180):
        if n in (60, 61):  # the two fixed baskets below
            continue
        user = rng.choice(["u1", "u2", "u3", "u5", "u6", "u7", "u8"])
        created = now - timedelta(days=rng.uniform(0, 45), minutes=rng.randint(0, 600))
        age_days = (now - created).days
        status = ("cancelled" if rng.random() < 0.08 else "delivered" if age_days > 6
                  else "shipped" if age_days > 2 else "processing")
        oid = f"ORD-{10000 + n}"
        total = 0
        pool = rng.choice(pools)
        for p in rng.sample(pool, k=rng.randint(1, min(3, len(pool)))):
            qty = rng.choice((1, 1, 1, 1, 2, 3))
            items.append((oid, p["product_id"], rng.choice(p["sizes"]), qty, p["price"]))
            total += p["price"] * qty
        order_rows.append((oid, user, created.isoformat(timespec="seconds"), status, total))

    # Fixed baskets give quantity and status questions a repeatable answer on every reload.
    baskets = [
        ("ORD-10060", "u1", 8, "delivered", [("swim goggles", "one size", 3), ("swimsuit", "M", 1)]),
        ("ORD-10061", "u2", 2, "cancelled", [("hiking backpack", "20L", 1), ("hiking socks", "L", 2)]),
    ]
    for oid, user, days_ago, status, basket in baskets:
        basket_lines = []
        for category, size, qty in basket:
            p = next((p for p in rows if p["category"] == category and size in p["sizes"]), None)
            if p is None:  # a caller can generate orders from a subset of the catalog
                break
            basket_lines.append((oid, p["product_id"], size, qty, p["price"]))
        if len(basket_lines) != len(basket):
            continue
        items.extend(basket_lines)
        total = sum(qty * price for _, _, _, qty, price in basket_lines)
        created = now - timedelta(days=days_ago)
        order_rows.append((oid, user, created.isoformat(timespec="seconds"), status, total))
    return order_rows, items
