"""Build the dashboards in English and Thai. Run from the project root: py scripts/04_dashboard.py

Input : data/clean/paysim_clean.csv and the tables in output/tables/
Output: docs/index.html (English), docs/th.html (ภาษาไทย). GitHub Pages serves both from /docs.

All numbers in the text are computed from the tables when the script runs, so the text
cannot drift from the charts. Each language has its own wording in TEXT below.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs_version

RED, BLUE, GREY = "#c1121f", "#2a6f97", "#b8bcc2"
T = Path("output/tables")

by_type = pd.read_csv(T / "fraud_by_type.csv").sort_values("fraud_rate")
by_hour = pd.read_csv(T / "fraud_by_hour.csv")
amounts = pd.read_csv(T / "amount_summary.csv").set_index("group")
metrics = pd.read_csv(T / "model_metrics.csv")
tradeoff = pd.read_csv(T / "threshold_tradeoff.csv")
clean = pd.read_csv("data/clean/paysim_clean.csv", usecols=["amount", "isFraud"])

n_all, n_fraud = int(by_type["transactions"].sum()), int(by_type["fraud"].sum())
best = metrics.sort_values("pr_auc", ascending=False).iloc[0]
other = metrics.sort_values("pr_auc", ascending=False).iloc[-1]
tb = tradeoff[tradeoff["model"] == best["model"]]
to = tradeoff[tradeoff["model"] == other["model"]]
one = tb[abs(tb["reviewed_share"] - 0.01) < 1e-9].iloc[0]
half = tb[abs(tb["reviewed_share"] - 0.005) < 1e-9].iloc[0]
one_other = to[abs(to["reviewed_share"] - 0.01) < 1e-9].iloc[0]
used = by_type[by_type["fraud"] > 0].sort_values("fraud_rate", ascending=False)
top, second = used.iloc[0], used.iloc[1]
clean_types = by_type[by_type["fraud"] == 0]["type"].tolist()
peak = by_hour.loc[by_hour["fraud_rate"].idxmax()]
day = by_hour[by_hour["hour"].between(9, 20)]
quiet = by_hour[by_hour["fraud_rate"] > 0.10]["hour"]
fs = by_hour["fraud"] / by_hour["fraud"].sum()
med_f, med_l = amounts.loc["Fraud", "median_amount"], amounts.loc["Legitimate", "median_amount"]
emp_f, emp_l = amounts.loc["Fraud", "share_emptying_account"], amounts.loc["Legitimate", "share_emptying_account"]


def pct(v):
    """Whole percent, except near 100% where rounding would claim a perfect score."""
    return f"{v:.2%}" if 0.995 <= v < 1 else f"{v:.0%}"


def fmt_th_num(x):
    return f"{x:,.0f}"


# Numbers shared by both languages.
N = dict(
    n_all=f"{n_all:,}", n_fraud=f"{n_fraud:,}", ratio=f"{round(n_all / n_fraud):,}",
    billion=f"{amounts.loc['Fraud', 'total_amount'] / 1e9:.1f}",
    top_type=top["type"], top_rate=f"{top['fraud_rate']:.2%}", top_n=f"{int(top['fraud']):,}",
    second_type=second["type"], second_rate=f"{second['fraud_rate']:.2%}", second_n=f"{int(second['fraud']):,}",
    clean_types=", ".join(clean_types),
    fs_min=f"{fs.min():.1%}", fs_max=f"{fs.max():.1%}",
    peak_hour=f"{int(peak['hour']):02d}:00", peak_rate=f"{peak['fraud_rate']:.0%}",
    day_rate=f"{day['fraud'].sum() / day['transactions'].sum():.2%}",
    q_from=f"{int(quiet.min()):02d}:00", q_to=f"{int(quiet.max()) + 1:02d}:00",
    med_f=fmt_th_num(med_f), med_l=fmt_th_num(med_l), med_ratio=f"{med_f / med_l:.1f}",
    emp_f=f"{emp_f:.1%}", emp_l=f"{emp_l:.1%}",
    test_rows=f"{int(best['test_rows']):,}", test_fraud=f"{int(best['test_fraud']):,}",
    one_alerts=f"{int(one['alerts']):,}", one_recall=pct(one["recall"]), one_prec=f"{one['precision']:.0%}",
    half_recall=f"{half['recall']:.0%}", other_name_en="logistic regression", other_name_th="logistic regression",
    other_recall=f"{one_other['recall']:.0%}",
)
N_KPI_BIG = N["one_recall"]

TEXT = {
    "en": dict(
        lang="en", title="When do scammers move money, and how much can a bank stop?",
        subtitle="Four plain questions about fraud in mobile-money transfers, answered with one month of simulated transactions (PaySim).",
        kpi=[(N["n_all"], "transactions in one simulated month"), (N["n_fraud"], "were fraud"),
             (f"1 in {N['ratio']}", "transactions is fraud"), (f"{N['billion']} billion", "taken by fraud (simulation currency)")],
        how="How to read this chart", says="What the data says", means="What it means",
        glossary=False, glossary_title="", note_title="Before you quote these numbers",
        note=["The data is <b>simulated</b>. It is modelled on a real mobile-money service but is not real customer data and not Thai data.",
              "Simulated fraud follows simple rules, so it is much easier to detect than real fraud. Treat Q4 as a demonstration of the method.",
              "Amounts are in the simulation's currency units."],
        sources=("Data: PaySim, Lopez-Rojas, Elmir and Axelsson (2016), via <a href=\"https://www.kaggle.com/datasets/ealaxi/paysim1\">Kaggle</a>. "
                 "Method: <a href=\"METHODOLOGY.md\">METHODOLOGY</a>. Excel: <a href=\"results.xlsx\">results.xlsx</a>."),
        switch='<a href="th.html">ภาษาไทย</a>', other_page="index.html",
        q=[
            dict(tag="Q1", question="Which kinds of transaction do fraudsters use?",
                 answer="Only two: transfers and cash-outs.",
                 shows="Each bar is one transaction type. Its length is the share of that type that turned out to be fraud. Red bars have fraud; grey bars have none.",
                 says="{top_type} is the riskiest type: {top_rate} of them are fraud ({top_n} cases). {second_type} follows at {second_rate} ({second_n} cases). {clean_types} have no fraud at all.",
                 means="Fraud here is about moving money out: send it to another account, then withdraw it as cash. That is the same two-step pattern as mule-account scams, so monitoring can concentrate on these two transaction types."),
            dict(tag="Q2", question="What time of day does fraud happen?",
                 answer="Fraud runs around the clock. Normal customers do not.",
                 shows="Top: blue bars show when all transfers and cash-outs happen during the day; red bars show when fraud happens. Each colour adds up to 100%. Bottom: of the transactions made in that hour, the share that is fraud.",
                 says="Fraud is spread almost evenly: every hour holds between {fs_min} and {fs_max} of it. Normal activity nearly stops overnight. So at {peak_hour}, {peak_rate} of transfers and cash-outs are fraud, against {day_rate} between 09:00 and 20:00.",
                 means="Fraudsters are not more active at night; there are simply very few honest customers awake to hide among. A large transfer between {q_from} and {q_to} deserves a second look. Hours assume the simulation starts at midnight."),
            dict(tag="Q3", question="How much do they take, and do they empty the account?",
                 answer="More than double the normal amount, and almost always the whole balance.",
                 shows="Left: how transaction sizes are distributed. The further right a curve sits, the larger the amounts. Right: the share of transactions that take everything the sender had.",
                 says="A typical (median) fraud transaction is {med_f}, against {med_l} for a legitimate one: {med_ratio} times larger. {emp_f} of fraud transactions empty the account, against {emp_l} of legitimate ones.",
                 means="The clearest warning sign is not the size of the transaction but that it takes the entire balance in one go."),
            dict(tag="Q4", question="If the bank checks only the riskiest transactions, how much fraud is stopped?",
                 answer="Checking the riskiest 1% catches {one_recall} of fraud, in this simulation.",
                 shows="A model gives every transaction a risk score. The bank cannot review everything, so it reviews only the highest-scoring ones. Each pair of bars is one review budget: red is the share of fraud cases inside that group, blue is the share of fraud money.",
                 says="Tested on a later period the model had not seen ({test_rows} transactions, {test_fraud} fraud). Reviewing the riskiest 1% ({one_alerts} transactions) catches {one_recall} of fraud cases, and {one_prec} of those reviews turn out to be real fraud. Reviewing 0.5% catches {half_recall}. A simpler model ({other_name_en}) catches {other_recall} of cases at 1%.",
                 means="A small, well-aimed review team can stop most fraud. But this result is far better than a real bank would see: the simulator creates fraud with a simple rule (take the whole balance), which a model learns almost perfectly."),
        ],
        labels=dict(type_x="Share of transactions that are fraud", hour_x="Hour of day",
                    top_y="When activity happens", bottom_y="Chance that a transfer or cash-out is fraud",
                    all_tx="All transactions", fraud="Fraud", legit="Legitimate",
                    amt_x="Amount per transaction (log scale: each step is 10 times larger)",
                    emp_y="Share that empties the sender's account", share_of_group="Share of the group",
                    review_x="Share of transactions the bank reviews", caught_cases="Fraud cases caught",
                    caught_money="Fraud money caught", no_fraud="0 cases", cases="cases"),
    ),
    "th": dict(
        lang="th", title="มิจฉาชีพโอนเงินเมื่อไร และธนาคารหยุดได้มากแค่ไหน?",
        subtitle="ตอบสี่คำถามง่าย ๆ เรื่องการโกงในการโอนเงินผ่านแอปการเงินมือถือ จากข้อมูลธุรกรรมจำลองหนึ่งเดือน (PaySim)",
        kpi=[(N["n_all"], "ธุรกรรมในหนึ่งเดือนจำลอง"), (N["n_fraud"], "รายการเป็นการโกง"),
             (f"1 ใน {N['ratio']}", "ของธุรกรรมคือการโกง"), (f"{N['billion']} พันล้าน", "ยอดเงินที่ถูกโกง (หน่วยของการจำลอง)")],
        how="วิธีอ่านกราฟนี้", says="ข้อมูลบอกอะไร", means="ความหมายคืออะไร",
        glossary=False, glossary_title="", note_title="ก่อนนำตัวเลขไปใช้",
        note=["ข้อมูลเป็น<b>ข้อมูลจำลอง</b> สร้างจากรูปแบบของบริการเงินมือถือจริง แต่ไม่ใช่ข้อมูลลูกค้าจริง และไม่ใช่ข้อมูลของประเทศไทย",
              "การโกงในข้อมูลจำลองเป็นไปตามกฎง่าย ๆ จึงตรวจจับได้ง่ายกว่าการโกงจริงมาก ให้ดูคำถามที่ 4 เป็นตัวอย่างของวิธีการ",
              "จำนวนเงินเป็นหน่วยของการจำลอง ไม่ใช่บาท"],
        sources=("ข้อมูล: PaySim, Lopez-Rojas, Elmir และ Axelsson (2016) จาก <a href=\"https://www.kaggle.com/datasets/ealaxi/paysim1\">Kaggle</a> "
                 "วิธีการ: <a href=\"METHODOLOGY_TH.docx\">คำอธิบายวิธีการ (Word)</a> ไฟล์ Excel: <a href=\"results.xlsx\">results.xlsx</a>"),
        switch='<a href="index.html">English</a>', other_page="th.html",
        q=[
            dict(tag="คำถามที่ 1", question="มิจฉาชีพใช้ธุรกรรมประเภทไหน?",
                 answer="มีเพียงสองประเภท: การโอนและการถอนเงินสด",
                 shows="แต่ละแท่งคือธุรกรรมหนึ่งประเภท ความยาวแท่งคือสัดส่วนของธุรกรรมประเภทนั้นที่เป็นการโกง แท่งสีแดงมีการโกง แท่งสีเทาไม่มีเลย",
                 says="{top_type} มีความเสี่ยงสูงสุด: {top_rate} ของรายการเป็นการโกง ({top_n} รายการ) รองลงมาคือ {second_type} ที่ {second_rate} ({second_n} รายการ) ประเภท {clean_types} ไม่มีการโกงเลย",
                 means="การโกงในที่นี้คือการย้ายเงินออก: โอนไปบัญชีอื่น แล้วถอนเป็นเงินสด เป็นรูปแบบเดียวกับบัญชีม้า จึงควรเฝ้าระวังสองประเภทนี้เป็นพิเศษ"),
            dict(tag="คำถามที่ 2", question="มิจฉาชีพโกงช่วงเวลาไหนของวัน?",
                 answer="การโกงเกิดตลอดเวลา แต่ลูกค้าปกติไม่ได้ทำธุรกรรมตลอดเวลา",
                 shows="ด้านบน: แท่งสีน้ำเงินแสดงช่วงเวลาที่มีการโอนและถอนเงินทั้งหมด แท่งสีแดงแสดงช่วงเวลาที่เกิดการโกง สีแต่ละสีรวมกันได้ 100% ด้านล่าง: ในชั่วโมงนั้น ธุรกรรมกี่เปอร์เซ็นต์เป็นการโกง",
                 says="การโกงกระจายเกือบเท่ากันทุกชั่วโมง โดยแต่ละชั่วโมงมีประมาณ {fs_min} ถึง {fs_max} ของการโกงทั้งหมด กิจกรรมปกติแทบหยุดตอนกลางคืน ดังนั้นตอน {peak_hour} มี {peak_rate} ของการโอนและถอนเงินเป็นการโกง เทียบกับ {day_rate} ระหว่าง 09:00 ถึง 20:00",
                 means="มิจฉาชีพไม่ได้ทำงานมากขึ้นตอนกลางคืน เพียงแต่มีลูกค้าปกติตื่นอยู่น้อยมากให้ปนไปด้วย การโอนจำนวนมากระหว่าง {q_from} ถึง {q_to} ควรถูกตรวจสอบเพิ่มเติม (ชั่วโมงในข้อมูลสมมติว่าการจำลองเริ่มตอนเที่ยงคืน)"),
            dict(tag="คำถามที่ 3", question="มิจฉาชีพเอาเงินไปเท่าไร และกวาดเงินทั้งบัญชีหรือไม่?",
                 answer="มากกว่าขนาดธุรกรรมปกติเกือบเท่าตัว และเกือบทุกครั้งเอาเงินทั้งบัญชี",
                 shows="ด้านซ้าย: การกระจายขนาดของธุรกรรม เส้นที่อยู่ทางขวามากกว่าหมายถึงจำนวนเงินที่มากกว่า ด้านขวา: สัดส่วนของธุรกรรมที่เอาเงินทั้งหมดที่ผู้โอนมี",
                 says="ธุรกรรมโกงขนาดกลาง (มัธยฐาน) อยู่ที่ {med_f} เทียบกับ {med_l} ของธุรกรรมที่ถูกต้อง มากกว่า {med_ratio} เท่า และ {emp_f} ของธุรกรรมที่เป็นการโกงทำให้บัญชีว่างเปล่า เทียบกับ {emp_l} ของธุรกรรมที่ถูกต้อง",
                 means="สัญญาณเตือนที่ชัดที่สุดไม่ใช่ขนาดของธุรกรรม แต่คือการที่ธุรกรรมเอาเงินทั้งหมดไปในครั้งเดียว"),
            dict(tag="คำถามที่ 4", question="ถ้าธนาคารตรวจเฉพาะธุรกรรมที่เสี่ยงสูงสุด จะหยุดการโกงได้เท่าไร?",
                 answer="การตรวจเฉพาะ 1% ที่เสี่ยงสูงสุดจับการโกงได้ {one_recall} ในการจำลองนี้",
                 shows="โมเดลให้คะแนนความเสี่ยงกับทุกธุรกรรม ธนาคารตรวจทุกรายการไม่ได้ จึงตรวจเฉพาะรายการที่คะแนนสูงสุด แต่ละคู่แท่งคือการตรวจหนึ่งระดับ: แท่งสีแดงคือสัดส่วนของการโกงที่อยู่ในกลุ่มนั้น แท่งสีน้ำเงินคือสัดส่วนของยอดเงินที่โกงที่อยู่ในกลุ่มนั้น",
                 says="ทดสอบกับช่วงเวลาหลังที่โมเดลไม่เคยเห็น ({test_rows} ธุรกรรม มีการโกง {test_fraud} รายการ) การตรวจ 1% ที่เสี่ยงสูงสุด ({one_alerts} ธุรกรรม) จับการโกงได้ {one_recall} และ {one_prec} ของรายการที่ตรวจเป็นการโกงจริง การตรวจ 0.5% จับได้ {half_recall} โมเดลที่ง่ายกว่า ({other_name_th}) จับได้ {other_recall} ที่ระดับ 1%",
                 means="ทีมตรวจสอบขนาดเล็กที่เลือกรายการได้ดีสามารถหยุดการโกงส่วนใหญ่ได้ แต่ผลนี้ดีกว่าที่ธนาคารจริงจะทำได้มาก เพราะตัวจำลองสร้างการโกงด้วยกฎง่ายเพียงข้อเดียว (เอาเงินทั้งบัญชี) ซึ่งโมเดลเรียนรู้ได้เกือบสมบูรณ์"),
        ],
        labels=dict(type_x="สัดส่วนของธุรกรรมที่เป็นการโกง", hour_x="ชั่วโมงของวัน",
                    top_y="กิจกรรมเกิดขึ้นเมื่อไร", bottom_y="โอนหรือถอนเงินแล้วมีโอกาสเป็นการโกงเท่าไร",
                    all_tx="ธุรกรรมทั้งหมด", fraud="การโกง", legit="ปกติ",
                    amt_x="ขนาดของธุรกรรม (สเกลลอการิทึม: แต่ละขั้นใหญ่กว่า 10 เท่า)",
                    emp_y="สัดส่วนที่เอาเงินทั้งบัญชี", share_of_group="สัดส่วนของกลุ่ม",
                    review_x="สัดส่วนของธุรกรรมที่ธนาคารตรวจ", caught_cases="จับการโกงได้ (รายการ)",
                    caught_money="จับยอดเงินที่โกงได้", no_fraud="0 รายการ", cases="รายการ"),
    ),
}


def layout(fig, height=380, **kw):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=60, b=10), template="plotly_white",
        font=dict(family="system-ui, -apple-system, Segoe UI, Sans Thai, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), **kw,
    )
    fig.update_yaxes(automargin=True, ticksuffix="  ")
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})


def charts(L):
    """Charts with labels in the requested language. Numbers and colours are identical."""
    b = L["labels"]
    fig = go.Figure(go.Bar(
        x=by_type["fraud_rate"], y=by_type["type"], orientation="h",
        marker_color=[RED if f > 0 else GREY for f in by_type["fraud"]],
        text=[f"{r:.2%} ({n:,} {b['cases']})" if n else f"{b['no_fraud']}" for r, n in zip(by_type["fraud_rate"], by_type["fraud"])],
        textposition="outside", cliponaxis=False,
    ))
    fig.update_xaxes(tickformat=".1%", title=b["type_x"], range=[0, by_type["fraud_rate"].max() * 1.5])
    q1 = layout(fig, 320)

    from plotly.subplots import make_subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=(b["top_y"], b["bottom_y"]))
    fig.add_bar(x=by_hour["hour"], y=by_hour["transactions"] / by_hour["transactions"].sum(), name=b["all_tx"],
                marker_color=BLUE, row=1, col=1)
    fig.add_bar(x=by_hour["hour"], y=by_hour["fraud"] / by_hour["fraud"].sum(), name=b["fraud"],
                marker_color=RED, row=1, col=1)
    fig.add_scatter(x=by_hour["hour"], y=by_hour["fraud_rate"], mode="lines+markers", line_color=RED,
                    showlegend=False, row=2, col=1)
    fig.update_yaxes(tickformat=".0%", row=1, col=1)
    fig.update_yaxes(tickformat=".0%", row=2, col=1)
    fig.update_xaxes(title=b["hour_x"], dtick=2, row=2, col=1)
    q2 = layout(fig, 520, barmode="group")

    import numpy as np
    bins = np.logspace(0, np.log10(clean["amount"].max() + 1), 60)
    mid = np.sqrt(bins[:-1] * bins[1:])
    fig = go.Figure()
    for label, flag, color in ((b["legit"], 0, BLUE), (b["fraud"], 1, RED)):
        counts, _ = np.histogram(clean.loc[clean["isFraud"] == flag, "amount"] + 1, bins=bins)
        fig.add_scatter(x=mid, y=counts / counts.sum(), name=label, mode="lines", line=dict(color=color, width=2),
                        fill="tozeroy")
    fig.update_xaxes(type="log", title=b["amt_x"])
    fig.update_yaxes(tickformat=".0%", title=b["share_of_group"])
    q3a = layout(fig, 360)

    fig = go.Figure(go.Bar(
        x=[b["fraud"], b["legit"]], y=[emp_f, emp_l], marker_color=[RED, BLUE],
        text=[f"{emp_f:.1%}", f"{emp_l:.1%}"], textposition="outside", cliponaxis=False,
    ))
    fig.update_yaxes(tickformat=".0%", range=[0, 1.12], title=b["emp_y"])
    q3b = layout(fig, 360)

    labels = [f"{s:.1%}" for s in tb["reviewed_share"]]
    fig = go.Figure()
    fig.add_bar(x=labels, y=tb["recall"], name=b["caught_cases"], marker_color=RED,
                text=[pct(v) for v in tb["recall"]], textposition="outside")
    fig.add_bar(x=labels, y=tb["fraud_amount_caught_share"], name=b["caught_money"], marker_color=BLUE,
                text=[pct(v) for v in tb["fraud_amount_caught_share"]], textposition="outside")
    fig.update_yaxes(tickformat=".0%", range=[0, 1.15])
    fig.update_xaxes(title=b["review_x"])
    q4 = layout(fig, 380, barmode="group")
    return [[q1], [q2], [q3a, q3b], [q4]]


def page(L):
    ch = charts(L)
    sections = "".join(
        f"""
