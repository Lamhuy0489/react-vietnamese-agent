import os
import re
import subprocess

import markdown
import pypdf

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MD_PATH = os.path.join(DOCS_DIR, "BAO_CAO_TIEN_DO_DO_AN.md")
HTML_PATH = os.path.join(DOCS_DIR, "bao_cao_print.html")
PDF_PATH = os.path.join(DOCS_DIR, "BAO_CAO_TIEN_DO_DO_AN.pdf")
FIGURES_DIR = os.path.join(DOCS_DIR, "figures")

def read_svg(filename):
    svg_path = os.path.join(FIGURES_DIR, filename)
    if not os.path.exists(svg_path):
        return f"<p style='color:red;'>[Không tìm thấy hình: {filename}]</p>"
    with open(svg_path, encoding="utf-8") as f:
        content = f.read()
    # Ensure viewBox and responsive scaling
    content = re.sub(r'width="[^"]+"', 'width="100%"', content, count=1)
    content = re.sub(r'height="[^"]+"', 'height="auto"', content, count=1)
    return content

def generate_html():
    with open(MD_PATH, encoding="utf-8") as f:
        md_text = f.read()

    # Pre-process image tags to inline SVG
    svg_replacements = {
        'figures/react_flow_diagram.svg': read_svg('react_flow_diagram.svg'),
        'figures/pregate_logic_diagram.svg': read_svg('pregate_logic_diagram.svg'),
        'figures/security_vs_utility_curve.svg': read_svg('security_vs_utility_curve.svg'),
        'figures/gpu_coexistence_diagram.svg': read_svg('gpu_coexistence_diagram.svg'),
    }

    # Replace markdown image syntax or HTML img tags
    for src, svg_markup in svg_replacements.items():
        # Match <img src="figures/..." ... />
        md_text = re.sub(rf'<img\s+src="{re.escape(src)}"[^>]*>', svg_markup, md_text)
        # Match ![...](figures/...)
        md_text = re.sub(rf'!\[[^\]]*\]\({re.escape(src)}\)', svg_markup, md_text)

    # Convert Markdown to HTML
    html_body = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

    # Wrap chapters in semantic section breaks
    html_body = re.sub(
        r'(<h2 id="chuong-[^>]*>|<h2\b[^>]*>CHƯƠNG)',
        r'<div class="chapter-break"></div>\1',
        html_body,
    )

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Báo cáo Kỹ thuật và Tiến độ Đồ án Tốt nghiệp</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 20mm 15mm 20mm 15mm;
      @bottom-right {{
        content: counter(page);
      }}
    }}
    
    * {{
      box-sizing: border-box;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.6;
      color: #1e293b;
      margin: 0;
      padding: 0;
      background: #ffffff;
    }}

    h1, h2, h3, h4 {{
      color: #0f172a;
      font-weight: 700;
      line-height: 1.3;
      page-break-after: avoid;
    }}

    h1 {{
      font-size: 18pt;
      text-transform: uppercase;
      letter-spacing: -0.01em;
      border-bottom: 2.5px solid #2563eb;
      padding-bottom: 8px;
      margin-top: 0;
      margin-bottom: 16px;
      color: #1e3a8a;
    }}

    h2 {{
      font-size: 13.5pt;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 5px;
      margin-top: 24pt;
      margin-bottom: 12pt;
      color: #1e40af;
      text-transform: uppercase;
    }}

    h3 {{
      font-size: 11.5pt;
      margin-top: 16pt;
      margin-bottom: 8pt;
      color: #0f172a;
    }}

    h4 {{
      font-size: 10.5pt;
      margin-top: 12pt;
      margin-bottom: 6pt;
      color: #334155;
    }}

    p {{
      margin-top: 0;
      margin-bottom: 8pt;
      text-align: justify;
    }}

    ul, ol {{
      margin-top: 0;
      margin-bottom: 10pt;
      padding-left: 20px;
    }}

    li {{
      margin-bottom: 4pt;
      text-align: justify;
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 14pt 0;
      font-size: 9.5pt;
      page-break-inside: avoid;
    }}

    th, td {{
      border: 1px solid #94a3b8;
      padding: 6pt 8pt;
      text-align: left;
      vertical-align: top;
    }}

    th {{
      background-color: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
    }}

    tr:nth-child(even) {{
      background-color: #f8fafc;
    }}

    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 9pt;
      background-color: #f1f5f9;
      padding: 1.5pt 3.5pt;
      border-radius: 3px;
      color: #0f172a;
      border: 1px solid #e2e8f0;
    }}

    pre {{
      background-color: #0f172a;
      color: #f8fafc;
      padding: 10pt 12pt;
      border-radius: 6px;
      font-size: 8.5pt;
      line-height: 1.45;
      overflow-x: auto;
      page-break-inside: avoid;
      margin: 10pt 0;
    }}

    pre code {{
      background-color: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: inherit;
    }}

    blockquote {{
      border-left: 3.5px solid #3b82f6;
      background-color: #f8fafc;
      margin: 10pt 0;
      padding: 8pt 14pt;
      color: #334155;
      font-style: italic;
    }}

    .diagram-container {{
      text-align: center;
      margin: 16pt auto;
      page-break-inside: avoid;
      width: 100%;
    }}

    .diagram-container svg {{
      max-width: 100% !important;
      height: auto !important;
      display: block;
      margin: 0 auto;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(15, 23, 42, 0.05);
      background: #ffffff;
    }}

    .caption {{
      font-size: 9pt;
      color: #64748b;
      margin-top: 6pt;
      font-weight: 600;
      text-align: center;
    }}

    .chapter-break {{
      page-break-before: always;
      break-before: page;
      margin-top: 0;
      padding-top: 10pt;
    }}

    .page-break {{
      page-break-before: always;
      break-before: page;
      display: block;
      height: 0;
      margin: 0;
      padding: 0;
    }}

    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 16pt 0;
    }}

    /* Title banner styling */
    .title-banner {{
      background: #f8fafc;
      border: 1.5px solid #cbd5e1;
      border-left: 5px solid #2563eb;
      padding: 14pt 18pt;
      margin-bottom: 20pt;
      border-radius: 6px;
    }}

    .title-banner p {{
      margin-bottom: 4pt;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated HTML at: {HTML_PATH}")

def export_pdf():
    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not os.path.exists(chrome_bin):
        print(f"Error: Chrome binary not found at {chrome_bin}")
        return False
    
    cmd = [
        chrome_bin,
        "--headless",
        "--disable-gpu",
        "--allow-file-access-from-files",
        f"--print-to-pdf={PDF_PATH}",
        "--no-pdf-header-footer",
        HTML_PATH
    ]
    
    print("Executing Chrome headless PDF generation...")
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if res.returncode != 0:
        print(f"Error running Chrome: {res.stderr}")
        return False
    
    if os.path.exists(PDF_PATH):
        size_mb = os.path.getsize(PDF_PATH) / (1024 * 1024)
        print(f"Successfully generated PDF: {PDF_PATH} ({size_mb:.2f} MB)")
        
        # Verify with pypdf
        reader = pypdf.PdfReader(PDF_PATH)
        print(f"Total pages generated: {len(reader.pages)}")
        for idx in range(min(5, len(reader.pages))):
            txt = reader.pages[idx].extract_text()
            print(f"Page {idx+1}: {len(txt)} characters extracted")
        return True
    else:
        print("Error: PDF file was not created.")
        return False

if __name__ == "__main__":
    generate_html()
    export_pdf()
