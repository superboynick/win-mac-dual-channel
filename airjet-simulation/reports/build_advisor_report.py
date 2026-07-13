#!/usr/bin/env python3
"""Build the advisor-facing AirJet project report from its Markdown source."""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#2F75B5")
CYAN = colors.HexColor("#D9EAF7")
LIGHT_BLUE = colors.HexColor("#EDF5FA")
LIGHT_GRAY = colors.HexColor("#F3F5F7")
MID_GRAY = colors.HexColor("#697785")
DARK = colors.HexColor("#1E2A33")
GREEN = colors.HexColor("#2E7D5B")
AMBER = colors.HexColor("#D89000")
RED = colors.HexColor("#B64040")


def register_fonts() -> None:
    pdfmetrics.registerFont(
        TTFont("CJK", "/System/Library/Fonts/STHeiti Light.ttc", subfontIndex=0)
    )
    pdfmetrics.registerFont(
        TTFont("CJK-Bold", "/System/Library/Fonts/STHeiti Medium.ttc", subfontIndex=0)
    )


def width_units(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in {"W", "F", "A"} else 1 for ch in text)


def inline_markup(text: str) -> str:
    value = html.escape(text.strip())
    value = re.sub(
        r"`([^`]+)`",
        r"<font name='CJK-Bold' color='#315F7D'>\1</font>",
        value,
    )
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(
        r"(https://[^\s<]+)",
        r"<link href='\1' color='#1F5E8C'><u>\1</u></link>",
        value,
    )
    return value


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=9.3,
            leading=15.0,
            textColor=DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=4.5,
            wordWrap="CJK",
        ),
        "Lead": ParagraphStyle(
            "Lead",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=10.4,
            leading=17.5,
            textColor=DARK,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
            wordWrap="CJK",
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=base["Heading1"],
            fontName="CJK-Bold",
            fontSize=16.5,
            leading=22,
            textColor=NAVY,
            spaceBefore=11,
            spaceAfter=8,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="CJK-Bold",
            fontSize=12.2,
            leading=17,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=5,
            keepWithNext=True,
            wordWrap="CJK",
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=9.1,
            leading=14.5,
            leftIndent=13,
            firstLineIndent=0,
            bulletIndent=2,
            textColor=DARK,
            spaceAfter=2.5,
            wordWrap="CJK",
        ),
        "Numbered": ParagraphStyle(
            "Numbered",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=9.1,
            leading=14.5,
            leftIndent=18,
            firstLineIndent=0,
            bulletIndent=1,
            textColor=DARK,
            spaceAfter=3,
            wordWrap="CJK",
        ),
        "Quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=9.1,
            leading=15,
            leftIndent=10,
            rightIndent=8,
            borderColor=BLUE,
            borderWidth=1.5,
            borderPadding=(5, 7, 5, 9),
            backColor=LIGHT_BLUE,
            textColor=colors.HexColor("#304958"),
            wordWrap="CJK",
            spaceAfter=8,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=8.3,
            leading=12.5,
            leftIndent=8,
            rightIndent=8,
            borderPadding=6,
            backColor=LIGHT_GRAY,
            textColor=colors.HexColor("#274555"),
            wordWrap="CJK",
            spaceAfter=6,
        ),
        "Table": ParagraphStyle(
            "Table",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=7.2,
            leading=10.5,
            textColor=DARK,
            wordWrap="CJK",
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="CJK-Bold",
            fontSize=7.5,
            leading=10.5,
            textColor=colors.white,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="CJK",
            fontSize=7.5,
            leading=11,
            textColor=MID_GRAY,
            wordWrap="CJK",
        ),
    }


class AdvisorDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, styles: dict[str, ParagraphStyle]):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=19 * mm,
            bottomMargin=18 * mm,
            title="基于公开证据的 AirJet Mini 整机多物理场数字复原",
            author="AirJet Mini reconstruction project",
            subject="项目描述与阶段汇报 - 导师审阅版",
        )
        self.styles = styles
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates(
            [
                PageTemplate(id="main", frames=frame, onPage=self.draw_page),
            ]
        )

    def draw_page(self, canvas, doc) -> None:
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#C7D2DA"))
            canvas.setLineWidth(0.4)
            canvas.line(18 * mm, A4[1] - 13 * mm, A4[0] - 18 * mm, A4[1] - 13 * mm)
            canvas.setFont("CJK", 7.2)
            canvas.setFillColor(MID_GRAY)
            canvas.drawString(18 * mm, A4[1] - 10.5 * mm, "AirJet Mini 整机数字复原 - 导师审阅版")
            canvas.drawRightString(A4[0] - 18 * mm, A4[1] - 10.5 * mm, "技术基线 0c1c0de")
        canvas.setStrokeColor(colors.HexColor("#C7D2DA"))
        canvas.line(18 * mm, 12 * mm, A4[0] - 18 * mm, 12 * mm)
        canvas.setFont("CJK", 7.2)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(18 * mm, 8.2 * mm, "2026-07-13 | 公开证据约束模型，不等同精确数字孪生")
        canvas.drawRightString(A4[0] - 18 * mm, 8.2 * mm, f"第 {doc.page} 页")
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"Heading1", "Heading2"}:
            return
        level = 0 if style_name == "Heading1" else 1
        text = flowable.getPlainText()
        key = f"heading-{level}-{self.seq.nextf('heading')}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def evidence_figure(width: float) -> Drawing:
    height = 48 * mm
    drawing = Drawing(width, height)
    labels = [
        ("1 型号数据表", NAVY),
        ("2 官方教程", BLUE),
        ("3 专利候选", colors.HexColor("#5088A8")),
        ("4 数值文献", colors.HexColor("#6B9A9B")),
        ("5 官方图像", colors.HexColor("#8AA77C")),
        ("6 工程推断", colors.HexColor("#A8A76A")),
    ]
    gap = 2 * mm
    box_h = 5.6 * mm
    for index, (label, color) in enumerate(labels):
        box_w = width - index * 14 * mm
        x = index * 7 * mm
        y = height - (index + 1) * (box_h + gap)
        drawing.add(Rect(x, y, box_w, box_h, rx=2, ry=2, fillColor=color, strokeColor=None))
        drawing.add(
            String(
                x + 3 * mm,
                y + 1.7 * mm,
                label,
                fontName="CJK-Bold",
                fontSize=8,
                fillColor=colors.white,
            )
        )
    drawing.add(
        String(
            width - 57 * mm,
            2 * mm,
            "证据越低，必须保留越大的不确定性",
            fontName="CJK",
            fontSize=7.5,
            fillColor=MID_GRAY,
        )
    )
    return drawing


def architecture_figure(width: float) -> Drawing:
    height = 47 * mm
    drawing = Drawing(width, height)
    box_w = 49 * mm
    box_h = 28 * mm
    gap = (width - 3 * box_w) / 2
    boxes = [
        ("模型 A", "单 cell 压电结构", "频率 / 位移 / 功耗", NAVY),
        ("模型 B", "完整产品气动", "全 cell / 流道 / 相位", BLUE),
        ("模型 C", "完整产品 CHT", "芯片 / TIM / 自热", GREEN),
    ]
    y = 12 * mm
    for i, (title, subtitle, output, color) in enumerate(boxes):
        x = i * (box_w + gap)
        drawing.add(Rect(x, y, box_w, box_h, rx=5, ry=5, fillColor=colors.white, strokeColor=color, strokeWidth=1.4))
        drawing.add(Rect(x, y + box_h - 7 * mm, box_w, 7 * mm, rx=5, ry=5, fillColor=color, strokeColor=color))
        drawing.add(String(x + box_w / 2, y + box_h - 5 * mm, title, fontName="CJK-Bold", fontSize=9.5, textAnchor="middle", fillColor=colors.white))
        drawing.add(String(x + box_w / 2, y + 12.5 * mm, subtitle, fontName="CJK-Bold", fontSize=8, textAnchor="middle", fillColor=DARK))
        drawing.add(String(x + box_w / 2, y + 6.5 * mm, output, fontName="CJK", fontSize=7, textAnchor="middle", fillColor=MID_GRAY))
        if i < 2:
            x1 = x + box_w + 2 * mm
            x2 = x + box_w + gap - 2 * mm
            y_arrow = y + box_h / 2
            drawing.add(Line(x1, y_arrow, x2, y_arrow, strokeColor=MID_GRAY, strokeWidth=1.2))
            drawing.add(Line(x2 - 3, y_arrow + 2, x2, y_arrow, strokeColor=MID_GRAY, strokeWidth=1.2))
            drawing.add(Line(x2 - 3, y_arrow - 2, x2, y_arrow, strokeColor=MID_GRAY, strokeWidth=1.2))
    drawing.add(String(width / 2, 3 * mm, "单 cell 用于识别接口；最终气动和热结果必须回到完整产品", fontName="CJK", fontSize=8, textAnchor="middle", fillColor=NAVY))
    return drawing


