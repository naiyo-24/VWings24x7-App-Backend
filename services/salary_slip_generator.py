from PIL import Image, ImageDraw, ImageFont

def _draw_page(template_path, teacher, salaries_page, fonts):
    img = Image.open(template_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    font, bold_font, small_font, small_bold_font = fonts

    # Teacher details in 4x4 grid
    y = 300
    left_x = 50
    right_x = img.width // 2 + 50
    details = [
        f"Name: {teacher.full_name}",
        f"Phone: {teacher.phone_no}",
        f"Email: {teacher.email}",
        f"Bank Account No: {teacher.bank_account_no}",
        f"Bank Account Name: {teacher.bank_account_name}",
        f"Bank Branch: {teacher.bank_branch_name}",
        f"IFSC: {teacher.ifsc_code}",
        f"UPI ID: {teacher.upiid}"
    ]
    for i in range(4):
        draw.text((left_x, y), details[i], fill="black", font=small_font)
        draw.text((right_x, y), details[i+4], fill="black", font=small_font)
        y += 25

    # Divider
    draw.line([(50, y), (img.width - 50, y)], fill="black", width=2)
    y += 20

    # Table header (includes Loss of Pay column)
    table_headers = ["Month", "Year", "Basic Salary", "PF", "SI", "DA", "PA", "Loss of Pay", "Total Salary", "Transaction ID"]
    x_positions = [50, 120, 180, 250, 300, 350, 400, 450, 520, 620]
    for i, header in enumerate(table_headers):
        draw.text((x_positions[i], y), header, fill="black", font=small_bold_font)
    y += 25

    # Table data for each salary on this page
    for salary in salaries_page:
        data = [
            salary.month,
            str(salary.year),
            f"{salary.basic_salary:.2f}",
            f"{salary.pf:.2f}",
            f"{salary.si:.2f}",
            f"{salary.da:.2f}",
            f"{salary.pa:.2f}",
            f"{getattr(salary, 'loss_of_pay', 0.0):.2f}",
            f"{salary.total_salary:.2f}",
            salary.transaction_id or ""
        ]
        for i, value in enumerate(data):
            draw.text((x_positions[i], y), value, fill="black", font=small_font)
        y += 25

    return img


def generate_salary_slip(teacher, salaries, output_path):
    template_path = "static/salary.jpeg"

    # Use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        bold_font = ImageFont.truetype("arialbd.ttf", 20)  # Bold font
        small_font = ImageFont.truetype("arial.ttf", 14)
        small_bold_font = ImageFont.truetype("arialbd.ttf", 14)
    except:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        small_bold_font = ImageFont.load_default()

    fonts = (font, bold_font, small_font, small_bold_font)

    # Paginate salaries: max 12 rows per page
    max_rows_per_page = 12
    pages = [salaries[i:i + max_rows_per_page] for i in range(0, len(salaries), max_rows_per_page)]
    if not pages:
        # still generate an empty page
        pages = [[]]

    images = []
    for page_salaries in pages:
        img = _draw_page(template_path, teacher, page_salaries, fonts)
        images.append(img)

    # Save as multi-page PDF
    if images:
        first, rest = images[0], images[1:]
        first.save(output_path, "PDF", resolution=100.0, save_all=True, append_images=rest)

    for im in images:
        im.close()
