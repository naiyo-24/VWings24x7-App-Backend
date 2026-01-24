
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Image
import os
from datetime import datetime


def fmt(a):
	try:
		return f"{float(a or 0):.2f}"
	except Exception:
		return "0.00"

def generate_salary_slip_pdf(pdf_path, teacher, slips: list):
	"""
	Generate a single landscape PDF for a teacher containing multiple salary rows.

	`slips` is a list of dicts with keys:
	  month, year, basic_salary, da_amount, pa_amount, deductions,
	  pf_amount, si_amount, transaction_id, total_amount, optional percents
	"""
	# Company info
	company_name = "VWings24x7"
	company_address = "A/90, Bapuji Nagar, Regent Estate, Jadavpur, Kolkata - 700092"
	company_phone = "+91 9875337521"
	company_email = "contact@vwings24x7.com"
	logo_path = os.path.join("static", "logo.png")

	page_size = landscape(A4)
	c = canvas.Canvas(pdf_path, pagesize=page_size)
	width, height = page_size

	def _draw_header_and_get_table_top():
		# Draw logo + company info + title + teacher info, return divider_y and table_top
		if os.path.exists(logo_path):
			c.drawImage(logo_path, 30, height-90, width=60, height=60, mask='auto')
		c.setFont("Helvetica-Bold", 18)
		c.drawString(100, height-60, company_name)
		c.setFont("Helvetica", 10)
		c.drawString(100, height-80, company_address)
		c.drawString(100, height-95, f"Phone: {company_phone}  Email: {company_email}")

		# Title
		c.setFont("Helvetica-Bold", 16)
		c.drawCentredString(width/2, height-120, f"Salary Slips for {teacher.full_name}")

		# Teacher & bank info
		c.setFont("Helvetica", 11)
		y_local = height-150
		c.drawString(40, y_local, f"Teacher ID: {teacher.teacher_id}")
		c.drawString(250, y_local, f"Teacher Name: {teacher.full_name}")
		y_local -= 18
		c.drawString(40, y_local, f"Bank Account Name: {teacher.bank_account_name or ''}")
		c.drawString(250, y_local, f"Bank Name: {teacher.bank_branch_name or ''}")
		y_local -= 18
		c.drawString(40, y_local, f"Branch Name: {teacher.bank_branch_name or ''}")
		c.drawString(250, y_local, f"UPI ID: {teacher.upiid or ''}")
		y_local -= 18
		c.drawString(40, y_local, f"IFSC Code: {teacher.ifsc_code or ''}")

		# divider and table_top
		divider_y_local = y_local - 10
		table_top_local = divider_y_local - 18
		# draw divider
		left_x = 40
		right_x = width - 40
		c.setStrokeColor(colors.grey)
		c.setLineWidth(1)
		c.line(left_x, divider_y_local, right_x, divider_y_local)
		return divider_y_local, table_top_local

	def _draw_minimal_header_and_get_table_top():
		# Draw only company logo and company info (no teacher details or title)
		if os.path.exists(logo_path):
			c.drawImage(logo_path, 30, height-90, width=60, height=60, mask='auto')
		c.setFont("Helvetica-Bold", 18)
		c.drawString(100, height-60, company_name)
		c.setFont("Helvetica", 10)
		c.drawString(100, height-80, company_address)
		c.drawString(100, height-95, f"Phone: {company_phone}  Email: {company_email}")

		# Draw teacher & bank info (same block as full header, but omit centered title)
		c.setFont("Helvetica", 11)
		y_local = height-150
		c.drawString(40, y_local, f"Teacher ID: {teacher.teacher_id}")
		c.drawString(250, y_local, f"Teacher Name: {teacher.full_name}")
		y_local -= 18
		c.drawString(40, y_local, f"Bank Account Name: {teacher.bank_account_name or ''}")
		c.drawString(250, y_local, f"Bank Name: {teacher.bank_branch_name or ''}")
		y_local -= 18
		c.drawString(40, y_local, f"Branch Name: {teacher.bank_branch_name or ''}")
		c.drawString(250, y_local, f"UPI ID: {teacher.upiid or ''}")
		y_local -= 18
		c.drawString(40, y_local, f"IFSC Code: {teacher.ifsc_code or ''}")

		# divider and table_top match full header calculations
		divider_y_local = y_local - 10
		table_top_local = divider_y_local - 18
		left_x = 40
		right_x = width - 40
		c.setStrokeColor(colors.grey)
		c.setLineWidth(1)
		c.line(left_x, divider_y_local, right_x, divider_y_local)
		return divider_y_local, table_top_local

	# Watermark
	if os.path.exists(logo_path):
		c.saveState()
		c.translate(width/2, height/2)
		c.rotate(30)
		c.setFillAlpha(0.08)
		c.drawImage(logo_path, -150, -150, width=300, height=300, mask='auto')
		c.restoreState()

	# Logo at top
	if os.path.exists(logo_path):
		c.drawImage(logo_path, 30, height-90, width=60, height=60, mask='auto')

	# Initial header draw
	divider_y, table_top = _draw_header_and_get_table_top()
	header = [
		"Month",
		"Basic Salary",
		"DA",
		"PA",
		"Deductions",
		"PF",
		"SI",
		"Transaction ID",
		"Total",
	]

	data = [header]
	for s in slips:
		month_label = f"{s.get('month')} {s.get('year')}"
		# ensure numeric components and recompute total to avoid overrides
		basic = float(s.get('basic_salary') or 0)
		da_amt = float(s.get('da_amount') or 0)
		pa_amt = float(s.get('pa_amount') or 0)
		deductions_amt = float(s.get('deductions') or 0)
		pf_amt = float(s.get('pf_amount') or 0)
		si_amt = float(s.get('si_amount') or 0)
		total_amt = basic + da_amt + pa_amt - pf_amt - si_amt - deductions_amt

		row = [
			month_label,
			fmt(basic),
			fmt(da_amt),
			fmt(pa_amt),
			fmt(deductions_amt),
			fmt(pf_amt),
			fmt(si_amt),
			str(s.get('transaction_id') or ""),
			fmt(total_amt),
		]
		data.append(row)

	# column widths (distribute across width)
	total_width = width - 120
	col_widths = [total_width * 0.16, total_width * 0.12, total_width * 0.10, total_width * 0.10,
				  total_width * 0.10, total_width * 0.10, total_width * 0.10, total_width * 0.14, total_width * 0.08]
	# Pagination: compute rows per page based on available space
	bottom_margin = 60
	footer_height = 30
	row_h = 20
	available_height = table_top - bottom_margin
	# rows per page (excluding header row)
	rows_per_page = max(1, int(available_height // row_h) - 1)

	# prepare table style
	table_style = TableStyle([
		("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
		("TEXTCOLOR", (0,0), (-1,0), colors.black),
		("ALIGN", (1,1), (-1,-1), "RIGHT"),
		("ALIGN", (0,0), (0,-1), "LEFT"),
		("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
		("BOTTOMPADDING", (0,0), (-1,0), 8),
		("GRID", (0,0), (-1,-1), 0.5, colors.grey),
	])

	# chunk rows
	rows = data[1:]
	pages = [rows[i:i+rows_per_page] for i in range(0, len(rows), rows_per_page)]

	for page_index, page_rows in enumerate(pages):
		page_data = [header] + page_rows
		table = Table(page_data, colWidths=col_widths)
		table.setStyle(table_style)
		table.wrapOn(c, width, height)
		table_height = row_h * len(page_data)
		table_y = table_top - table_height
		table.drawOn(c, 60, table_y)

		# footer: Generated on (left) and Powered by (right)
		footer_y = 30
		c.setFont("Helvetica-Oblique", 8)
		gen_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
		c.drawString(40, footer_y, gen_text)
		powered_text = "Powered by Naiyo24"
		powered_w = c.stringWidth(powered_text, "Helvetica-Oblique", 8)
		c.drawString(width - 40 - powered_w, footer_y, powered_text)

		if page_index < len(pages) - 1:
			c.showPage()
			# draw a minimal header on subsequent pages to keep divider/table aligned
			divider_y, table_top = _draw_minimal_header_and_get_table_top()

	c.setFont("Helvetica-Oblique", 8)
	gen_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
	c.drawString(40, 30, gen_text)
	# Powered by text to the right of the timestamp
	c.setFont("Helvetica-Oblique", 8)
	c.drawString(40 + max(200, len(gen_text) * 4), 30, "Powered by Naiyo24")
	c.save()