def stages_figure(width: float) -> Drawing:
    height = 29 * mm
    drawing = Drawing(width, height)
    gap = 2.2 * mm
    box_w = (width - 6 * gap) / 7
    for i in range(7):
        x = i * (box_w + gap)
        color = AMBER if i == 0 else colors.HexColor("#AAB4BB")
        drawing.add(Rect(x, 10 * mm, box_w, 11 * mm, rx=3, ry=3, fillColor=color, strokeColor=None))
        drawing.add(String(x + box_w / 2, 16.5 * mm, f"P{i}", fontName="CJK-Bold", fontSize=9, textAnchor="middle", fillColor=colors.white))
        status = "进行中" if i == 0 else "未开始"
        drawing.add(String(x + box_w / 2, 5 * mm, status, fontName="CJK", fontSize=6.7, textAnchor="middle", fillColor=color))
        if i < 6:
            x1 = x + box_w + 1
            x2 = x + box_w + gap - 1
            drawing.add(Line(x1, 15.5 * mm, x2, 15.5 * mm, strokeColor=colors.HexColor("#C3CBD0"), strokeWidth=1))
    return drawing


def compute_figure(width: float) -> Drawing:
    height = 52 * mm
    drawing = Drawing(width, height)
    labels = [
        ("P2 单 cell 结构", 32, NAVY),
        ("P3 单 cell CFD", 64, BLUE),
        ("P4a 整机降阶", 128, colors.HexColor("#5A8F85")),
        ("P4b 整机高保真", 256, RED),
        ("P5 整机 CHT", 128, GREEN),
    ]
    left = 37 * mm
    max_bar = width - left - 7 * mm
    for i, (label, memory, color) in enumerate(labels):
        y = height - (i + 1) * 9 * mm
        drawing.add(String(0, y + 1.5 * mm, label, fontName="CJK", fontSize=7.2, fillColor=DARK))
        bar_w = max_bar * memory / 256
        drawing.add(Rect(left, y, bar_w, 5 * mm, rx=2, ry=2, fillColor=color, strokeColor=None))
        drawing.add(String(left + bar_w + 2 * mm, y + 1.5 * mm, f"{memory} GB", fontName="CJK-Bold", fontSize=7, fillColor=color))
    current_x = left + max_bar * 31.43 / 256
    drawing.add(Line(current_x, 2 * mm, current_x, height - 4 * mm, strokeColor=AMBER, strokeWidth=1.4))
    drawing.add(String(current_x + 1.5 * mm, 2 * mm, "当前 31.43 GiB", fontName="CJK-Bold", fontSize=7, fillColor=AMBER))
    return drawing


def parse_table(lines: list[str], styles: dict[str, ParagraphStyle], available_width: float) -> Table:
    raw_rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    rows = [raw_rows[0]] + raw_rows[2:]
    columns = len(rows[0])
    maxima = []
    for index in range(columns):
        values = [row[index] if index < len(row) else "" for row in rows]
        maxima.append(max(8, min(34, max(width_units(value) for value in values))))
    minimum = 16 * mm if columns <= 4 else 12 * mm
    widths = [max(minimum, available_width * value / sum(maxima)) for value in maxima]
    scale = available_width / sum(widths)
    widths = [value * scale for value in widths]

    data = []
    for row_index, row in enumerate(rows):
        style = styles["TableHead"] if row_index == 0 else styles["Table"]
        padded = row + [""] * (columns - len(row))
        data.append([Paragraph(inline_markup(cell), style) for cell in padded[:columns]])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BFC9D0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row_index in range(1, len(data)):
        if row_index % 2 == 0:
            commands.append(("BACKGROUND", (0, row_index), (-1, row_index), LIGHT_GRAY))
    table.setStyle(TableStyle(commands))
    table.spaceBefore = 4
    table.spaceAfter = 9
    return table


def parse_markdown(text: str, styles: dict[str, ParagraphStyle], available_width: float) -> list:
    lines = text.splitlines()
    story: list = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            joined = " ".join(item.strip() for item in paragraph)
            style = styles["Lead"] if joined.startswith("本项目拟") else styles["Body"]
            story.append(Paragraph(inline_markup(joined), style))
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Paragraph("<br/>".join(html.escape(item) for item in code_lines), styles["Code"]))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        if stripped == "---":
            flush_paragraph()
            story.append(Spacer(1, 3 * mm))
            index += 1
            continue
        if stripped == "<!-- PAGEBREAK -->":
            flush_paragraph()
            story.append(PageBreak())
            index += 1
            continue
        if stripped == "<!-- FIGURE:EVIDENCE -->":
            flush_paragraph()
            story.extend([evidence_figure(available_width), Spacer(1, 2 * mm)])
            index += 1
            continue
        if stripped == "<!-- FIGURE:ARCHITECTURE -->":
            flush_paragraph()
            story.extend([architecture_figure(available_width), Spacer(1, 2 * mm)])
            index += 1
            continue
        if stripped == "<!-- FIGURE:STAGES -->":
            flush_paragraph()
            story.extend([stages_figure(available_width), Spacer(1, 2 * mm)])
            index += 1
            continue
        if stripped == "<!-- FIGURE:COMPUTE -->":
            flush_paragraph()
            story.extend([compute_figure(available_width), Spacer(1, 2 * mm)])
            index += 1
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[3:]), styles["Heading1"]))
            index += 1
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), styles["Heading2"]))
            index += 1
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            index += 1
            continue
        if stripped.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), styles["Quote"]))
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[index + 1]):
            flush_paragraph()
            table_lines = [line, lines[index + 1]]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(parse_table(table_lines, styles, available_width))
            continue
        bullet = re.match(r"^-\s+(.*)$", stripped)
        if bullet:
            flush_paragraph()
            story.append(Paragraph(inline_markup(bullet.group(1)), styles["Bullet"], bulletText="•"))
            index += 1
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            story.append(
                Paragraph(
                    inline_markup(numbered.group(2)),
                    styles["Numbered"],
                    bulletText=f"{numbered.group(1)}.",
                )
            )
            index += 1
            continue
        paragraph.append(line)
        index += 1

    flush_paragraph()
    return story


