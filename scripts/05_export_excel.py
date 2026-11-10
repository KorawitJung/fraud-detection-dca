"""Export the result tables and sources to one Excel workbook. Run from the project root:
    py scripts/05_export_excel.py

Input : output/tables/*.csv, data/clean/cleaning_log.csv, data/reference/sources.csv
Output: output/results.xlsx

The full cleaned data (2.7 million rows) is larger than an Excel sheet allows, so the
workbook holds the summary tables. Re-create the cleaned file with scripts/01_preprocess.py.
"""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

T = Path("output/tables")
OUT = Path("output/results.xlsx")

OVERVIEW = [
    ("ชื่อ", "การฉ้อโกงการโอนเงินบนแพลตฟอร์มการเงินมือถือ (ข้อมูลจำลอง PaySim)"),
    ("คำถาม", "ธุรกรรมประเภทไหนและเวลาไหนที่มี fraud? เอาเงินไปเท่าไร? ธนาคารตรวจเฉพาะความเสี่ยงสูงสุดแล้วหยุดได้เท่าไร?"),
    ("ข้อมูลต้นทาง", "PaySim (Lopez-Rojas, Elmir, Axelsson 2016) ผ่าน Kaggle: ealaxi/paysim1 ดูชีต sources"),
    ("ข้อควรระวัง", "ข้อมูลเป็นการจำลอง ไม่ใช่ข้อมูลลูกค้าจริงและไม่ใช่ข้อมูลประเทศไทย ผลสะท้อนวิธีการ ไม่ใช่สถานการณ์จริง"),
    ("ขนาดข้อมูล", "ธุรกรรมทั้งหมด 6,362,620 รายการ หลังทำความสะอาด 2,770,409 รายการ (ประเภท CASH_OUT และ TRANSFER)"),
    ("ชีตในไฟล์นี้", "sources: แหล่งข้อมูลและลิงก์ | cleaning_log: ขั้นตอนการทำความสะอาด | fraud_by_type: Q1 | fraud_by_hour: Q2 | amount_summary: Q3 | model_metrics: ผลโมเดล | threshold_tradeoff: Q4"),
    ("ไฟล์ข้อมูลเต็ม", "ไม่แนบ (ใหญ่เกิน Excel) สร้างใหม่ด้วย scripts/00_download.py และ scripts/01_preprocess.py"),
]

TABLE_SHEETS = [
    ("fraud_by_type", "fraud_by_type.csv", "Q1: อัตราการเกิด fraud แยกตามประเภทธุรกรรม"),
    ("fraud_by_hour", "fraud_by_hour.csv", "Q2: จำนวนธุรกรรมและ fraud แยกตามชั่วโมงของวัน (step mod 24)"),
    ("amount_summary", "amount_summary.csv", "Q3: ขนาดเงินและสัดส่วนที่ทำให้บัญชีว่าง ของ fraud เทียบกับปกติ"),
    ("model_metrics", "model_metrics.csv", "ผลโมเดล: PR-AUC และ ROC-AUC บนช่วงเวลาที่ไม่เคยเห็น"),
    ("threshold_tradeoff", "threshold_tradeoff.csv", "Q4: ถ้าตรวจเฉพาะธุรกรรมเสี่ยงสูงสุด X% จะจับ fraud ได้เท่าไร"),
]

HEADER_FILL = PatternFill("solid", fgColor="14213D")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def write_sheet(writer, name, frame, note):
    """Note in row 1, table from row 3. Thai note is wrapped so it stays readable."""
    frame.to_excel(writer, sheet_name=name, index=False, startrow=2)
    ws = writer.sheets[name]
    ws["A1"] = note
    ws["A1"].font = Font(bold=True, size=12)
    for cell in ws[3]:
        if cell.value is not None:
            cell.fill, cell.font = HEADER_FILL, HEADER_FONT
            cell.alignment = Alignment(wrap_text=True, vertical="center")
    for col in range(1, ws.max_column + 1):
        width = max(len(str(c.value)) if c.value is not None else 0 for c in ws[get_column_letter(col)][2:])
        ws.column_dimensions[get_column_letter(col)].width = min(max(12, width + 2), 60)
    ws.freeze_panes = "A4"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        pd.DataFrame(OVERVIEW, columns=["หัวข้อ", "รายละเอียด"]).to_excel(writer, sheet_name="overview", index=False)
        ws = writer.sheets["overview"]
        ws.column_dimensions["A"].width = 18
        ws.column_dimensions["B"].width = 110
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

        src = pd.read_csv("data/reference/sources.csv")
        write_sheet(writer, "sources", src, "แหล่งข้อมูลและลิงก์ (ตรวจสอบเมื่อ 2026-11)")
        write_sheet(writer, "cleaning_log", pd.read_csv("data/clean/cleaning_log.csv"),
                    "ขั้นตอนการทำความสะอาดข้อมูลและจำนวนแถวที่เหลือ")
        for sheet, file, note in TABLE_SHEETS:
            write_sheet(writer, sheet, pd.read_csv(T / file), note)

    # Keep the number formats readable: percentages as %, money with separators.
    wb = load_workbook(OUT)
    pct_cols = {"fraud_rate", "share_emptying_account", "reviewed_share", "precision", "recall",
                "fraud_amount_caught_share", "pr_auc", "roc_auc", "baseline_pr_auc", "test_attack_share"}
    money_cols = {"total_amount", "median_amount", "mean_amount", "max_amount"}
    for ws in wb.worksheets[2:]:
        headers = {c.value: c.column_letter for c in ws[3] if c.value}
        for name, letter in headers.items():
            fmt = "0.00%" if name in pct_cols else "#,##0" if name in money_cols else None
            if fmt:
                for cell in ws[letter][3:]:
                    cell.number_format = fmt
    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
