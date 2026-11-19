"""Invented catalog copy. Each English detail is paired with the same fact in Thai."""

# One of these details supplements the two existing features of each generated model.
CATEGORY_DETAILS = {
    "running shoes": [
        ("A roomy toe box leaves space for toes to spread on long road runs.", "หน้าเท้ากว้าง เผื่อพื้นที่ให้นิ้วเท้าขยับเวลาวิ่งไกลบนถนน"),
        ("A close-fitting heel cup keeps the heel seated on tight turns.", "เบ้าส้นกระชับ ช่วยให้ส้นเท้าไม่หลุดเวลาเลี้ยวโค้ง")],
    "trail running shoes": [
        ("Deep, widely spaced lugs shed mud on soft trails.", "ดอกยางลึกและเว้นระยะห่าง ช่วยสลัดโคลนบนทางดินนิ่ม"),
        ("A reinforced toe cap shields the front of the foot on rocky descents.", "หุ้มปลายเท้าด้วยวัสดุเสริม เหมาะกับทางลงเขาที่มีหิน")],
    "training shoes": [
        ("Rubber wraps up the sides for rope climbs in the gym.", "ขอบยางหุ้มด้านข้างสำหรับการฝึกปีนเชือกในยิม"),
        ("A broad heel platform gives a stable base for squats.", "ฐานส้นกว้าง ช่วยให้ยืนมั่นคงขณะทำสควอต")],
    "football boots": [
        ("An offset lace channel leaves a smooth instep for striking the ball.", "แนวเชือกรองเท้าเยื้องไปด้านข้าง ทำให้หลังเท้าเรียบเวลายิงบอล"),
        ("A textured instep gives feedback when receiving a short pass.", "ผิวสัมผัสบริเวณหลังเท้าช่วยให้รู้จังหวะสัมผัสลูกเมื่อรับบอลสั้น")],
    "badminton shoes": [
        ("The toe has a wear patch for players who drag the trailing foot on lunges.", "เสริมแผ่นกันสึกที่ปลายเท้า สำหรับคนที่ลากเท้าหลังตอนก้าวรับลูก"),
        ("A ventilated tongue lets heat escape during indoor doubles practice.", "ลิ้นรองเท้ามีช่องระบายความร้อน เหมาะกับการซ้อมประเภทคู่ในร่ม")],
    "running t-shirt": [
        ("Flat seams sit smoothly under a running vest on long outings.", "ตะเข็บแบน ใส่เสื้อกั๊กวิ่งทับได้สบายเมื่อต้องวิ่งนาน"),
        ("Mesh panels under the arms release heat on humid days.", "แผงผ้าตาข่ายใต้รักแร้ช่วยระบายความร้อนในวันอากาศอบอ้าว")],
    "polo shirt": [
        ("Side vents let the hem move as the wearer turns through a golf swing.", "ชายเสื้อผ่าด้านข้าง ช่วยให้หมุนตัวตอนสวิงกอล์ฟได้สะดวก"),
        ("A firm ribbed collar holds its shape during a full round of golf.", "ปกเสื้อผ้าริบอยู่ทรงตลอดการออกรอบ")],
    "training shorts": [
        ("A drawcord inside the waistband makes the fit adjustable between sets.", "มีเชือกผูกซ่อนในขอบเอว ปรับความกระชับระหว่างเซ็ตได้"),
        ("Side splits give the thighs room for deep lunges.", "ผ่าชายขาด้านข้างเพื่อให้ก้าวย่อตัวได้ลึก")],
    "leggings": [
        ("A thigh pocket holds a phone flat against the leg on walks.", "กระเป๋าข้างต้นขาช่วยเก็บโทรศัพท์ให้แนบขาขณะเดิน"),
        ("The ankle-length cut covers the lower leg during floor stretches.", "ขายาวถึงข้อเท้า ช่วยคลุมหน้าแข้งเวลานั่งยืดเหยียดบนพื้น")],
    "sports bra": [
        ("High support for running. A front zip makes the bra easier to take off after a sweaty workout.", "ให้การรองรับระดับสูงสำหรับวิ่ง ซิปด้านหน้าช่วยให้ถอดง่ายหลังออกกำลังกายจนเหงื่อออก"),
        ("Medium support for studio workouts. Adjustable shoulder straps let the wearer fine-tune the fit.", "ให้การรองรับระดับปานกลางสำหรับออกกำลังกายในสตูดิโอ ปรับความยาวสายบ่าให้พอดีได้")],
    "running jacket": [
        ("Thumb loops keep the sleeves in place on windy morning runs.", "ห่วงสอดนิ้วโป้งช่วยยึดแขนเสื้อเวลาวิ่งเช้าที่ลมแรง"),
        ("A vent across the back releases heat while the front is zipped.", "ช่องระบายอากาศด้านหลังช่วยถ่ายเทความร้อนแม้รูดซิปหน้าจนสุด")],
    "hiking backpack": [
        ("Two stretch side pockets keep bottles within reach on the trail.", "ช่องยืดด้านข้างสองช่องช่วยให้หยิบขวดน้ำได้สะดวกระหว่างเดินป่า"),
        ("External loops secure trekking poles when both hands are needed.", "ห่วงด้านนอกใช้ยึดไม้เท้าเดินป่าเมื่อต้องใช้มือทั้งสองข้าง")],
    "hiking socks": [
        ("A flat toe seam sits smoothly inside close-fitting hiking boots.", "ตะเข็บปลายเท้าแบบแบน เหมาะกับรองเท้าเดินป่าทรงกระชับ"),
        ("A reinforced heel adds durability where the boot rubs on climbs.", "เสริมส้นถุงเท้าตรงจุดที่เสียดสีกับรองเท้าเวลาเดินขึ้นเขา")],
    "swimsuit": [
        ("A full front lining adds coverage in the pool.", "ซับในเต็มด้านหน้าช่วยให้ชุดปกปิดดีขึ้นเมื่อลงสระ"),
        ("Flat seams reduce rubbing during repeated laps.", "ตะเข็บแบนช่วยลดการเสียดสีเมื่อว่ายหลายรอบ")],
    "swim goggles": [
        ("A split strap spreads tension across the back of the head.", "สายรัดแยกสองเส้นช่วยกระจายแรงรัดบริเวณท้ายทอย"),
        ("Soft eye seals sit close to the face during lap training.", "ขอบแว่นนุ่มแนบใบหน้า เหมาะกับการว่ายฝึกซ้อมในสระ")],
    "badminton racket": [
        ("A flexible shaft suits a smooth swing when clearing to the back court.", "ก้านยืดหยุ่น เหมาะกับวงสวิงต่อเนื่องเมื่อตีลูกโด่งไปท้ายคอร์ต"),
        ("A stiff shaft gives a direct response on fast, compact drives.", "ก้านแข็งตอบสนองไวเมื่อตีลูกดาดด้วยวงสวิงสั้น")],
    "tennis racket": [
        ("An open string pattern helps players brush up on topspin shots.", "หน้าเอ็นแบบห่างช่วยให้ปาดลูกเพื่อสร้างท็อปสปินได้ง่าย"),
        ("A dense string pattern gives a predictable response on flat shots.", "หน้าเอ็นถี่ช่วยให้คุมทิศทางได้สม่ำเสมอเมื่อตีลูกแบน")],
    "yoga mat": [
        ("A carrying strap keeps the mat together on the way to class.", "มีสายรัดสำหรับพกเสื่อไปเรียนโยคะ"),
        ("A wipe-clean surface makes it easy to clean after practice.", "พื้นผิวเช็ดทำความสะอาดง่ายหลังฝึก")],
    "water bottle": [
        ("A wide opening fits ice cubes and a washing brush.", "ปากขวดกว้าง ใส่น้ำแข็งก้อนและสอดแปรงล้างขวดได้"),
        ("A flip spout opens with one hand while walking.", "ฝาจุกแบบพับเปิดได้ด้วยมือเดียวขณะเดิน")],
    "running watch": [
        ("Vibration lap alerts can be felt without looking down at the screen.", "ระบบสั่นเตือนเมื่อครบรอบ ช่วยให้รู้ระยะโดยไม่ต้องก้มมองหน้าจอ"),
        ("Physical buttons let the runner pause a session with wet fingers.", "ปุ่มกดจริงช่วยให้หยุดบันทึกการวิ่งได้แม้นิ้วเปียก")],
    "cap": [
        ("A soft brim folds into a vest pocket when the sun goes down.", "ปีกหมวกนิ่ม พับใส่กระเป๋าเสื้อกั๊กได้เมื่อแดดร่ม"),
        ("A stiff curved brim shades the eyes without flapping in the wind.", "ปีกโค้งแข็งช่วยบังแดดและไม่กระพือเมื่อลมแรง")],
    "swim cap": [
        ("A smooth outer surface slides under a goggle strap.", "ผิวด้านนอกเรียบ ช่วยให้เลื่อนสายแว่นว่ายน้ำเข้าที่ได้ง่าย"),
        ("A thicker rim helps the edge stay in place during turns.", "ขอบหมวกหนาช่วยให้หมวกอยู่กับที่ตอนกลับตัวในสระ")],
    "goalkeeper gloves": [
        ("A pull tab at the cuff helps the keeper put the second glove on.", "หูดึงที่ข้อมือช่วยให้สวมถุงมือข้างที่สองได้ง่าย"),
        ("A breathable mesh back lets heat escape between saves.", "หลังมือผ้าตาข่ายช่วยระบายความร้อนระหว่างรอรับลูก")],
    "shin guards": [
        ("A fabric sleeve holds the guard in place under football socks.", "ปลอกผ้าช่วยยึดสนับแข้งให้อยู่กับที่ใต้ถุงเท้าฟุตบอล"),
        ("A narrow lower edge leaves room for ankle movement.", "ขอบล่างทรงแคบ เว้นพื้นที่ให้ขยับข้อเท้าได้สะดวก")],
}