<section id="q{i + 1}">
  <p class="tag">{q['tag']}</p>
  <h2>{q['question']}</h2>
  <p class="answer">{q['answer'].format(**N)}</p>
  <div class="charts {'two' if len(ch[i]) > 1 else 'one'}">{''.join(f'<div class="chart">{c}</div>' for c in ch[i])}</div>
  <dl>
    <dt>{L['how']}</dt><dd>{q['shows']}</dd>
    <dt>{L['says']}</dt><dd>{q['says'].format(**N)}</dd>
    <dt>{L['means']}</dt><dd>{q['means'].format(**N)}</dd>
  </dl>
</section>""" for i, q in enumerate(L["q"]))
    kpis = "".join(f'<div class="kpi"><b>{v}</b><span>{l}</span></div>' for v, l in L["kpi"])
    nav = "".join(f'<a href="#q{i + 1}">{"Q" + q["tag"][-1]}</a>' for i, q in enumerate(L["q"]))
    notes = "".join(f"<li>{n}</li>" for n in L["note"])
    font = "'Sarabun', 'Leelawadee UI', 'Tahoma', system-ui, sans-serif" if L["lang"] == "th" else "system-ui, -apple-system, 'Segoe UI', sans-serif"
    return f"""<!DOCTYPE html>
<html lang="{L['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{L['title']}</title>
<script src="https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js" charset="utf-8"></script>
<style>
  body {{ margin: 0; background: #f4f5f7; color: #1d2733; font: 16px/1.7 {font}; }}
  header {{ background: #14213d; color: #fff; padding: 40px 20px 28px; }}
  header h1 {{ margin: 0 0 8px; font-size: 30px; line-height: 1.3; }}
  header p {{ margin: 0; color: #c9d1dc; max-width: 760px; }}
  .wrap {{ max-width: 1040px; margin: 0 auto; padding: 0 20px; }}
  nav {{ margin-top: 18px; }}
  nav a, .switch {{ color: #fff; border: 1px solid #5b6a85; border-radius: 16px; padding: 3px 14px; margin-right: 8px; text-decoration: none; font-size: 14px; }}
  .switch {{ float: right; margin-right: 0; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin: 24px 0; }}
  .kpi, section, .note {{ background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(20, 33, 61, .12); }}
  .kpi {{ padding: 16px 18px; }}
  .kpi b {{ display: block; font-size: 26px; }}
  .kpi span {{ color: #5a6675; font-size: 14px; }}
  section {{ padding: 24px 26px; margin-bottom: 24px; }}
  .tag {{ margin: 0; color: {RED}; font-weight: 700; }}
  h2 {{ margin: 2px 0 6px; font-size: 23px; line-height: 1.3; }}
  .answer {{ margin: 0 0 12px; font-size: 18px; font-weight: 600; color: #14213d; }}
  .charts.two {{ display: grid; grid-template-columns: 3fr 2fr; gap: 12px; }}
  .chart {{ min-width: 0; }}
  dl {{ margin: 14px 0 0; border-top: 1px solid #e3e6ea; padding-top: 12px; }}
  dt {{ font-weight: 700; font-size: 14px; color: #5a6675; margin-top: 10px; }}
  dd {{ margin: 2px 0 0; }}
  .note {{ padding: 20px 26px; margin-bottom: 40px; border-left: 5px solid #e9a100; }}
  .note h2 {{ font-size: 19px; }}
  .note li {{ margin-bottom: 4px; }}
  @media (max-width: 760px) {{ .charts.two {{ grid-template-columns: 1fr; }} header h1 {{ font-size: 24px; }} }}
</style>
</head>
<body>
<header><div class="wrap">
  {L['switch']}
  <h1>{L['title']}</h1>
  <p>{L['subtitle']}</p>
  <nav>{nav}</nav>
</div></header>
<div class="wrap">
  <div class="kpis">{kpis}</div>
  {sections}
  <div class="note">
    <h2>{L['note_title']}</h2>
    <ul>{notes}</ul>
    <p>{L['sources']}</p>
  </div>
</div>
</body>
</html>
"""


Path("docs").mkdir(exist_ok=True)
Path("docs/index.html").write_text(page(TEXT["en"]), encoding="utf-8")
Path("docs/th.html").write_text(page(TEXT["th"]), encoding="utf-8")
# GitHub Pages serves only /docs, so the downloads linked from the pages are copied there.
import shutil

for name in ("results.xlsx", "METHODOLOGY_TH.docx"):
    src = Path("output") / name
    if src.exists():
        shutil.copy2(src, Path("docs") / name)
print("wrote docs/index.html and docs/th.html")
