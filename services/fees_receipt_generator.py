from PIL import Image, ImageDraw, ImageFont


def _draw_page(template_path, student, fees_list, fonts):
    img = Image.open(template_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    font, bold_font, small_font, small_bold_font = fonts

    # Student details block
    y = 260
    left_x = 50
    right_x = img.width // 2 + 50
    details = [
        f"Name: {student.full_name}",
        f"Student ID: {student.student_id}",
        f"Course: {getattr(student.course, 'course_name', '')}",
        f"Phone: {student.phone_no}",
        f"Guardian: {student.guardian_name}",
        f"Email: {student.email}",
        f"Address: {student.address}"
    ]

    # Draw two columns
    for i, detail in enumerate(details[:4]):
        draw.text((left_x, y + i * 24), detail, fill="black", font=bold_font)
    for i, detail in enumerate(details[4:]):
        draw.text((right_x, y + i * 24), detail, fill="black", font=bold_font)

    y += 110

    # Divider
    draw.line([(50, y), (img.width - 50, y)], fill="black", width=2)
    y += 20

    # Table header
    table_headers = ["Payment No", "Mode", "Transaction ID", "Amount", "Total Fees", "Paid", "Due"]
    x_positions = [50, 140, 260, 430, 520, 620, 700]
    row_height = 26
    for i, header in enumerate(table_headers):
        x = x_positions[i]
        draw.text((x, y), header, fill="black", font=small_bold_font)
        try:
            bbox = draw.textbbox((x, y), header, font=small_bold_font)
            ux0, uy0, ux1, uy1 = bbox
            draw.line([(ux0, uy1 + 2), (ux1, uy1 + 2)], fill="black", width=1)
        except Exception:
            w, h = small_bold_font.getsize(header)
            draw.line([(x, y + h + 2), (x + w, y + h + 2)], fill="black", width=1)
    y += row_height

    # Rows for each payment
    for fees in fees_list:
        data = [
            str(fees.payment_no or ""),
            fees.payment_mode or "",
            fees.transaction_id or "",
            f"{fees.amount:.2f}",
            f"{fees.total_course_fees:.2f}",
            f"{fees.amount_paid:.2f}",
            f"{fees.amount_due:.2f}"
        ]
        for i, value in enumerate(data):
            draw.text((x_positions[i], y), value, fill="black", font=small_font)
        y += row_height

    return img


def generate_fees_receipt(student, fees_list, output_path):
    template_path = "static/fees.jpeg"

    try:
        font = ImageFont.truetype("arial.ttf", 20)
        bold_font = ImageFont.truetype("arialbd.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)
        small_bold_font = ImageFont.truetype("arialbd.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
        bold_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        small_bold_font = ImageFont.load_default()

    fonts = (font, bold_font, small_font, small_bold_font)

    # Paginate if many rows: reuse approach with max rows per page
    max_rows_per_page = 20
    pages = [fees_list[i:i + max_rows_per_page] for i in range(0, len(fees_list), max_rows_per_page)]
    if not pages:
        pages = [[]]

    images = []
    for page in pages:
        img = _draw_page(template_path, student, page, fonts)
        images.append(img)

    if images:
        first, rest = images[0], images[1:]
        first.save(output_path, "PDF", resolution=1000.0, save_all=True, append_images=rest)

    for im in images:
        im.close()
