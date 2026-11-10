"""Write the Thai methodology document as Word. Run from the project root: py scripts/06_build_word.py

Input : data/reference/sources.csv and the numbers in output/tables/
Output: output/METHODOLOGY_TH.docx (copied to docs/ by 04_dashboard.py)
"""
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

OUT = Path("output/METHODOLOGY_TH.docx")
T = Path("output/tables")

by_type = pd.read_csv(T / "fraud_by_type.csv")
amounts = pd.read_csv(T / "amount_summary.csv").set_index("group")
metrics = pd.read_csv(T / "model_metrics.csv")
tradeoff = pd.read_csv(T / "threshold_tradeoff.csv")
sources = pd.read_csv("data/reference/sources.csv")
best = metrics.sort_values("pr_auc", ascending=False).iloc[0]
tb = tradeoff[tradeoff["model"] == best["model"]]
one = tb[abs(tb["reviewed_share"] - 0.01) < 1e-9].iloc[0]
half = tb[abs(tb["reviewed_share"] - 0.005) < 1e-9].iloc[0]
n_all = int(by_type["transactions"].sum())
n_fraud = int(by_type["fraud"].sum())
clean_log_last = pd.read_csv("data/clean/cleaning_log.csv")["rows"].iloc[-1]

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Leelawadee UI"
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn("w:eastAsia"), "Leelawadee UI")
doc.styles["Normal"].paragraph_format.space_after = Pt(6)