def build_cover(styles: dict[str, ParagraphStyle]) -> list:
    title_style = ParagraphStyle(
        "CoverTitle",
        fontName="CJK-Bold",
        fontSize=25,
        leading=34,
        textColor=NAVY,
        alignment=TA_CENTER,
        wordWrap="CJK",
    )
    subtitle_style = ParagraphStyle(
        "CoverSubTitle",
        fontName="CJK",
        fontSize=14,
        leading=21,
        textColor=BLUE,
        alignment=TA_CENTER,
        wordWrap="CJK",
    )
    english_style = ParagraphStyle(
        "CoverEnglish",
        fontName="CJK",
        fontSize=9.2,
        leading=14,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
    )
    meta_style = ParagraphStyle(
        "CoverMeta",
        fontName="CJK",
        fontSize=10,
        leading=19,
        textColor=DARK,
        alignment=TA_LEFT,
        leftIndent=36 * mm,
    )
    status_data = [
        [Paragraph("当前阶段", styles["TableHead"]), Paragraph("P0 产品证据冻结进行中", styles["Table"])],
        [Paragraph("已完成", styles["TableHead"]), Paragraph("规划、证据框架、审计与跨机交接", styles["Table"])],
        [Paragraph("未完成", styles["TableHead"]), Paragraph("P0-P6 物理 Gate、CAD、CFD、CHT", styles["Table"])],
    ]
    status_table = Table(status_data, colWidths=[30 * mm, 92 * mm], hAlign="CENTER")
    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), NAVY),
                ("BACKGROUND", (1, 0), (1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B8C8D4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C8D3DB")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return [
        Spacer(1, 21 * mm),
        Paragraph("基于公开证据的<br/>AirJet Mini 整机多物理场数字复原", title_style),
        Spacer(1, 7 * mm),
        Paragraph("项目描述与阶段汇报 - 导师审阅版", subtitle_style),
        Spacer(1, 4 * mm),
        Paragraph("Public-Evidence-Constrained Full-Product Multiphysics Reconstruction of Frore AirJet Mini", english_style),
        Spacer(1, 11 * mm),
        Table([["", ""]], colWidths=[30 * mm, 92 * mm], style=[("LINEABOVE", (0, 0), (-1, 0), 2, BLUE)]),
        Spacer(1, 8 * mm),
        Paragraph("汇报人：____________", meta_style),
        Paragraph("汇报日期：2026-07-13", meta_style),
        Paragraph("报告版本：v1.0", meta_style),
        Paragraph("技术基线：Git commit 0c1c0de", meta_style),
        Spacer(1, 10 * mm),
        status_table,
        Spacer(1, 12 * mm),
        Paragraph("本报告是项目立项与阶段汇报，不是论文初稿或仿真结果报告。", english_style),
        PageBreak(),
    ]


def build_report(source: Path, output: Path) -> None:
    register_fonts()
    styles = make_styles()
    markdown = source.read_text(encoding="utf-8")
    first_break = "<!-- PAGEBREAK -->"
    body = markdown.split(first_break, 1)[1] if first_break in markdown else markdown

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = AdvisorDocTemplate(str(output), styles)
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="CJK-Bold",
            fontSize=9.5,
            leading=15,
            textColor=NAVY,
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=2,
        ),
        ParagraphStyle(
            "TOC2",
            fontName="CJK",
            fontSize=8.4,
            leading=13,
            textColor=DARK,
            leftIndent=12,
            firstLineIndent=0,
        ),
    ]
    story = build_cover(styles)
    story.extend(
        [
            Paragraph("目录", styles["Heading1"]),
            Spacer(1, 2 * mm),
            toc,
            PageBreak(),
        ]
    )
    story.extend(parse_markdown(body, styles, doc.width))
    doc.multiBuild(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_report(args.source.resolve(), args.output.resolve())
    print(f"WROTE {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
