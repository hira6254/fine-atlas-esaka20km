#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINE ATLAS — 江坂20km圏内 お魚カスタム定期便 営業図鑑 & AI仕入・配送モデル試算 生成スクリプト
Reads `stores_master.json` and generates inside `BASE_DIR` ONLY:
1. `data.js` for the Web Application (60 stores + procurement AI research + delivery models)
2. `2_江坂20km圏内_営業リスト_ファインアトラス定期便.xlsx` (5-sheet executive & field workbook)
"""

import json
import math
import os
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


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def sanitize_cell_text(val):
    if isinstance(val, str) and val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + val
    return val


def build_excel(master):
    stores = master["stores"]
    playbook = master["playbook"]
    procurement = master["procurementResearch"]
    delivery = master["deliveryModels"]

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
    kelp_fill = PatternFill("solid", fgColor="ECFDF5")

    font_title = Font(name="Meiryo UI", size=14, bold=True, color="FFFFFF")
    font_sub = Font(name="Meiryo UI", size=9.5, bold=False, color="1E3F5E")
    font_th = Font(name="Meiryo UI", size=9.5, bold=True, color="FFFFFF")
    font_sec = Font(name="Meiryo UI", size=10.5, bold=True, color="0F2940")
    font_body = Font(name="Meiryo UI", size=9.5, color="1F2328")
    font_bold = Font(name="Meiryo UI", size=9.5, bold=True, color="0F2940")
    font_rank_s = Font(name="Meiryo UI", size=10, bold=True, color="B91C1C")
    font_rank_a = Font(name="Meiryo UI", size=10, bold=True, color="0369A1")
    font_kelp = Font(name="Meiryo UI", size=9.5, bold=True, color="065F46")
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
    ws1["B2"] = f"株式会社ファインアトラス｜江坂20km圏内「お魚カスタム定期便（月額1万円〜）」営業攻略ダッシュボード（厳選{n_stores}店舗版）"
    ws1["B2"].fill = navy_dark
    ws1["B2"].font = font_title
    ws1["B2"].alignment = Alignment(vertical="center", indent=1)
    ws1.row_dimensions[2].height = 32

    ws1.merge_cells("B3:M3")
    ws1["B3"] = "主力5商材（煮穴子・穴子フィレ・甘鯛・のどぐろ・剣先イカ）＋拡張5商材｜全国冷凍魚AI相場調査＆江坂20km配送損益モデル収録"
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
    ws1["B8"] = "■ エリア別 ターゲット件数・月間見込売上集計（江坂20km圏内・全60店舗）"
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
        ("③ 第3本命（単価拡大枠）\n北摂・阪神間の個人鮨", "豊中・箕面・伊丹・西宮・夙川・芦屋などの住宅街名店（単価8,000〜18,000円）。客層が良く高単価だが、大阪本場・木津市場への毎朝往復が重労働。まずは『時化の日・週末のバックアップ用として月1万円定期便（隔週）』で口座を開き、対馬水産の品質体感後に拡張5品目も加えて月3〜8万円の本口座へ拡大（Land & Expand）する。"),
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
    ws2["A1"] = f"江坂20km圏内 お魚カスタム定期便（煮穴子・穴子フィレ・甘鯛・のどぐろ・剣先イカ）S・A厳選ターゲット全{n_stores}店舗リスト【株式会社ファインアトラス】"
    ws2["A1"].fill = navy_dark
    ws2["A1"].font = font_title
    ws2["A1"].alignment = Alignment(vertical="center", indent=1)
    ws2.row_dimensions[1].height = 30

    ws2.merge_cells("A2:W2")
    ws2["A2"] = "※低確度店（激安居酒屋・大手チェーン・弟子多数の超高級店）は完全除外済。実在・営業確認・電話番号＆SNS/口コミ精査済みの即戦力60店舗リスト。"
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
        "所在地（住所・TEL）",
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
        1: 5, 2: 25, 3: 6.5, 4: 26, 5: 26, 6: 18, 7: 30, 8: 22,
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

    # =========================================================================
    # SHEET 4: 全国冷凍魚10品目_仕入相場AI調査
    # =========================================================================
    ws4 = wb.create_sheet("全国冷凍魚10品目_仕入相場AI調査")
    ws4.freeze_panes = "D5"

    ws4.merge_cells("A1:O1")
    ws4["A1"] = "株式会社ファインアトラス｜全国業務用冷凍魚10品目 仕入れ価格相場AI調査（2025〜2026年実勢）＆ 飲食店FL原価試算シート"
    ws4["A1"].fill = navy_dark
    ws4["A1"].font = font_title
    ws4["A1"].alignment = Alignment(vertical="center", indent=1)
    ws4.row_dimensions[1].height = 30

    ws4.merge_cells("A2:O2")
    ws4["A2"] = "出典：東京都中央卸売市場（豊洲）・大阪市中央卸売市場 水産市況統計、業務用B2B卸EC（Mマート・魚ポチ/フーヅフリッジ等）公開相場レンジ"
    ws4["A2"].fill = slate_sub
    ws4["A2"].font = font_sub
    ws4["A2"].alignment = Alignment(vertical="center", indent=1)
    ws4.row_dimensions[2].height = 20

    headers_s4 = [
        "No.",
        "商材区分",
        "品目名（規格・状態）",
        "産地・市場卸実勢ベンチマーク（円/kg）",
        "市場卸下限\n(円/kg)",
        "FA標準仕入原価\n目安(円/kg)",
        "市場卸上限\n(円/kg)",
        "FA想定卸売単価\n(円/kg)",
        "FA想定粗利率",
        "納品時\n可食歩留",
        "1皿正味量\n(g/人前)",
        "飲食店1人前\n実質原価(円)",
        "飲食店想定\n売価(円)",
        "飲食店原価率\n(目標26-30%)",
        "急速凍結優位性（ドリップ差）＆ 営業提案・アップセル切り口",
    ]
    ws4.row_dimensions[4].height = 30
    for c_idx, h_txt in enumerate(headers_s4, start=1):
        cell = ws4.cell(4, c_idx, h_txt)
        cell.fill = navy_dark
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    proc_items = procurement["items"]
    p_first = 5
    p_last = p_first + len(proc_items) - 1

    for idx, it in enumerate(proc_items):
        r = p_first + idx
        ws4.row_dimensions[r].height = 58
        is_core = it["tier"] == "主力5品目"
        edge_note = sanitize_cell_text(f"{it['freezingEdge']}\n【提案】{it['upsellPitch']}（{it['rawFishYieldNote']}）")
        vals = [
            it["no"],
            sanitize_cell_text(it["tier"]),
            sanitize_cell_text(it["name"]),
            sanitize_cell_text(it["originSpec"]),
            it["wholesaleLow"],
            it["wholesaleMid"],
            it["wholesaleHigh"],
            it["atlasSellKg"],
            f"=(H{r}-F{r})/H{r}",
            it["yieldRate"],
            it["servingG"],
            f"=(H{r}*(K{r}/1000))/J{r}",
            it["menuPriceStd"],
            f"=L{r}/M{r}",
            edge_note,
        ]
        for c_idx, val in enumerate(vals, start=1):
            cell = ws4.cell(r, c_idx, val)
            cell.border = border_grid
            cell.font = font_body
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if idx % 2 == 1:
                cell.fill = zebra_fill

        ws4.cell(r, 1).alignment = Alignment(horizontal="center", vertical="center")
        ws4.cell(r, 2).alignment = Alignment(horizontal="center", vertical="center")
        ws4.cell(r, 2).fill = rank_s_fill if is_core else rank_a_fill
        ws4.cell(r, 2).font = font_rank_s if is_core else font_rank_a
        ws4.cell(r, 3).font = font_bold

        for yen_col in (5, 6, 7, 8, 12, 13):
            ws4.cell(r, yen_col).number_format = "¥#,##0"
            ws4.cell(r, yen_col).alignment = Alignment(horizontal="right", vertical="center")
        ws4.cell(r, 8).font = font_bold
        ws4.cell(r, 8).fill = recipe_fill
        ws4.cell(r, 9).number_format = "0.0%"
        ws4.cell(r, 9).alignment = Alignment(horizontal="right", vertical="center")
        ws4.cell(r, 9).font = font_kelp
        ws4.cell(r, 10).number_format = "0%"
        ws4.cell(r, 10).alignment = Alignment(horizontal="right", vertical="center")
        ws4.cell(r, 11).number_format = '#,##0"g"'
        ws4.cell(r, 11).alignment = Alignment(horizontal="right", vertical="center")
        ws4.cell(r, 12).font = font_bold
        ws4.cell(r, 14).number_format = "0.0%"
        ws4.cell(r, 14).alignment = Alignment(horizontal="right", vertical="center")
        ws4.cell(r, 14).fill = kelp_fill
        ws4.cell(r, 14).font = font_kelp
        ws4.cell(r, 15).alignment = Alignment(vertical="top", wrap_text=True)

    avg_r = p_last + 1
    ws4.row_dimensions[avg_r].height = 26
    ws4.merge_cells(f"A{avg_r}:D{avg_r}")
    ws4.cell(avg_r, 1, "全国冷凍魚10品目 平均値（主力5品目 ＋ 拡張アップセル5品目）").alignment = Alignment(horizontal="right", vertical="center")
    for col_i, fmt in [
        (5, "¥#,##0"), (6, "¥#,##0"), (7, "¥#,##0"), (8, "¥#,##0"),
        (9, "0.0%"), (10, "0.0%"), (11, '#,##0"g"'), (12, "¥#,##0"),
        (13, "¥#,##0"), (14, "0.0%")
    ]:
        col_let = get_column_letter(col_i)
        c = ws4.cell(avg_r, col_i, f"=AVERAGE({col_let}{p_first}:{col_let}{p_last})")
        c.number_format = fmt
        c.alignment = Alignment(horizontal="right", vertical="center")
    ws4.cell(avg_r, 15, "全10品目で飲食店原価率26.5〜30.2%の適正FLレンジと、FA粗利率30.6〜35.7%（平均34.1%）を同時達成").alignment = Alignment(vertical="center")
    for c_idx in range(1, 16):
        c = ws4.cell(avg_r, c_idx)
        c.fill = slate_sub
        c.font = font_bold
        c.border = border_total

    # Freezing Tech Comparison Block
    ft_start = avg_r + 2
    ws4.cell(ft_start, 1, "■ 凍結技術別 ドリップ流出率・お造り／焼物適性比較（なぜ『一般冷凍』ではなく『産地特殊急速凍結』が関西の料理長に刺さるか）").font = font_sec
    ws4.row_dimensions[ft_start].height = 24

    ft_head_r = ft_start + 1
    ws4.row_dimensions[ft_head_r].height = 24
    ft_cols = [
        ("A", "C", "凍結方式・パッケージング"),
        ("D", "E", "最大氷結晶帯(-1〜-5℃)通過"),
        ("F", "G", "解凍ドリップ流出率"),
        ("H", "L", "細胞組織・旨味保持メカニズム"),
        ("M", "O", "割烹・鮨・ビストロ適性判定"),
    ]
    for cs, ce, h_lbl in ft_cols:
        ws4.merge_cells(f"{cs}{ft_head_r}:{ce}{ft_head_r}")
        ws4[f"{cs}{ft_head_r}"] = sanitize_cell_text(h_lbl)
        ws4[f"{cs}{ft_head_r}"].fill = navy_mid
        ws4[f"{cs}{ft_head_r}"].font = font_th
        ws4[f"{cs}{ft_head_r}"].alignment = Alignment(horizontal="center", vertical="center")
    for c_i in range(1, 16):
        ws4.cell(ft_head_r, c_i).border = border_grid

    for idx, fc in enumerate(procurement["freezingComparison"]):
        rr = ft_head_r + 1 + idx
        ws4.row_dimensions[rr].height = 34
        merges = [
            ("A", "C", sanitize_cell_text(fc["method"]), font_bold, Alignment(vertical="center", wrap_text=True)),
            ("D", "E", sanitize_cell_text(fc["passTime"]), font_body, Alignment(horizontal="center", vertical="center")),
            ("F", "G", sanitize_cell_text(fc["dripRate"]), font_rank_s if idx == 0 else font_kelp, Alignment(horizontal="center", vertical="center")),
            ("H", "L", sanitize_cell_text(fc["cellState"]), font_body, Alignment(vertical="center", wrap_text=True)),
            ("M", "O", sanitize_cell_text(fc["culinaryFit"]), font_bold, Alignment(vertical="center", wrap_text=True)),
        ]
        for cs, ce, txt, fnt, aln in merges:
            ws4.merge_cells(f"{cs}{rr}:{ce}{rr}")
            ws4[f"{cs}{rr}"] = txt
            ws4[f"{cs}{rr}"].font = fnt
            ws4[f"{cs}{rr}"].alignment = aln
            if idx == 2:
                ws4[f"{cs}{rr}"].fill = kelp_fill
        for c_i in range(1, 16):
            ws4.cell(rr, c_i).border = border_grid
            if idx == 2:
                ws4.cell(rr, c_i).fill = kelp_fill

    src_r = ft_head_r + 5
    ws4.cell(src_r, 1, "■ 参照統計・業務用卸データソース").font = font_sec
    for idx, s_txt in enumerate(procurement["sources"], start=1):
        ws4.merge_cells(f"A{src_r + idx}:O{src_r + idx}")
        ws4.cell(src_r + idx, 1, sanitize_cell_text(f"・{s_txt}")).font = font_body

    s4_widths = {
        1: 5, 2: 13, 3: 28, 4: 38, 5: 13, 6: 14, 7: 13, 8: 15,
        9: 12, 10: 10, 11: 11, 12: 14, 13: 13, 14: 13, 15: 48
    }
    for col_i, w in s4_widths.items():
        ws4.column_dimensions[get_column_letter(col_i)].width = w

    # =========================================================================
    # SHEET 5: 江坂20km_配送モデル損益試算
    # =========================================================================
    ws5 = wb.create_sheet("江坂20km_配送モデル損益試算")
    ws5.views.sheetView[0].showGridLines = False

    ws5.merge_cells("B2:J2")
    ws5["B2"] = "株式会社ファインアトラス｜江坂拠点（半径20km）配送モデル3案 損益比較 ＆ 段階移行ロードマップ試算"
    ws5["B2"].fill = navy_dark
    ws5["B2"].font = font_title
    ws5["B2"].alignment = Alignment(vertical="center", indent=1)
    ws5.row_dimensions[2].height = 32

    ws5.merge_cells("B3:J3")
    ws5["B3"] = sanitize_cell_text(f"拠点前提：{delivery['depotName']}")
    ws5["B3"].fill = slate_sub
    ws5["B3"].font = font_sub
    ws5["B3"].alignment = Alignment(vertical="center", indent=1)
    ws5.row_dimensions[3].height = 22

    ws5.merge_cells("B4:J4")
    ws5["B4"] = sanitize_cell_text(delivery["executiveConclusion"])
    ws5["B4"].fill = recipe_fill
    ws5["B4"].font = font_bold
    ws5["B4"].alignment = Alignment(vertical="center", wrap_text=True)
    ws5["B4"].border = border_grid
    for ci in range(2, 11):
        ws5.cell(4, ci).border = border_grid
    ws5.row_dimensions[4].height = 46

    # Table 1: 3 Delivery Models Cost Structure (Rows 6..10)
    ws5["B6"] = "■ 1. 江坂20km圏 配送3モデル コスト構造・損益分岐比較"
    ws5["B6"].font = font_sec
    ws5.row_dimensions[6].height = 22

    headers_m = [
        "配送モデル名",
        "推奨フェーズ",
        "月額固定費\n(円/月)",
        "1配送変動費\n(円/回)",
        "コスト内訳・運用前提",
        "損益分岐店舗数・逆転条件",
        "強み（メリット）",
        "弱み・留意点（デメリット）",
        "総合判定",
    ]
    ws5.row_dimensions[7].height = 28
    for idx, h_txt in enumerate(headers_m, start=2):
        cell = ws5.cell(7, idx, h_txt)
        cell.fill = navy_mid
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    verdicts = ["○ 初期1〜38店", "○ 拡大39店〜", "◎ 最適解（推奨）"]
    for idx, md in enumerate(delivery["models"]):
        r = 8 + idx
        ws5.row_dimensions[r].height = 56
        fixed_val = md["phase2FixedCost"] if md["code"] == "MODEL_3" else md["monthlyFixedCost"]
        var_val = "=ROUND(140*0.85+1220*0.15,0)" if md["code"] == "MODEL_3" else md["variableCostPerDrop"]
        row_m = [
            sanitize_cell_text(md["name"]),
            sanitize_cell_text(md["badge"]),
            fixed_val,
            var_val,
            sanitize_cell_text(md["costBreakdown"]),
            sanitize_cell_text(md["breakevenStoresNote"]),
            sanitize_cell_text(md["pros"]),
            sanitize_cell_text(md["cons"]),
            verdicts[idx],
        ]
        for ci, val in enumerate(row_m, start=2):
            c = ws5.cell(r, ci, val)
            c.border = border_grid
            c.font = font_bold if ci in (2, 10) else font_body
            c.alignment = Alignment(vertical="center", wrap_text=True)
            if idx == 2:
                c.fill = kelp_fill
        ws5.cell(r, 4).number_format = "¥#,##0"
        ws5.cell(r, 4).alignment = Alignment(horizontal="right", vertical="center")
        ws5.cell(r, 5).number_format = "¥#,##0"
        ws5.cell(r, 5).alignment = Alignment(horizontal="right", vertical="center")
        ws5.cell(r, 10).alignment = Alignment(horizontal="center", vertical="center")
        if idx == 2:
            ws5.cell(r, 10).font = font_kelp

    # Table 2: Unit Economics per 1 Store (Rows 12..18)
    ws5["B12"] = "■ 2. 1店舗あたり単月損益シミュレーション（なぜ『月1万円入口プラン＝隔週2回配送』が必須なのか）"
    ws5["B12"].font = font_sec
    ws5.row_dimensions[12].height = 22

    headers_u = [
        "契約・配送パターン",
        "月間売上/店",
        "想定粗利率",
        "月間粗利額",
        "月間配送回数",
        "1配送コスト",
        "月間配送費計",
        "1店営業利益",
        "売上対営業利益率",
    ]
    ws5.row_dimensions[13].height = 26
    for idx, h_txt in enumerate(headers_u, start=2):
        cell = ws5.cell(13, idx, h_txt)
        cell.fill = navy_dark
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    unit_rows = [
        ("【NG設計】月1万円入口 × クール便・毎週配送（月4回）", 10000, 0.42, 4, "=E8"),
        ("【推奨入口】月1万円入口 × クール便・隔週まとめ配送（月2回）", 10000, 0.42, 2, "=E8"),
        ("【本口座・クール便】月2.8万円育成口座 × クール便（週1回・月4回）", 28000, 0.40, 4, "=E8"),
        ("【本口座・自社便39店時】月2.8万円 × 自社冷凍バン（39店按分・月4回）", 28000, 0.40, 4, "=ROUND(($D$9/(39*4))+$E$9,0)"),
        ("【完成形・自社便単独60店按分＋対面単価UP】月3.4万円 × 自社冷凍バン（60店按分・月4回）", 34000, 0.40, 4, "=ROUND(($D$9/(60*4))+$E$9,0)"),
    ]
    for idx, (lbl, sales, gm, drops, drop_cost_f) in enumerate(unit_rows):
        r = 14 + idx
        ws5.row_dimensions[r].height = 25
        ws5.cell(r, 2, sanitize_cell_text(lbl)).font = font_bold if idx in (0, 1, 4) else font_body
        ws5.cell(r, 3, sales).number_format = "¥#,##0"
        ws5.cell(r, 4, gm).number_format = "0.0%"
        ws5.cell(r, 5, f"=C{r}*D{r}").number_format = "¥#,##0"
        ws5.cell(r, 6, drops).number_format = '0"回"'
        ws5.cell(r, 7, drop_cost_f).number_format = "¥#,##0"
        ws5.cell(r, 8, f"=F{r}*G{r}").number_format = "¥#,##0"
        ws5.cell(r, 9, f"=E{r}-H{r}").number_format = "¥#,##0"
        ws5.cell(r, 10, f"=I{r}/C{r}").number_format = "0.0%"
        for ci in range(2, 11):
            c = ws5.cell(r, ci)
            c.border = border_grid
            if ci >= 3:
                c.alignment = Alignment(horizontal="right", vertical="center")
            else:
                c.alignment = Alignment(vertical="center")
            if idx == 0:
                c.fill = rank_s_fill
            elif idx in (1, 4):
                c.fill = kelp_fill
        ws5.cell(r, 9).font = font_rank_s if idx == 0 else font_bold

    # Table 3: Store Count Phase Scaling Simulation (Rows 20..25)
    ws5["B20"] = "■ 3. 稼働店舗数フェーズ別（15店 → 23店 → 39店 → 60店）月間事業営業利益 比較"
    ws5["B20"].font = font_sec
    ws5.row_dimensions[20].height = 22

    headers_p = [
        "拡大フェーズ",
        "稼働店舗数",
        "平均客単価(基本)",
        "月平均配送回数",
        "基本月商合計",
        "①クール便単独\n営業利益(円/月)",
        "②自社バン単独\n営業利益(円/月)",
        "③ハイブリッド(対面単価UP込)\n営業利益(円/月)",
        "フェーズ別アクション指針",
    ]
    ws5.row_dimensions[21].height = 28
    for idx, h_txt in enumerate(headers_p, start=2):
        cell = ws5.cell(21, idx, h_txt)
        cell.fill = navy_mid
        cell.font = font_th
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_grid

    phase_defs = [
        ("Phase 1a：初期立上げ（15店）", 15, 16000, 2.5, "クール便（月1万枠＝隔週）＋江坂近隣のみ富田君訪問で固定費0円黒字スタート"),
        ("Phase 1b：単体黒字ライン（23店）", 23, 28000, 4.0, "自社便単体も黒字化するが（+¥9,720）、38店まではクール便継続の方が高利益"),
        ("Phase 2：自社便切替点（39店）", 39, 28000, 4.0, "対面単価UP(+6千円)込みでクール便利益(+¥246,480)をハイブリッド(+¥248,288)が逆転！"),
        ("Phase 3：60店フル稼働（60店）", 60, 28000, 4.0, "55店で純運賃単体でも自社便優位＋対面単価3.4万円化で月間営業利益+50万円超"),
    ]
    for idx, (p_lbl, cnt, avg_s, drops_m, note_txt) in enumerate(phase_defs):
        r = 22 + idx
        ws5.row_dimensions[r].height = 34
        ws5.cell(r, 2, sanitize_cell_text(p_lbl)).font = font_bold
        ws5.cell(r, 3, cnt).number_format = '0"店"'
        ws5.cell(r, 4, avg_s).number_format = "¥#,##0"
        ws5.cell(r, 5, drops_m).number_format = '0.0"回"'
        ws5.cell(r, 6, f"=C{r}*D{r}").number_format = "¥#,##0"
        # Model 1 Cool only operating profit (40% gross margin minus Cool variable cost)
        ws5.cell(r, 7, f"=(F{r}*0.40)-(C{r}*E{r}*$E$8)").number_format = "¥#,##0"
        # Model 2 Own Van only operating profit (40% gross margin minus fixed 235k & 140/drop)
        ws5.cell(r, 8, f"=(F{r}*0.40)-($D$9+C{r}*E{r}*$E$9)").number_format = "¥#,##0"
        # Model 3 Hybrid operating profit: if <39 stores use Model 1; if >=39 stores, 85% cluster van (with +6,000 upsell lift per store) + 15% Cool
        ws5.cell(
            r, 9,
            f"=IF(C{r}<39, G{r}, ((C{r}*(D{r}+6000))*0.40)-($D$9+C{r}*E{r}*$E$10))"
        ).number_format = "¥#,##0"
        ws5.cell(r, 10, sanitize_cell_text(note_txt)).font = font_body

        for ci in range(2, 11):
            c = ws5.cell(r, ci)
            c.border = border_grid
            if 3 <= ci <= 9:
                c.alignment = Alignment(horizontal="right", vertical="center")
            else:
                c.alignment = Alignment(vertical="center", wrap_text=True)
            if idx % 2 == 1:
                c.fill = zebra_fill
        ws5.cell(r, 9).fill = kelp_fill
        ws5.cell(r, 9).font = font_kelp

    # Table 4: Weekday 4-Cluster Schedule (Rows 27..33)
    ws5["B27"] = "■ 4. 江坂デポ発 曜日別4クラスター巡回スケジュール（厳選60店舗 完全カバー計画）"
    ws5["B27"].font = font_sec
    ws5.row_dimensions[27].height = 22

    ws5.row_dimensions[28].height = 25
    cluster_headers = [
        ("B", "B", "巡回曜日"),
        ("C", "D", "クラスター便名称"),
        ("E", "F", "カバー対象エリア"),
        ("G", "I", "推奨走行ルート・所要時間目安"),
        ("J", "J", "対象店舗数"),
    ]
    for cs, ce, h_lbl in cluster_headers:
        ws5.merge_cells(f"{cs}28:{ce}28")
        ws5[f"{cs}28"] = h_lbl
        ws5[f"{cs}28"].fill = navy_dark
        ws5[f"{cs}28"].font = font_th
        ws5[f"{cs}28"].alignment = Alignment(horizontal="center", vertical="center")
    for ci in range(2, 11):
        ws5.cell(28, ci).border = border_grid

    for idx, cl in enumerate(delivery["weekdayClusters"]):
        r = 29 + idx
        ws5.row_dimensions[r].height = 26
        ws5.cell(r, 2, sanitize_cell_text(cl["day"])).font = font_bold
        ws5.cell(r, 2).alignment = Alignment(horizontal="center", vertical="center")
        ws5.merge_cells(f"C{r}:D{r}")
        ws5[f"C{r}"] = sanitize_cell_text(cl["clusterName"])
        ws5[f"C{r}"].font = font_bold
        ws5[f"C{r}"].alignment = Alignment(vertical="center")
        ws5.merge_cells(f"E{r}:F{r}")
        ws5[f"E{r}"] = sanitize_cell_text(cl["areas"])
        ws5[f"E{r}"].font = font_body
        ws5[f"E{r}"].alignment = Alignment(vertical="center", wrap_text=True)
        ws5.merge_cells(f"G{r}:I{r}")
        ws5[f"G{r}"] = sanitize_cell_text(cl["routeNote"])
        ws5[f"G{r}"].font = font_body
        ws5[f"G{r}"].alignment = Alignment(vertical="center", wrap_text=True)
        ws5.cell(r, 10, cl["targetStoresCount"]).number_format = '0" 店舗"'
        ws5.cell(r, 10).font = font_bold
        ws5.cell(r, 10).alignment = Alignment(horizontal="right", vertical="center")
        for ci in range(2, 11):
            ws5.cell(r, ci).border = border_grid
            if idx % 2 == 1:
                ws5.cell(r, ci).fill = zebra_fill

    ws5.row_dimensions[33].height = 25
    ws5.merge_cells("B33:I33")
    ws5["B33"] = "月曜日は江坂デポでの入荷検品・ピッキング＆富田君の新規サンプル訪問日に充当（火〜金で全60店舗を巡回）"
    ws5["B33"].alignment = Alignment(horizontal="right", vertical="center")
    ws5.cell(33, 10, "=SUM(J29:J32)").number_format = '0" 店舗"'
    ws5.cell(33, 10).alignment = Alignment(horizontal="right", vertical="center")
    for ci in range(2, 11):
        ws5.cell(33, ci).fill = slate_sub
        ws5.cell(33, ci).font = font_bold
        ws5.cell(33, ci).border = border_total

    s5_widths = {
        "A": 3, "B": 36, "C": 16, "D": 15, "E": 15,
        "F": 32, "G": 28, "H": 28, "I": 28, "J": 24
    }
    for col_l, w in s5_widths.items():
        ws5.column_dimensions[col_l].width = w

    wb.save(OUT_XLSX)
    print(f"Saved 5-sheet Excel workbook: {OUT_XLSX} ({n_stores} stores)")


def build_data_js(master):
    payload = (
        "// Auto-generated from scripts/stores_master.json — DO NOT EDIT MANUALLY\n"
        "window.FINE_ATLAS_FISH_CATALOG = " + json.dumps(master["fishCatalog"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_STORES = " + json.dumps(master["stores"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_PLAYBOOK = " + json.dumps(master["playbook"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_PROCUREMENT = " + json.dumps(master["procurementResearch"], ensure_ascii=False, indent=2) + ";\n\n"
        "window.FINE_ATLAS_DELIVERY_MODELS = " + json.dumps(master["deliveryModels"], ensure_ascii=False, indent=2) + ";\n"
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
