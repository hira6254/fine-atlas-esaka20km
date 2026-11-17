#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINE ATLAS — 江坂20km圏内 お魚カスタム定期便 営業図鑑 & Excelリスト生成スクリプト
Reads `stores_master.json` and generates:
1. `data.js` for the Web Application
2. `2_江坂20km圏内_営業リスト_ファインアトラス定期便.xlsx` (3-sheet executive & field workbook)
"""

import json
import math
import os
import shutil
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, Reference

ESAKA_LAT = 34.7588
ESAKA_LNG = 135.4969

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_JSON = os.path.join(BASE_DIR, "scripts", "stores_master.json")
OUT_DATA_JS = os.path.join(BASE_DIR, "data.js")
OUT_XLSX = os.path.join(BASE_DIR, "2_江坂20km圏内_営業リスト_ファインアトラス定期便.xlsx")
WORKSPACE_XLSX = "/home/antigravity/2_江坂20km圏内_営業リスト_ファインアトラス定期便.xlsx"


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sanitize_cell_text(val):
    if isinstance(val, str) and val and val[0] in ("=", "+", "-"):
        return "'" + val
    return val


def build_excel(master):
    stores = master["stores"]
    playbook = master["playbook"]

    wb = openpyxl.Workbook()

    # Palette (matching Tomita-kun's Hokkaido sheet & Pisces Ocean Craft)
    navy_dark = PatternFill("solid", fgColor="0F2940")
    navy_mid = PatternFill("solid", fgColor="1E3F5E")
    slate_sub = PatternFill("solid", fgColor="E8EFF5")
    zebra_fill = PatternFill("solid", fgColor="F7FAFC")
    rank_s_fill = PatternFill("solid", fgColor="FDF2F2")
    rank_a_fill = PatternFill("solid", fgColor="EFF8FF")
    recipe_fill = PatternFill("solid", fgColor="FFFBEB")
    kpi_card_fill = PatternFill("solid", fgColor="F0F7FA")

    font_title = Font(name="Meiryo UI", size=14, bold=True, color="FFFFFF")
    font_sub = Font(name="Meiryo UI", size=9.5, bold=False, color="1E3F5E")
    font_th = Font(name="Meiryo UI", size=9.5, bold=True, color="FFFFFF")
    font_sec = Font(name="Meiryo UI", size=10.5, bold=True, color="0F2940")
    font_body = Font(name="Meiryo UI", size=9.5, color="1F2328")
    font_bold = Font(name="Meiryo UI", size=9.5, bold=True, color="0F2940")
    font_rank_s = Font(name="Meiryo UI", size=10, bold=True, color="B91C1C")
    font_rank_a = Font(name="Meiryo UI", size=10, bold=True, color="0369A1")
    font_kpi_lbl = Font(name="Meiryo UI", size=9, bold=True, color="475569")
    font_kpi_val = Font(name="Meiryo UI", size=16, bold=True, color="0F2940")

    thin_side = Side(style="thin", color="CBD5E1")
    med_bottom = Side(style="medium", color="0F2940")
    border_grid = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_total = Border(top=med_bottom, bottom=med_bottom, left=thin_side, right=thin_side)

    # =========================================================================
    # SHEET 1: ダッシュボード_江坂20km戦略
    # =========================================================================
    ws1 = wb.active
    ws1.title = "ダッシュボード_江坂20km戦略"
    ws1.views.sheetView[0].showGridLines = False

    n_stores = len(stores)
    first_row = 5
    last_row = 4 + n_stores
    list_sheet_ref = "江坂20km_S・A厳選架電リスト"

    ws1.merge_cells("B2:M2")
    ws1["B2"] = "株式会社ファインアトラス｜江坂20km圏内「お魚カスタム定期便（月額1万円〜）」営業攻略ダッシュボード"
    ws1["B2"].fill = navy_dark
    ws1["B2"].font = font_title
    ws1["B2"].alignment = Alignment(vertical="center", indent=1)
    ws1.row_dimensions[2].height = 32

    ws1.merge_cells("B3:M3")
    ws1["B3"] = "対象5商材：煮穴子・穴子フィレ・甘鯛・のどぐろ・剣先イカ（店ごとに加工度・量調整可）｜SNS・口コミ・調理人不足シグナル精査済"
    ws1["B3"].fill = slate_sub
    ws1["B3"].font = font_sub
    ws1["B3"].alignment = Alignment(vertical="center", indent=1)
    ws1.row_dimensions[3].height = 22

    # Top 5 KPI Cards (Row 5-6)
    kpi_defs = [
        ("B", "C", "厳選ターゲット総数", f"=COUNTA('{list_sheet_ref}'!B{first_row}:B{last_row})", '0" 店舗"'),
        ("D", "E", "Sランク（最優先・即決層）", f'=COUNTIF(\'{list_sheet_ref}\'!C{first_row}:C{last_row},"S")', '0" 店舗"'),
        ("F", "G", "Aランク（高確度・育成層）", f'=COUNTIF(\'{list_sheet_ref}\'!C{first_row}:C{last_row},"A")', '0" 店舗"'),
        ("H", "J", "入口：月1万円定期便 導入総額", f"=SUM('{list_sheet_ref}'!R{first_row}:R{last_row})", "¥#,##0"),
        ("K", "M", "育成後：月間見込売上ポテンシャル", f"=SUM('{list_sheet_ref}'!U{first_row}:U{last_row})", "¥#,##0"),
    ]
    ws1.row_dimensions[5].height = 20
    ws1.row_dimensions[6].height = 30
    for c_start, c_end, label, formula, num_fmt in kpi_defs:
        ws1.merge_cells(f"{c_start}5:{c_end}5")
        ws1.merge_cells(f"{c_start}6:{c_end}6")
        ws1[f"{c_start}5"] = label
        ws1[f"{c_start}5"].font = font_kpi_lbl
        ws1[f"{c_start}5"].fill = kpi_card_fill
        ws1[f"{c_start}5"].alignment = Alignment(horizontal="center", vertical="center")

        ws1[f"{c_start}6"] = formula
        ws1[f"{c_start}6"].font = font_kpi_val
        ws1[f"{c_start}6"].fill = kpi_card_fill
        ws1[f"{c_start}6"].number_format = num_fmt
        ws1[f"{c_start}6"].alignment = Alignment(horizontal="center", vertical="center")

    # Section Headers Row 8
    ws1["B8"] = "■ エリア別 ターゲット件数・月間見込売上集計（江坂20km圏内）"
    ws1["B8"].font = font_sec
    ws1["H8"] = "■ 勝ち筋3大ターゲット層別 件数・売上ポテンシャル集計"
    ws1["H8"].font = font_sec
    ws1.row_dimensions[8].height = 22

    # Table Headers Row 9
    left_headers = ["エリア区分", "対象店舗数", "うちSランク", "入口定期便計(円)", "育成後月商(円)"]
    for idx, h in enumerate(left_headers, start=2):
        cell = ws1.cell(9, idx, h)
        cell.fill = navy_mid
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_grid

    right_headers = ["勝ち筋セグメント区分", "対象店舗数", "うちSランク", "育成後月商(円)", "想定粗利(35%)", "売上構成比"]
    for idx, h in enumerate(right_headers, start=8):
        cell = ws1.cell(9, idx, h)
        cell.fill = navy_mid
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_grid
    ws1.row_dimensions[9].height = 24

    areas = [
        "北摂ホーム（江坂・吹田・豊中・箕面・高槻）",
        "福島・西天満・北新地・天満",
        "靱公園・本町・心斎橋・堀江",
        "阪神間・淀川（芦屋・夙川・西宮・伊丹・新大阪）",
    ]
    for i, area_name in enumerate(areas):
        r = 10 + i
        ws1.row_dimensions[r].height = 22
        ws1.cell(r, 2, area_name).font = font_body
        ws1.cell(r, 3, f"=COUNTIF('{list_sheet_ref}'!$E${first_row}:$E${last_row}, B{r})").number_format = "0"
        ws1.cell(r, 4, f'=COUNTIFS(\'{list_sheet_ref}\'!$E${first_row}:$E${last_row}, B{r}, \'{list_sheet_ref}\'!$C${first_row}:$C${last_row}, "S")').number_format = "0"
        ws1.cell(r, 5, f"=SUMIF('{list_sheet_ref}'!$E${first_row}:$E${last_row}, B{r}, '{list_sheet_ref}'!$R${first_row}:$R${last_row})").number_format = "¥#,##0"
        ws1.cell(r, 6, f"=SUMIF('{list_sheet_ref}'!$E${first_row}:$E${last_row}, B{r}, '{list_sheet_ref}'!$U${first_row}:$U${last_row})").number_format = "¥#,##0"
        for c in range(2, 7):
            ws1.cell(r, c).border = border_grid
            if c >= 3:
                ws1.cell(r, c).font = font_body

    segments = [
        "①洋食ポワソン（少人数ビストロ・伊・仏）",
        "②少人数ネオ割烹・創作和食・蕎麦割烹",
        "③住宅街・阪神間の実力派鮨＆日本料理",
    ]
    for i, seg_name in enumerate(segments):
        r = 10 + i
        ws1.cell(r, 8, seg_name).font = font_body
        ws1.cell(r, 9, f"=COUNTIF('{list_sheet_ref}'!$D${first_row}:$D${last_row}, H{r})").number_format = "0"
        ws1.cell(r, 10, f'=COUNTIFS(\'{list_sheet_ref}\'!$D${first_row}:$D${last_row}, H{r}, \'{list_sheet_ref}\'!$C${first_row}:$C${last_row}, "S")').number_format = "0"
        ws1.cell(r, 11, f"=SUMIF('{list_sheet_ref}'!$D${first_row}:$D${last_row}, H{r}, '{list_sheet_ref}'!$U${first_row}:$U${last_row})").number_format = "¥#,##0"
        ws1.cell(r, 12, f"=SUMIF('{list_sheet_ref}'!$D${first_row}:$D${last_row}, H{r}, '{list_sheet_ref}'!$V${first_row}:$V${last_row})").number_format = "¥#,##0"
        ws1.cell(r, 13, f"=IF($K$14>0, K{r}/$K$14, 0)").number_format = "0.0%"
        for c in range(8, 14):
            ws1.cell(r, c).border = border_grid
            if c >= 9:
                ws1.cell(r, c).font = font_body

    # Blank filler row 13 on right table so Totals align on row 14
    for c in range(8, 14):
        ws1.cell(13, c, "" if c == 8 else 0).border = border_grid
    ws1.cell(13, 8, "（予備枠）").font = Font(name="Meiryo UI", size=8.5, color="94A3B8")
    ws1.cell(13, 13, "=IF($K$14>0, K13/$K$14, 0)").number_format = "0.0%"

    # Totals Row 14
    ws1.row_dimensions[14].height = 24
    ws1.cell(14, 2, "合計").font = font_bold
    ws1.cell(14, 3, "=SUM(C10:C13)").number_format = "0"
    ws1.cell(14, 4, "=SUM(D10:D13)").number_format = "0"
    ws1.cell(14, 5, "=SUM(E10:E13)").number_format = "¥#,##0"
    ws1.cell(14, 6, "=SUM(F10:F13)").number_format = "¥#,##0"
    for c in range(2, 7):
        ws1.cell(14, c).fill = slate_sub
        ws1.cell(14, c).font = font_bold
        ws1.cell(14, c).border = border_total

    ws1.cell(14, 8, "合計").font = font_bold
    ws1.cell(14, 9, "=SUM(I10:I12)").number_format = "0"
    ws1.cell(14, 10, "=SUM(J10:J12)").number_format = "0"
    ws1.cell(14, 11, "=SUM(K10:K12)").number_format = "¥#,##0"
    ws1.cell(14, 12, "=SUM(L10:L12)").number_format = "¥#,##0"
    ws1.cell(14, 13, "=SUM(M10:M12)").number_format = "0.0%"
    for c in range(8, 14):
        ws1.cell(14, c).fill = slate_sub
        ws1.cell(14, c).font = font_bold
        ws1.cell(14, c).border = border_total

    # Bar Charts in Rows 16-28
    chart1 = BarChart()
    chart1.type = "col"
    chart1.title = "エリア別 育成後月間見込売上（円）"
    chart1.y_axis.title = "見込売上(円)"
    data1 = Reference(ws1, min_col=6, min_row=9, max_row=13)
    cats1 = Reference(ws1, min_col=2, min_row=10, max_row=13)
    chart1.add_data(data1, titles_from_data=True)
    chart1.set_categories(cats1)
    chart1.legend = None
    chart1.width = 14.5
    chart1.height = 7.2
    ws1.add_chart(chart1, "B16")

    chart2 = BarChart()
    chart2.type = "col"
    chart2.title = "勝ち筋3大ターゲット層別 育成後月間見込売上（円）"
    chart2.y_axis.title = "見込売上(円)"
    data2 = Reference(ws1, min_col=11, min_row=9, max_row=12)
    cats2 = Reference(ws1, min_col=8, min_row=10, max_row=12)
    chart2.add_data(data2, titles_from_data=True)
    chart2.set_categories(cats2)
    chart2.legend = None
    chart2.width = 14.5
    chart2.height = 7.2
    ws1.add_chart(chart2, "H16")

    # Strategy Insights Block (Row 31-36)
    ws1["B31"] = "■ 経営・営業戦略コンパス：江坂20km圏内で「月額1万円お魚カスタム定期便」が最も刺さる3大ターゲット層"
    ws1["B31"].font = font_sec
    ws1.row_dimensions[31].height = 24

    strategy_notes = [
        ("① 第1本命（即決率No.1）\n洋食ポワソン層", "オーナーシェフ1〜2名のビストロ・イタリアン・フレンチ（単価7,000〜15,000円）。狭い洋食厨房での『鱗引き・内臓処理・三枚おろし』は衛生面も時間面も最大の負担。週末コース用に『鱗付き甘鯛フィレ』『のどぐろフィレ』『穴子フィレ』『剣先イカ』が月1万円〜届くカスタム定期便はドンピシャで即決しやすい。"),
        ("② 第2本命（継続率No.1）\n少人数ネオ割烹・蕎麦割烹", "二番手（追い回し）不足で大将1人が深夜まで穴子炊きや魚おろしをしている個人和食（単価6,500〜16,000円）。特に中央市場が遠い『北摂エリア』や、毎朝の蕎麦打ちで魚仕込み時間が足りない『蕎麦割烹』が狙い目。『三枚おろし・生フィレ＋無添加煮穴子』の加工度カスタムなら大将のプライドを守りつつ残業を消せる。"),
        ("③ 第3本命（単価拡大枠）\n北摂・阪神間の個人鮨", "豊中・箕面・伊丹・西宮・夙川・芦屋などの住宅街名店（単価8,000〜18,000円）。客層が良く高単価だが、大阪本場・木津市場への毎朝往復が重労働。まずは『時化の日・週末のバックアップ用として月1万円定期便』で口座を開き、対馬水産の品質を体感後に月3〜8万円のメイン口座へ拡大（Land & Expand）する。"),
        ("④ 追わない層（除外基準）", "【除外①】見習い職人が5人以上いる単価3万円超の超高級店（丸魚仕込みが修業のため時短価値が響かない） ／ 【除外②】単価4,000円以下の大衆海鮮居酒屋（原価率が合わない） ／ 【除外③】本社一括購買の大手チェーン店。"),
    ]
    for idx, (head_txt, body_txt) in enumerate(strategy_notes, start=32):
        ws1.row_dimensions[idx].height = 38
        ws1.merge_cells(f"B{idx}:C{idx}")
        ws1.merge_cells(f"D{idx}:M{idx}")
        ws1[f"B{idx}"] = head_txt
        ws1[f"B{idx}"].font = font_bold
        ws1[f"B{idx}"].fill = slate_sub
        ws1[f"B{idx}"].alignment = Alignment(vertical="center", wrap_text=True)
        ws1[f"D{idx}"] = body_txt
        ws1[f"D{idx}"].font = font_body
        ws1[f"D{idx}"].alignment = Alignment(vertical="center", wrap_text=True)
        for col_i in range(2, 14):
            ws1.cell(idx, col_i).border = border_grid

    s1_widths = {
        "A": 3, "B": 34, "C": 13, "D": 13, "E": 17, "F": 18,
        "G": 3, "H": 34, "I": 13, "J": 13, "K": 18, "L": 17, "M": 12
    }
    for col_l, w in s1_widths.items():
        ws1.column_dimensions[col_l].width = w

    # =========================================================================
    # SHEET 2: 江坂20km_S・A厳選架電リスト
    # =========================================================================
    ws2 = wb.create_sheet(list_sheet_ref)
    ws2.freeze_panes = "D5"

    ws2.merge_cells("A1:W1")
    ws2["A1"] = "江坂20km圏内 お魚カスタム定期便（煮穴子・穴子フィレ・甘鯛・のどぐろ・剣先イカ）S・A厳選ターゲットリスト【株式会社ファインアトラス】"
    ws2["A1"].fill = navy_dark
    ws2["A1"].font = font_title
    ws2["A1"].alignment = Alignment(vertical="center", indent=1)
    ws2.row_dimensions[1].height = 30

    ws2.merge_cells("A2:W2")
    ws2["A2"] = "※低確度店（激安居酒屋・大手チェーン・弟子多数の超高級店）は完全除外済。Instagram・Googleマップ・食べログ口コミから『魚へのこだわり×少人数仕込み負荷』を裏取りした即戦力リスト。"
    ws2["A2"].fill = slate_sub
    ws2["A2"].font = font_sub
    ws2["A2"].alignment = Alignment(vertical="center", indent=1)
    ws2.row_dimensions[2].height = 20

    headers_s2 = [
        "No.",
        "店舗名・施設名",
        "確度",
        "勝ち筋セグメント区分",
        "エリア区分",
        "江坂からの距離・最寄駅",
        "所在地（住所）",
        "業態・ディナー単価・席数体制",
        "最優先フック商材",
        "5商材適性（煮穴子/フィレ/甘鯛/のどぐろ/剣先）",
        "月1万円カスタム定期便 推奨レシピ（加工度調整案）",
        "精査ソース（SNS発信・Googleマップ・食べログ口コミの事実）",
        "なぜ売れると判断したか（調理人不足・ワンオペ・仕込み課題推論）",
        "推奨架電時間",
        "第一声キラーコピー（無料サンプル／お試しセット打診）",
        "第二声クロージング（月額1万円カスタム定期便への接続トーク）",
        "架電ステータス",
        "入口定期便(円/月)",
        "育成後月間量(kg)",
        "想定単価(円/kg)",
        "育成後見込月商(円)",
        "想定月間粗利(35%)",
        "富田君 営業進捗・加工度カスタムメモ",
    ]
    ws2.row_dimensions[4].height = 28
    for c_idx, h_text in enumerate(headers_s2, start=1):
        cell = ws2.cell(4, c_idx, h_text)
        cell.fill = navy_dark
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    for idx, st in enumerate(stores):
        r = first_row + idx
        ws2.row_dimensions[r].height = 76
        is_even = idx % 2 == 1
        row_bg = zebra_fill if is_even else None

        row_values = [
            st["id"],
            sanitize_cell_text(st["name"]),
            st["rank"],
            sanitize_cell_text(st["segmentExcel"]),
            sanitize_cell_text(st["areaGroup"]),
            sanitize_cell_text(f"{st['distanceKm']:.1f}km（{st['station']}）"),
            sanitize_cell_text(st["address"]),
            sanitize_cell_text(f"{st['genre']}\n{st['priceRange']}"),
            sanitize_cell_text(st["hookProduct"]),
            sanitize_cell_text(st["fitSummary"]),
            sanitize_cell_text(st["customPlan10k"]),
            sanitize_cell_text(st["snsEvidence"]),
            sanitize_cell_text(st["whySell"]),
            sanitize_cell_text(st["callWindow"]),
            sanitize_cell_text(st["pitchSample"]),
            sanitize_cell_text(st["pitchSub10k"]),
            "未架電",
            10000,
            st["estKg"],
            st["unitPrice"],
            f"=S{r}*T{r}",
            f"=U{r}*0.35",
            "",
        ]
        for c_idx, val in enumerate(row_values, start=1):
            cell = ws2.cell(r, c_idx, val)
            cell.border = border_grid
            cell.font = font_body
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if row_bg:
                cell.fill = row_bg

        # Specific cell styling
        ws2.cell(r, 1).alignment = Alignment(horizontal="center", vertical="center")
        ws2.cell(r, 2).font = font_bold
        ws2.cell(r, 3).alignment = Alignment(horizontal="center", vertical="center")
        if st["rank"] == "S":
            ws2.cell(r, 3).fill = rank_s_fill
            ws2.cell(r, 3).font = font_rank_s
        else:
            ws2.cell(r, 3).fill = rank_a_fill
            ws2.cell(r, 3).font = font_rank_a

        ws2.cell(r, 11).fill = recipe_fill
        ws2.cell(r, 14).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws2.cell(r, 17).alignment = Alignment(horizontal="center", vertical="center")

        ws2.cell(r, 18).number_format = "¥#,##0"
        ws2.cell(r, 18).alignment = Alignment(horizontal="right", vertical="center")
        ws2.cell(r, 19).number_format = "#,##0"
        ws2.cell(r, 19).alignment = Alignment(horizontal="right", vertical="center")
        ws2.cell(r, 20).number_format = "¥#,##0"
        ws2.cell(r, 20).alignment = Alignment(horizontal="right", vertical="center")
        ws2.cell(r, 21).number_format = "¥#,##0"
        ws2.cell(r, 21).alignment = Alignment(horizontal="right", vertical="center")
        ws2.cell(r, 21).font = font_bold
        ws2.cell(r, 22).number_format = "¥#,##0"
        ws2.cell(r, 22).alignment = Alignment(horizontal="right", vertical="center")

    # Summary Total Row
    tot_r = last_row + 1
    ws2.row_dimensions[tot_r].height = 26
    ws2.merge_cells(f"A{tot_r}:Q{tot_r}")
    ws2.cell(tot_r, 1, f"江坂20km圏内 厳選{n_stores}店舗 合計 ／ 平均単価").alignment = Alignment(horizontal="right", vertical="center")
    ws2.cell(tot_r, 18, f"=SUM(R{first_row}:R{last_row})").number_format = "¥#,##0"
    ws2.cell(tot_r, 19, f"=SUM(S{first_row}:S{last_row})").number_format = "#,##0"
    ws2.cell(tot_r, 20, f"=AVERAGE(T{first_row}:T{last_row})").number_format = "¥#,##0"
    ws2.cell(tot_r, 21, f"=SUM(U{first_row}:U{last_row})").number_format = "¥#,##0"
    ws2.cell(tot_r, 22, f"=SUM(V{first_row}:V{last_row})").number_format = "¥#,##0"
    for c_idx in range(1, 24):
        c = ws2.cell(tot_r, c_idx)
        c.fill = slate_sub
        c.font = font_bold
        c.border = border_total

    # Dropdown Validation on Status Column Q (col 17)
    dv = DataValidation(type="list", formula1='"未架電,不在・再架電,サンプル送付OK,試食評価中,定期便成約,見送り"', allow_blank=True)
    ws2.add_data_validation(dv)
    dv.add(f"Q{first_row}:Q{last_row}")

    s2_widths = {
        1: 5, 2: 25, 3: 6.5, 4: 26, 5: 26, 6: 18, 7: 28, 8: 22,
        9: 18, 10: 24, 11: 32, 12: 40, 13: 40, 14: 14, 15: 44, 16: 42,
        17: 15, 18: 15, 19: 14, 20: 14, 21: 16, 22: 16, 23: 26
    }
    for col_i, w in s2_widths.items():
        ws2.column_dimensions[get_column_letter(col_i)].width = w

    # =========================================================================
    # SHEET 3: 関西版_商材別_切り返しトーク設計書
    # =========================================================================
    ws3 = wb.create_sheet("関西版_商材別_切り返しトーク設計書")
    ws3.merge_cells("A1:F1")
    ws3["A1"] = "江坂20km圏内（大阪・北摂・阪神間）専用｜5商材＆月額1万円カスタム定期便 反論処理＆クロージング設計書"
    ws3["A1"].fill = navy_dark
    ws3["A1"].font = font_title
    ws3["A1"].alignment = Alignment(vertical="center", indent=1)
    ws3.row_dimensions[1].height = 30

    headers_s3 = [
        "商材・テーマ区分",
        "メインターゲット業態",
        "関西の料理長・店主から出る典型的な断り文句",
        "裏にある本音・現状のペイン（調理人不足・原価）",
        "一撃でサンプル送付＆月1万円定期便に変える切り返しトーク",
        "推奨お試しサンプル提案セット",
    ]
    ws3.row_dimensions[3].height = 26
    for c_idx, h_txt in enumerate(headers_s3, start=1):
        cell = ws3.cell(3, c_idx, h_txt)
        cell.fill = navy_mid
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    for idx, pb in enumerate(playbook):
        r = 4 + idx
        ws3.row_dimensions[r].height = 74
        vals = [
            sanitize_cell_text(pb["category"]),
            sanitize_cell_text(pb["targetGenre"]),
            sanitize_cell_text(pb["objection"]),
            sanitize_cell_text(pb["realPain"]),
            sanitize_cell_text(pb["counterTalk"]),
            sanitize_cell_text(pb["sampleSet"]),
        ]
        for c_idx, val in enumerate(vals, start=1):
            cell = ws3.cell(r, c_idx, val)
            cell.border = border_grid
            cell.font = font_bold if c_idx == 1 else font_body
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if idx % 2 == 1:
                cell.fill = zebra_fill

    s3_widths = {"A": 20, "B": 22, "C": 32, "D": 36, "E": 52, "F": 26}
    for col_l, w in s3_widths.items():
        ws3.column_dimensions[col_l].width = w

    wb.save(OUT_XLSX)
    shutil.copyfile(OUT_XLSX, WORKSPACE_XLSX)
    print(f"Saved Excel workbook: {OUT_XLSX} ({n_stores} stores)")


def build_data_js(master):
    payload = (
        "// Auto-generated from scripts/stores_master.json — DO NOT EDIT MANUALLY\n"
        "window.FINE_ATLAS_FISH_CATALOG = " + json.dumps(master["fishCatalog"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_STORES = " + json.dumps(master["stores"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_PLAYBOOK = " + json.dumps(master["playbook"], ensure_ascii=False, indent=2) + ";\n"
    )
    with open(OUT_DATA_JS, "w", encoding="utf-8") as f:
        f.write(payload)
    print(f"Saved data.js: {OUT_DATA_JS}")


def main():
    with open(MASTER_JSON, "r", encoding="utf-8") as f:
        master = json.load(f)

    for i, st in enumerate(master["stores"], start=1):
        st["id"] = i
        dist = haversine_km(ESAKA_LAT, ESAKA_LNG, st["lat"], st["lng"])
        st["distanceKm"] = round(dist, 1)
        if dist > 20.0:
            raise ValueError(f"Store {st['name']} is {dist:.2f}km from Esaka (> 20km limit)!")
        st["monthlySales"] = int(st["estKg"] * st["unitPrice"])

    build_data_js(master)
    build_excel(master)


if __name__ == "__main__":
    main()
