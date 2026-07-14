# Advisor report build

Files:

- `AIRJET_MINI_PROJECT_REPORT_FOR_ADVISOR_2026-07-13.md`: editable Chinese report source.
- `build_advisor_report.py`: ReportLab builder for the A4 advisor PDF.

The rendered PDF is deliberately kept outside Git at:

`output/pdf/AirJet_Mini_整机数字复原项目阶段报告_导师版_2026-07-14.pdf`

Build on the project Mac:

```sh
python3 -m venv /private/tmp/airjet-report-venv
/private/tmp/airjet-report-venv/bin/pip install reportlab pdfplumber pypdf
/private/tmp/airjet-report-venv/bin/python \
  airjet-simulation/reports/build_advisor_report.py \
  --source airjet-simulation/reports/AIRJET_MINI_PROJECT_REPORT_FOR_ADVISOR_2026-07-13.md \
  --output output/pdf/AirJet_Mini_整机数字复原项目阶段报告_导师版_2026-07-14.pdf
```

The builder embeds the macOS `STHeiti` fonts. If moved to another OS, update the font paths before building. After every content or layout change, render with Poppler and inspect every page:

```sh
pdftoppm -png -r 110 \
  output/pdf/AirJet_Mini_整机数字复原项目阶段报告_导师版_2026-07-14.pdf \
  tmp/pdfs/advisor-render/page
```

The PDF is a stage report. `P0 PASS` means that the evidence freeze and its uncertainty boundaries passed; it must not be interpreted as a P1-P6 CAD or physical-simulation result.