# Close alternatives within a brand. These complete descriptions replace the generic
# features so a model cannot inherit a contradictory thickness, lens or accessory.
MODEL_DETAILS = {
    "SG14-000": ("Clear untinted lenses admit light in dim indoor pools so lane lines remain visible after dark. Soft seals fit around the eyes.",
                 "เลนส์ใสไม่มีสี ให้แสงผ่านได้มาก เห็นเส้นก้นสระชัดเมื่อซ้อมในร่มตอนค่ำ ขอบแว่นนุ่มแนบรอบดวงตา"),
    "SG14-001": ("Dark mirrored lenses reduce reflected glare from the water in bright outdoor pools. The split strap steadies the goggles on turns.",
                 "เลนส์ปรอทสีเข้มช่วยลดแสงจ้าที่สะท้อนจากผิวน้ำ เหมาะกับสระกลางแจ้งช่วงแดดจัด สายรัดสองเส้นช่วยให้แว่นกระชับตอนกลับตัว"),
    "SG14-010": ("Three interchangeable nose bridges adjust the distance between the eye cups. Choose the wider bridge if the goggles pinch the nose.",
                 "มีสะพานจมูกให้เปลี่ยนสามขนาดเพื่อปรับระยะห่างระหว่างเลนส์ หากแว่นบีบสันจมูกให้เปลี่ยนเป็นชิ้นที่กว้างขึ้น"),
    "HB11-004": ("A suspended mesh back panel holds the pack away from the spine. Air flows through the gap on hot, humid climbs.",
                 "แผงตาข่ายขึงตึงเว้นช่องระหว่างเป้กับแผ่นหลัง ลมไหลผ่านช่องนี้ได้เวลาเดินขึ้นเขาในอากาศร้อนชื้น"),
    "HB11-011": ("A separate bottom zip opens into the main compartment. Pull a jacket out from the base while the top stays packed.",
                 "มีซิปแยกใต้เป้ที่เปิดถึงช่องหลัก หยิบเสื้อจากก้นเป้ได้โดยไม่ต้องรื้อของที่วางทับอยู่ด้านบน"),
    "HB11-016": ("A two-litre drinking reservoir and hose are included. The hose clips to the shoulder strap for sipping while walking.",
                 "ในชุดมีถุงน้ำความจุสองลิตรพร้อมสายดูด สายยึดกับสายสะพายไหล่ได้ จึงจิบน้ำระหว่างเดินโดยไม่ต้องถอดเป้"),
    "GG22-002": ("Soft wet-grip latex on the palm helps catch a slick ball in rainy matches. Rinse the palm after play on muddy grass.",
                 "ฝ่ามือใช้ลาเท็กซ์เนื้อนุ่มสำหรับจับลูกบอลเปียกตอนแข่งกลางฝน หลังเล่นบนสนามหญ้าที่มีโคลนควรล้างฝ่ามือถุงมือ"),
    "GG22-007": ("An abrasion-resistant palm withstands repeated contact with coarse artificial turf. Dense latex favours durability for daily training.",
                 "ฝ่ามือใช้ลาเท็กซ์เนื้อแน่นทนการเสียดสีกับหญ้าเทียมผิวหยาบ เหมาะกับการซ้อมทุกวันที่ทำให้ฝ่ามือถุงมือสึกเร็ว"),
    "GG22-009": ("Removable finger spines sit in pockets along the back of the fingers. Slide them out for a more flexible glove during drills.",
                 "ก้านดามนิ้วสอดอยู่ในช่องด้านหลังนิ้วแต่ละนิ้ว ถอดก้านออกได้เมื่อต้องการให้ถุงมืองอนิ้วง่ายขึ้นตอนซ้อม"),
    "YM17-006": ("A thin 2 mm mat has scored folds that pack flat into a suitcase. Its rectangular folded shape fits between layers of clothing.",
                 "เสื่อบาง 2 มม. มีรอยพับสำหรับพับเป็นสี่เหลี่ยมแบน สอดไว้ระหว่างเสื้อผ้าในกระเป๋าเดินทางได้"),
    "YM17-002": ("A 12 mm foam base cushions the knees against hard tile during kneeling poses. The thick mat rolls up for storage.",
                 "ฐานโฟมหนา 12 มม. รองเข่าเมื่อต้องคุกเข่าบนพื้นกระเบื้องแข็งเป็นเวลานาน ม้วนเก็บหลังใช้งานได้"),
    "YM17-003": ("Printed alignment lines mark hand and foot positions for standing poses. A central line helps keep both sides even.",
                 "มีเส้นบอกตำแหน่งมือและเท้าบนเสื่อสำหรับฝึกท่ายืน เส้นกึ่งกลางช่วยให้วางเท้าซ้ายและขวาได้สมดุล"),
}
