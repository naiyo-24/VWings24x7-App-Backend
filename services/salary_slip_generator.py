
from reportlab.lib.pagesizes import A4
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Image
import os
from datetime import datetime

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

	# Company info
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
	y = height-150
	c.drawString(40, y, f"Teacher ID: {teacher.teacher_id}")
	c.drawString(250, y, f"Teacher Name: {teacher.full_name}")
	y -= 18
	c.drawString(40, y, f"Bank Account Name: {teacher.bank_account_name or ''}")
	c.drawString(250, y, f"Bank Name: {teacher.bank_branch_name or ''}")
	y -= 18
	c.drawString(40, y, f"Branch Name: {teacher.bank_branch_name or ''}")
	c.drawString(250, y, f"UPI ID: {teacher.upiid or ''}")
	y -= 18
	c.drawString(40, y, f"IFSC Code: {teacher.ifsc_code or ''}")

	# Salary table with columns: month, basic, da, pa, deductions, pf, si, transaction id, total
	y -= 40
	def fmt(a):
		return f"{(a or 0):.2f}"

	header = [
		"Month",
		"Basic Salary",
		"DA",
		"PA",
		"Deductions",
		"PF",
		"SI",
		"Transaction ID",
		"Total Credited",
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

	# draw a divider line above the table
	divider_y = y - 20
	left_x = 40
	right_x = width - 40
	c.setStrokeColor(colors.grey)
	c.setLineWidth(1)
	c.line(left_x, divider_y, right_x, divider_y)

	table = Table(data, colWidths=col_widths)
	table.setStyle(TableStyle([
		("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
		("TEXTCOLOR", (0,0), (-1,0), colors.black),
		("ALIGN", (1,1), (-1,-1), "RIGHT"),
		("ALIGN", (0,0), (0,-1), "LEFT"),
		("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
		("BOTTOMPADDING", (0,0), (-1,0), 8),
		("GRID", (0,0), (-1,-1), 0.5, colors.grey),
	]))
	table.wrapOn(c, width, height)
	table.drawOn(c, 60, y- (20 * len(data)))

	c.setFont("Helvetica-Oblique", 8)
	c.drawString(40, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
	c.save()
