"""Módulo de geração de relatórios (PDF) para LazRecon.

Fornece `save_pdf(groups, out_dir, filename)` que salva um PDF resumindo os achados.
"""

from fpdf import FPDF
import os


def save_pdf(groups: dict, out_dir: str, filename: str = "relatorio_fuzzer.pdf") -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Relatório de Reconhecimento Web - LazRecon", ln=True, align="C")
    pdf.ln(8)

    for alvo, items in groups.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(25, 8, "Alvo:", ln=0)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 8, f"{alvo}", ln=1)
        pdf.ln(3)

        for item in items:
            status = item.get("status", "")
            url = item.get("url", "")

            pdf.set_font("Arial", "B", 12)
            pdf.cell(22, 7, "Status:", ln=0)

            if status == 200 or str(status) == "200":
                pdf.set_text_color(0, 100, 0)
            elif status == 403 or str(status) == "403":
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.set_font("Arial", "B", 12)
            pdf.cell(18, 7, str(status), ln=0)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 7, f"  - {url}", ln=1)

        pdf.ln(4)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)
    pdf.output(out_path)
    return out_path

