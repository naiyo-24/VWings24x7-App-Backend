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
    margin = 18 * mm

    # header: logo + company details
    logo_path = os.path.join(os.getcwd(), "static", "logo.png")
    y_top = height - margin
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, margin, y_top - 30 * mm, width=30 * mm, height=30 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    company_x = margin + 35 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(company_x, y_top - 6, "VWINGS24X7")
    c.setFont("Helvetica", 9)
    # company contact block (placeholder values - update as needed)
    company_address = "Address: [Your Address]"
    company_phone = "Phone: [Your Phone]"
    company_email = "Email: [your-email@example.com]"
    c.drawString(company_x, y_top - 22, company_address)
    c.drawString(company_x, y_top - 36, company_phone + "    " + company_email)

    # title and month on the right
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(width - margin, y_top - 6, f"Monthly Commission Report")
    c.setFont("Helvetica", 9)
    c.drawRightString(width - margin, y_top - 22, f"Month: {month_year}")

    # divider
    y = y_top - 44
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(margin, y, width - margin, y)

    # counsellor details block
    y -= 18
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Counsellor Details")
    y -= 12
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Name: {counsellor.get('full_name', '') or ''}")
    c.drawString(margin + 110 * mm, y, f"ID: {counsellor.get('counsellor_id', '') or ''}")
    y -= 12
    c.drawString(margin, y, f"Phone: {counsellor.get('phone_no', '') or ''}")
    c.drawString(margin + 110 * mm, y, f"Email: {counsellor.get('email', '') or ''}")
    y -= 12
    addr = counsellor.get('address', '') or ''
    if addr:
        # wrap address if long
        c.drawString(margin, y, f"Address: {addr}")
        y -= 12

    # second divider before table
    y -= 6
    c.line(margin, y, width - margin, y)
    y -= 14

    # table header: compute proportional columns to fit within margins
    c.setFont("Helvetica-Bold", 9)
    table_x = margin
    table_width = width - 2 * margin
    # fractions for columns: ENQ, COURSE, STUDENT, COMM%, AMT, TXN
    col_fracs = [0.12, 0.12, 0.36, 0.12, 0.12, 0.16]
    # normalize if rounding causes slight difference
    total_frac = sum(col_fracs)
    col_fracs = [f / total_frac for f in col_fracs]
    cols = [table_x]
    col_widths = []
    acc = 0.0
    for f in col_fracs:
        col_widths.append(f * table_width)
        acc += f
        cols.append(table_x + acc * table_width)
    # cols now has starting x for each column plus an extra right edge
    headers = ["Enquiry ID", "Course ID", "Student Name", "Commission %", "Amount", "Transaction ID"]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    y -= 14
    c.setFont("Helvetica", 10)

    total_amount = 0.0
    for comm in commissions:
        # Enquiry ID
        c.drawString(cols[0], y, str(comm.get('enquiry_id', '')))
        # Course ID
        c.drawString(cols[1], y, str(comm.get('course_id', '')))
        # Student Name (truncate to fit column)
        student = str(comm.get('student_name', '') or '')
        max_chars = int(col_widths[2] / (6))  # approx chars per width
        if len(student) > max_chars:
            student = student[:max_chars - 3] + '...'
        c.drawString(cols[2], y, student)
        # Commission % (right aligned)
        pct_x = cols[3] + col_widths[3] - 4
        c.drawRightString(pct_x, y, f"{comm.get('commission_percentage', 0):.2f}")
        # Amount (right aligned)
        amt_x = cols[4] + col_widths[4] - 4
        c.drawRightString(amt_x, y, f"{comm.get('commission_amount', 0):.2f}")
        # Transaction ID (truncate if long)
        tx = str(comm.get('transaction_id', '') or '')
        max_tx_chars = int(col_widths[5] / (6))
        if len(tx) > max_tx_chars:
            tx = tx[:max_tx_chars - 3] + '...'
        c.drawString(cols[5], y, tx)
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
            # redraw table headers on new page
            header_y = height - margin - 50
            for i, h in enumerate(headers):
                c.drawString(cols[i], header_y, h)
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

    # payment summary: derive overall payment status and transaction id(s)
    payment_statuses = list({(comm.get('payment_status') or '').strip() for comm in commissions if comm.get('payment_status')})
    payment_status_summary = ''
    if len(payment_statuses) == 1:
        payment_status_summary = payment_statuses[0]
    elif len(payment_statuses) > 1:
        payment_status_summary = 'MIXED'

    txs = [t for t in {comm.get('transaction_id') for comm in commissions if comm.get('transaction_id')}]
    tx_summary = ''
    if len(txs) == 1:
        tx_summary = txs[0]
    elif len(txs) > 1:
        tx_summary = ', '.join(list(txs)[:3]) + (', ...' if len(txs) > 3 else '')

    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Payment Status: {payment_status_summary}")
    c.drawRightString(width - margin, y, f"Transaction ID: {tx_summary}")

    c.save()
    return file_path
