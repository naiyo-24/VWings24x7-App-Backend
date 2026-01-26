from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import os
from datetime import datetime


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def generate_fees_pdf(output_dir: str, fee_data: dict) -> str:
    """
    Generate an A4 PDF for the fee record.

    Parameters
    - output_dir: directory where the PDF will be written
    - fee_data: dict containing keys: student (dict), course (dict), installments (list), totals

    Returns relative file path to generated PDF.
    """
    _ensure_dir(output_dir)
    fee_id = fee_data.get("fee_id")
    student = fee_data.get("student", {})
    course = fee_data.get("course", {})
    installments = fee_data.get("installments") or []
    totals = fee_data.get("totals", {})

    filename = f"fees_{fee_id}.pdf"
    file_path = os.path.join(output_dir, filename)

    def _draw_header_and_watermark(c):
        # draw header logo and company info and a light watermark
        width, height = A4
        margin = 20 * mm
        x = margin
        y_top = height - margin
        # use absolute path for static logo
        logo_path = os.path.join(os.getcwd(), "static", "logo.png")

        # watermark centered and rotated, low alpha (draw first so header is on top)
        if os.path.exists(logo_path):
            try:
                c.saveState()
                try:
                    c.setFillAlpha(0.06)
                except Exception:
                    pass
                cx = width / 2
                cy = height / 2
                c.translate(cx, cy)
                c.rotate(30)
                img_w = 140 * mm
                img_h = 140 * mm
                c.drawImage(logo_path, -img_w / 2, -img_h / 2, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            finally:
                try:
                    c.restoreState()
                except Exception:
                    pass

        # header logo and company info (draw on top of watermark)
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, x, y_top - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        company_x = x + 35 * mm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(company_x, y_top - 10, "VWINGS24X7")
        c.setFont("Helvetica", 9)
        c.drawString(company_x, y_top - 26, "A/90, Bapuji Nagar, Regent Estate, Jadavpur, Kolkata - 700092")
        c.drawString(company_x, y_top - 40, "Phone: +91 9875337521")
        c.drawString(company_x, y_top - 54, "Email: contact@vwings24x7.com")

        # Divider
        header_y = y_top - 70
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(margin, header_y, width - margin, header_y)

        return header_y

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    header_y = _draw_header_and_watermark(c)

    # Student details
    y = header_y - 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Student Details")
    y -= 14
    c.setFont("Helvetica", 10)
    details = [
        ("Student ID:", student.get("student_id")),
        ("Name:", student.get("full_name")),
        ("Phone:", student.get("phone_no")),
        ("Email:", student.get("email")),
        ("Address:", student.get("address")),
        ("Course:", course.get("course_name")),
    ]
    for label, val in details:
        c.drawString(margin, y, f"{label} {val or ''}")
        y -= 12

    # Divider before table
    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 18

    # Table header (no Paid At column)
    c.setFont("Helvetica-Bold", 10)
    col_x = [margin, margin + 80 * mm, margin + 140 * mm]
    headers = ["Installment No", "Transaction ID", "Amount Paid"]
    for hx, h in zip(col_x, headers):
        c.drawString(hx, y, h)
    y -= 14
    c.setFont("Helvetica", 10)

    for inst in installments:
        c.drawString(col_x[0], y, str(inst.get("installment_no", "")))
        c.drawString(col_x[1], y, str(inst.get("transaction_id", "")))
        c.drawRightString(col_x[2] + 40 * mm, y, f"{inst.get('amount_paid', 0):.2f}")
        y -= 14
        if y < 80:
            c.showPage()
            header_y = _draw_header_and_watermark(c)
            y = header_y - 18

    # Totals at bottom
    if y < 120:
        c.showPage()
        header_y = _draw_header_and_watermark(c)
        y = header_y - 18

    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, f"Total Course Fees: {totals.get('total_course_fees', 0):.2f}")
    y -= 16
    c.drawString(margin, y, f"Total Amount Paid: {totals.get('total_paid', 0):.2f}")
    y -= 16
    c.drawString(margin, y, f"Total Amount Due: {totals.get('total_due', 0):.2f}")

    c.save()
    return file_path


def generate_consolidated_fees_pdf(output_dir: str, student: dict, installments: list, totals: dict) -> str:
    """Generate a single consolidated PDF containing all installments for a student."""
    _ensure_dir(output_dir)
    filename = f"fees_all_{student.get('student_id')}.pdf"
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    def _draw_header_and_watermark(c):
        logo_path = os.path.join(os.getcwd(), "static", "logo.png")
        x = margin
        y_top = height - margin

        # watermark centered and rotated, low alpha (draw first so header is on top)
        if os.path.exists(logo_path):
            try:
                c.saveState()
                try:
                    c.setFillAlpha(0.06)
                except Exception:
                    pass
                cx = width / 2
                cy = height / 2
                c.translate(cx, cy)
                c.rotate(30)
                img_w = 140 * mm
                img_h = 140 * mm
                c.drawImage(logo_path, -img_w / 2, -img_h / 2, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            finally:
                try:
                    c.restoreState()
                except Exception:
                    pass

        # header logo and company info (draw on top of watermark)
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, x, y_top - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        company_x = x + 35 * mm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(company_x, y_top - 10, "VWINGS24X7")
        c.setFont("Helvetica", 9)
        c.drawString(company_x, y_top - 26, "A/90, Bapuji Nagar, Regent Estate, Jadavpur, Kolkata - 700092")
        c.drawString(company_x, y_top - 40, "Phone: +91 9875337521")
        c.drawString(company_x, y_top - 54, "Email: contact@vwings24x7.com")
        header_y = y_top - 70
        c.setStrokeColor(colors.grey)
        c.setLineWidth(0.5)
        c.line(margin, header_y, width - margin, header_y)
        return header_y

    header_y = _draw_header_and_watermark(c)
    # Student details
    y = header_y - 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Student Details")
    y -= 14
    c.setFont("Helvetica", 10)
    details = [
        ("Student ID:", student.get("student_id")),
        ("Name:", student.get("full_name")),
        ("Phone:", student.get("phone_no")),
        ("Email:", student.get("email")),
        ("Address:", student.get("address")),
    ]
    for label, val in details:
        c.drawString(margin, y, f"{label} {val or ''}")
        y -= 12

    # Divider before table
    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 18

    # Table header (no Paid At)
    c.setFont("Helvetica-Bold", 10)
    col_x = [margin, margin + 60 * mm, margin + 120 * mm]
    headers = ["Installment No", "Transaction ID", "Amount Paid"]
    for hx, h in zip(col_x, headers):
        c.drawString(hx, y, h)
    y -= 14
    c.setFont("Helvetica", 10)

    for inst in installments:
        c.drawString(col_x[0], y, str(inst.get("installment_no", "")))
        c.drawString(col_x[1], y, str(inst.get("transaction_id", "")))
        c.drawRightString(col_x[2] + 30 * mm, y, f"{inst.get('amount_paid', 0):.2f}")
        y -= 14
        if y < 80:
            c.showPage()
            header_y = _draw_header_and_watermark(c)
            y = header_y - 18

    # Totals
    if y < 120:
        c.showPage()
        header_y = _draw_header_and_watermark(c)
        y = header_y - 18
    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, f"Total Course Fees (sum): {totals.get('total_course_fees', 0):.2f}")
    y -= 16
    c.drawString(margin, y, f"Total Amount Paid: {totals.get('total_paid', 0):.2f}")
    y -= 16
    c.drawString(margin, y, f"Total Amount Due: {totals.get('total_due', 0):.2f}")

    c.save()
    return file_path
