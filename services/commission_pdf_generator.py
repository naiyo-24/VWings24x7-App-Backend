from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import os
from datetime import datetime


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def generate_commission_pdf(output_dir: str, commission: dict) -> str:
    """Generate a simple A4 commission slip PDF.

    commission: dict with keys:
      commission_id, student_name, course_id, course_name,
      commission_percentage, course_fees, commission_amount
    """
    _ensure_dir(output_dir)
    filename = f"commission_{commission.get('commission_id')}.pdf"
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    # header
    logo_path = os.path.join(os.getcwd(), "static", "logo.png")
    y_top = height - margin
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, margin, y_top - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    company_x = margin + 35 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(company_x, y_top - 10, "VWINGS24X7")
    c.setFont("Helvetica", 9)
    c.drawString(company_x, y_top - 26, "Commission Slip")

    # details
    y = y_top - 50
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Commission Details")
    y -= 14
    c.setFont("Helvetica", 10)
    rows = [
        ("Commission ID:", commission.get("commission_id")),
        ("Student Name:", commission.get("student_name")),
        ("Enquiry ID:", commission.get("enquiry_id")),
        ("Course ID:", commission.get("course_id")),
        ("Course Name:", commission.get("course_name")),
        ("Course Fees:", f"{commission.get('course_fees',0):.2f}"),
        ("Commission %:", f"{commission.get('commission_percentage',0):.2f}"),
        ("Commission Amount:", f"{commission.get('commission_amount',0):.2f}"),
    ]
    for label, val in rows:
        c.drawString(margin, y, f"{label} {val or ''}")
        y -= 12

    # footer: month-year
    y -= 10
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Month: {commission.get('month_year')}")

    c.save()
    return file_path


def generate_monthly_commission_pdf(output_dir: str, counsellor: dict, commissions: list, month_year: str) -> str:
    """Generate a consolidated monthly commission PDF for a counsellor."""
    _ensure_dir(output_dir)
    counsellor_id = counsellor.get('counsellor_id') if isinstance(counsellor, dict) else None
    filename = f"commission_monthly_{counsellor_id}_{month_year}.pdf"
    file_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    margin = 20 * mm

    # header
    logo_path = os.path.join(os.getcwd(), "static", "logo.png")
    y_top = height - margin
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, margin, y_top - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    company_x = margin + 35 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(company_x, y_top - 10, "VWINGS24X7")
    c.setFont("Helvetica", 9)
    c.drawString(company_x, y_top - 26, f"Monthly Commission Report: {month_year}")

    # table header (only required columns)
    y = y_top - 50
    c.setFont("Helvetica-Bold", 10)
    cols = [margin, margin + 55 * mm, margin + 105 * mm, margin + 155 * mm, margin + 210 * mm]
    headers = ["Enquiry ID", "Course ID", "Student Name", "Commission %", "Amount"]
    for hx, h in zip(cols, headers):
        c.drawString(hx, y, h)
    y -= 14
    c.setFont("Helvetica", 10)

    total_amount = 0.0
    for comm in commissions:
        c.drawString(cols[0], y, str(comm.get('enquiry_id', '')))
        c.drawString(cols[1], y, str(comm.get('course_id', '')))
        c.drawString(cols[2], y, str(comm.get('student_name', ''))[:40])
        c.drawRightString(cols[3] + 18 * mm, y, f"{comm.get('commission_percentage', 0):.2f}")
        c.drawRightString(cols[4] + 15 * mm, y, f"{comm.get('commission_amount', 0):.2f}")
        total_amount += float(comm.get('commission_amount', 0) or 0)
        y -= 14
        if y < 80:
            c.showPage()
            # redraw header on new page
            if os.path.exists(logo_path):
                try:
                    c.drawImage(logo_path, margin, height - margin - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
                except Exception:
                    pass
            c.setFont("Helvetica-Bold", 10)
            for hx, h in zip(cols, headers):
                c.drawString(hx, height - margin - 50, h)
            y = height - margin - 66
            c.setFont("Helvetica", 10)

    # totals
    if y < 120:
        c.showPage()
        y = height - margin - 18
    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, f"Total Commission Amount: {total_amount:.2f}")

    c.save()
    return file_path
