import requests
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

# 🔥 FETCH DRIVERS DATA
def fetch_drivers():
    """Fetches driver data from OpenF1 API."""
    url = "https://api.openf1.org/v1/drivers"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch drivers data")
    return response.json()

# 📄 ADD PAGE NUMBERS
def add_page_number(canvas, doc):
    """Adds page number to each page."""
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(780, 20, text)

# 🏎 DOWNLOAD DRIVER HEADSHOTS
def download_headshot(image_url, driver_id):
    """Downloads and resizes driver headshots only if not already downloaded."""
    if not image_url:
        return None  # No headshot available
    
    file_path = f"headshots/{driver_id}.png"
    os.makedirs("headshots", exist_ok=True)  # Ensure folder exists

    if os.path.exists(file_path):
        return file_path  # Return existing file path if already downloaded

    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.resize((50, 50))  # Resize for PDF
            img.save(file_path)
            return file_path
    except Exception as e:
        print(f"⚠️ Failed to download image for {driver_id}: {e}")
    
    return None  # Return None if download fails

# 📄 CREATE PDF
def create_pdf(drivers_data, filename="f1_drivers_report_heads.pdf"):
    """Generates a PDF with all F1 drivers, headshots, and team-colored rows."""
    doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()

    # 🏎 ADD F1 LOGO
    logo_path = "f1_logo.png"
    if os.path.exists(logo_path):
        logo = RLImage(logo_path, width=100, height=50)
        elements.append(logo)

    # 📌 TITLE
    title = Paragraph("<b><font size='18' color='darkred'>Formula 1 Drivers Report</font></b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # 📊 TABLE HEADERS
    table_data = [["Headshot", "Driver #", "Full Name", "Abbreviation", "Team", "DOB", "Nationality"]]

    # 📊 POPULATE TABLE
    row_colors = []
    for driver in drivers_data:
        driver_id = driver.get("driver_id", f"unknown_{driver.get('driver_number', 'N/A')}")  # Fallback ID
        headshot_url = driver.get("headshot_url", None)  # Handle missing headshot

        # Handle headshot download
        headshot = download_headshot(headshot_url, driver_id) if headshot_url else None
        image = RLImage(headshot, width=50, height=50) if headshot else "N/A"

        # Handle missing or incorrect team color
        hex_color = driver.get("team_colour")
        if not hex_color or hex_color.lower() == "none":
            hex_color = "CCCCCC"  # Default gray
        team_color = colors.HexColor(f"#{hex_color}")

        table_data.append([
            image,
            driver.get("driver_number", "N/A"),
            f"{driver.get('first_name', 'N/A')} {driver.get('last_name', 'N/A')}",
            driver.get("name_acronym", "N/A"),
            driver.get("team_name", "N/A"),
            driver.get("dob", "N/A"),
            driver.get("country_code", "N/A")
        ])
        row_colors.append(team_color)

    # 📌 CREATE TABLE
    col_widths = [60, 60, 150, 80, 140, 100, 100]
    table = Table(table_data, colWidths=col_widths)

    # 🎨 STYLE TABLE (Alternating Team Colors)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]

    # Apply row colors
    for i in range(1, len(table_data)):
        style.append(('BACKGROUND', (0, i), (-1, i), row_colors[i-1]))

    table.setStyle(TableStyle(style))
    elements.append(table)

    # 🎯 BUILD PDF
    doc.build(elements, onLaterPages=add_page_number, onFirstPage=add_page_number)
    print(f"✅ PDF '{filename}' created successfully!")

# 🎯 RUN SCRIPT
if __name__ == "__main__":
    drivers_data = fetch_drivers()
    create_pdf(drivers_data)
