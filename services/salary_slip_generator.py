from PIL import Image, ImageDraw, ImageFont

def generate_salary_slip(teacher, salaries, output_path):
    # Load the template image
    template_path = "static/salary.jpeg"
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    # Use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Teacher details
    y = 300
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
    for detail in details:
        draw.text((50, y), detail, fill="black", font=small_font)
        y += 25
    
    # Divider
    draw.line([(50, y), (img.width - 50, y)], fill="black", width=2)
    y += 20
    
    # Table header
    table_headers = ["Month", "Year", "Basic Salary", "PF", "SI", "DA", "PA", "Total Salary", "Transaction ID"]
    x_positions = [50, 120, 180, 250, 300, 350, 400, 450, 550]
    for i, header in enumerate(table_headers):
        draw.text((x_positions[i], y), header, fill="black", font=small_font)
    y += 25
    
    # Table data for each salary
    for salary in salaries:
        data = [
            salary.month,
            str(salary.year),
            f"{salary.basic_salary:.2f}",
            f"{salary.pf:.2f}",
            f"{salary.si:.2f}",
            f"{salary.da:.2f}",
            f"{salary.pa:.2f}",
            f"{salary.total_salary:.2f}",
            salary.transaction_id or ""
        ]
        for i, value in enumerate(data):
            draw.text((x_positions[i], y), value, fill="black", font=small_font)
        y += 25
    
    # Save the image
    img.save(output_path, "JPEG")
    img.close()