def h(text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.name = "Leelawadee UI"
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Leelawadee UI")


def para(text):
    doc.add_paragraph(text)


def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    for i, head in enumerate(headers):
        t.rows[0].cells[i].text = head
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
    doc.add_paragraph()


title = doc.add_heading("การตรวจจับการโกงในการโอนเงินผ่านแอปการเงินมือถือ", 0)
para("คำอธิบายวิธีการทำงานทั้งหมด: การเก็บข้อมูล การทำความสะอาด การวิเคราะห์ และการสร้าง dashboard")
para("ข้อมูลที่ใช้: PaySim (ข้อมูลจำลอง) ผ่าน Kaggle ดูหัวข้อ 2 สำหรับลิงก์และสิทธิ์การใช้งาน")

h("1. คำถามของโปรเจกต์")
para("โปรเจกต์นี้ตอบสี่คำถามง่าย ๆ จากธุรกรรมจำลองหนึ่งเดือน:")
bullets([
    "คำถามที่ 1: มิจฉาชีพใช้ธุรกรรมประเภทไหน",
    "คำถามที่ 2: การโกงเกิดขึ้นช่วงเวลาไหนของวัน",
    "คำถามที่ 3: มิจฉาชีพเอาเงินไปเท่าไร และเอาเงินทั้งบัญชีหรือไม่",
    "คำถามที่ 4: ถ้าธนาคารตรวจเฉพาะธุรกรรมที่เสี่ยงที่สุด จะหยุดการโกงได้เท่าไร",
])
para("เหตุผลที่เลือกหัวข้อนี้: รูปแบบการโกงในข้อมูลคือการโอนเงินเข้าบัญชีปลายทางแล้วถอนเป็นเงินสดทันที ซึ่งคล้ายกับการใช้บัญชีม้าในการรับเงินโกง")

h("2. แหล่งข้อมูล")
para("ข้อมูลหลักคือ PaySim ซึ่งสร้างจากบันทึกธุรกรรมของบริการเงินมือถือจริงด้วยการจำลอง:")
rows = [(r["name"], r["role"], r["url"], r["licence_note"]) for _, r in sources.iterrows()]
table(["ชื่อ", "บทบาท", "ลิงก์", "หมายเหตุสิทธิ์การใช้"], rows)
para("ข้อควรระวัง: ข้อมูลเป็นการจำลอง ไม่ใช่ข้อมูลลูกค้าจริง และไม่ใช่ข้อมูลของประเทศไทย ผลที่ได้สะท้อนวิธีการ ไม่ใช่สถานการณ์การโกงจริงในไทย")

h("3. การเก็บข้อมูล")
para("สคริปต์ scripts/00_download.py ดาวน์โหลดไฟล์ผ่านไลบรารี kagglehub ไปยังโฟลเดอร์ data/raw/ ไฟล์ดิบไม่ถูกเก็บใน GitHub เพราะมีขนาดประมาณ 500 MB")
para("ไฟล์มี 6,362,620 ธุรกรรม และคอลัมน์ได้แก่ step (ชั่วโมงในการจำลอง), type (ประเภทธุรกรรม), amount, ยอดก่อนและหลังของผู้ส่งและผู้รับ, และ isFraud (ป้ายกำกับ 1 = การโกง)")

h("4. การทำความสะอาดข้อมูล")
para("สคริปต์ scripts/01_preprocess.py ทำตามขั้นตอนนี้ และบันทึกจำนวนแถวหลังแต่ละขั้นไว้ใน data/clean/cleaning_log.csv")
table(["ขั้นตอน", "กฎ"], [
    ("เปลี่ยนชื่อคอลัมน์", "oldbalanceOrg เป็น oldbalanceOrig ให้สอดคล้องกัน"),
    ("ลบแถวซ้ำ", "ลบแถวที่เหมือนกันทุกคอลัมน์ (ไม่พบในชุดนี้)"),
    ("ลบแถวที่ขาดข้อมูลสำคัญ", "ขาด step, type, amount, ชื่อบัญชี หรือป้ายกำกับ (ไม่พบในชุดนี้)"),
    ("ลบยอดเงินติดลบ", "amount < 0 (ไม่พบในชุดนี้)"),
    ("เลือกประเภทธุรกรรม", "เก็บเฉพาะประเภทที่มีการโกง คือ TRANSFER และ CASH_OUT ประเภทอื่นไม่มีการโกงเลย"),
    ("แบ่งข้อมูลตามเวลา", "80% แรกของธุรกรรมเรียงตามเวลาเป็นชุดฝึก ที่เหลือเป็นชุดทดสอบ"),
])
para(f"ผลลัพธ์: ธุรกรรมหลังทำความสะอาด {int(clean_log_last):,} รายการ จาก {n_all:,} รายการ มีการโกง {n_fraud:,} รายการ")

h("5. คุณสมบัติที่ใช้ในโมเดล")
para("ใช้เฉพาะข้อมูลที่รู้ก่อนธุรกรรมจะเสร็จสิ้น เพื่อให้โมเดลใช้ได้ในระบบจริง ได้แก่ ขนาดเงินแบบลอการิทึม สัดส่วนของเงินต่อยอดบัญชีผู้ส่ง การที่ธุรกรรมทำให้บัญชีว่างหรือไม่ ยอดตั้งต้นของผู้ส่งและผู้รับ ชั่วโมงของวัน ผู้รับเป็นร้านค้าหรือไม่ จำนวนและยอดรวมที่ผู้รับเคยได้รับก่อนหน้า และประเภทธุรกรรม")
para("คุณสมบัติที่คำนวณจากยอดหลังธุรกรรม (orig_balance_error, dest_balance_error) ไม่ถูกใช้ในโมเดล เพราะระบบจริงยังไม่รู้ค่านี้ตอนตัดสินใจ และในข้อมูลนี้มันรั่วป้ายกำกับได้โดยตรง")

h("6. วิธีวิเคราะห์และผลลัพธ์")
h("คำถามที่ 1: ประเภทธุรกรรม", 2)
para(f"การโกงเกิดใน TRANSFER {by_type.loc[by_type['type'] == 'TRANSFER', 'fraud_rate'].iloc[0]:.2%} ของธุรกรรมประเภทนี้ และใน CASH_OUT {by_type.loc[by_type['type'] == 'CASH_OUT', 'fraud_rate'].iloc[0]:.2%} ประเภทอื่นไม่มีการโกงเลย")
h("คำถามที่ 2: ช่วงเวลา", 2)
para("การโกงกระจายเกือบเท่ากันทุกชั่วโมง แต่ลูกค้าปกติแทบไม่ทำธุรกรรมระหว่าง 02:00 ถึง 07:00 ทำให้ในช่วงนั้นธุรกรรมโอนและถอนส่วนใหญ่เป็นการโกง (ประมาณ 58% ตอน 05:00) ชั่วโมงในข้อมูลสมมติว่าการจำลองเริ่มตอนเที่ยงคืน ซึ่งข้อมูลไม่ได้ยืนยัน")
h("คำถามที่ 3: ขนาดเงินและการกวาดบัญชี", 2)
para(f"ค่ามัธยฐานของธุรกรรมโกงคือ {amounts.loc['Fraud', 'median_amount']:,.0f} เทียบกับ {amounts.loc['Legitimate', 'median_amount']:,.0f} ของธุรกรรมปกติ {amounts.loc['Fraud', 'share_emptying_account']:.1%} ของธุรกรรมโกงทำให้บัญชีผู้ส่งว่างเปล่า เทียบกับ {amounts.loc['Legitimate', 'share_emptying_account']:.1%} ของธุรกรรมปกติ")
h("คำถามที่ 4: การตรวจเฉพาะความเสี่ยงสูงสุด", 2)
para("แบ่งข้อมูลตามเวลา ฝึกโมเดลสองแบบ (logistic regression และ gradient boosting) ด้วยการถ่วงน้ำหนักให้ชั้นที่พบน้อย ประเมินบนช่วง 20% หลัง เรียงธุรกรรมตามคะแนนเสี่ยง แล้วดูว่าการตรวจกลุ่มบนสุดจับการโกงได้เท่าไร")
para(f"โมเดลที่ดีกว่าคือ {best['model']} บนชุดทดสอบ {int(best['test_rows']):,} ธุรกรรม มีการโกง {int(best['test_fraud']):,} รายการ ตรวจ 1% ที่เสี่ยงที่สุด ({int(one['alerts']):,} รายการ) จับการโกงได้ {one['recall']:.2%} และ {one['precision']:.0%} ของรายการที่ตรวจเป็นการโกงจริง ตรวจ 0.5% จับได้ {half['recall']:.0%}")
para("ผลนี้ดีกว่าที่ธนาคารจริงจะทำได้มาก เพราะตัวจำลองสร้างการโกงด้วยกฎง่ายเพียงข้อเดียวคือเอาเงินทั้งบัญชี โมเดลจึงเรียนรู้ได้เกือบสมบูรณ์")

h("7. ข้อจำกัด")
bullets([
    "ข้อมูลเป็นการจำลอง พฤติกรรมการโกงถูกสร้างจากกฎ จึงตรวจจับได้ง่ายกว่าการโกงจริง",
    "ไม่มีข้อมูลลูกค้า อุปกรณ์ หรือช่องทางการทำธุรกรรม",
    "ตัวแปรความถี่ของผู้รับคำนวณตามลำดับเวลาโดยไม่มองไปข้างหน้า แต่บัญชีไม่ได้แยกระหว่างชุดฝึกและชุดทดสอบ",
    "ชั่วโมงของวันเป็นสมมติฐาน",
    "ไม่ได้ตรวจสอบกับข้อมูลการโกงในประเทศไทย ดูหมายเหตุในหัวข้อ 8",
])

h("8. บริบทไทยและงานต่อยอด")
para("แหล่งข้อมูลไทยในโปรเจกต์นี้ ได้แก่ สถิติของธนาคารแห่งประเทศไทย และ data.go.th ซึ่งเป็นหน้ารวม ยังไม่พบชุดข้อมูลการโกงรายละเอียดที่ใช้วิเคราะห์ได้ในขณะที่จัดทำ จึงยังไม่ได้เปรียบเทียบกับไทยโดยตรง")

h("9. วิธีรันซ้ำ")
para("ติดตั้ง: pip install -r requirements.txt แล้วรันตามลำดับ:")
bullets([
    "py scripts/00_download.py",
    "py scripts/01_preprocess.py",
    "py scripts/02_eda.py",
    "py scripts/03_model.py",
    "py scripts/04_dashboard.py",
    "py scripts/05_export_excel.py",
    "py scripts/06_build_word.py",
])

h("10. ไฟล์ในโปรเจกต์")
table(["ไฟล์", "เนื้อหา"], [
    ("docs/index.html", "Dashboard ภาษาอังกฤษ"),
    ("docs/th.html", "Dashboard ภาษาไทย"),
    ("output/results.xlsx", "ตารางผลลัพธ์และแหล่งข้อมูลใน Excel"),
    ("output/METHODOLOGY_TH.docx", "เอกสารนี้"),
    ("output/png/", "กราฟแบบภาพนิ่ง"),
])

for p in doc.paragraphs:
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("wrote", OUT)
