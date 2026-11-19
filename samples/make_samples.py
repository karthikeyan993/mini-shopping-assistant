"""Make the two sample inputs for step D: a drawn polo shirt (PNG) and a size chart (PDF).
Run: uv run --extra samples python samples/make_samples.py"""
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).parent


def shirt(path=HERE / "shirt.png"):
    W, H = 640, 640
    img = Image.new("RGB", (W, H), (236, 233, 228))
    body = [(170, 170), (250, 130), (390, 130), (470, 170), (560, 260), (500, 320), (450, 285), (450, 560),
            (190, 560), (190, 285), (140, 320), (80, 260)]
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(body, fill=255)
    stripes = Image.new("RGB", (W, H), (24, 38, 82))              # navy
    d = ImageDraw.Draw(stripes)
    for y in range(140, 570, 34):                                  # thin white horizontal stripes
        d.rectangle([0, y, W, y + 9], fill=(245, 245, 245))
    img.paste(stripes, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.line(body + [body[0]], fill=(15, 22, 50), width=4)
    d.polygon([(250, 130), (320, 175), (390, 130), (370, 118), (320, 150), (270, 118)], fill=(24, 38, 82),
              outline=(15, 22, 50))                                # collar
    d.rectangle([310, 160, 330, 260], fill=(24, 38, 82), outline=(15, 22, 50))   # placket
    for y in (185, 215, 245):
        d.ellipse([315, y - 5, 325, y + 5], fill=(245, 245, 245))   # buttons
    img.save(path)
    return path


def size_chart(path=HERE / "size_chart.pdf"):
    from fpdf import FPDF
    rows = [("XS", "84-88", "66"), ("S", "88-96", "68"), ("M", "96-104", "70"), ("L", "104-112", "72"),
            ("XL", "112-124", "74"), ("XXL", "124-136", "76")]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "Running T-Shirt - Size Guide (unisex)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, "Measure around the fullest part of your chest. Body length is measured from the highest "
                         "point of the shoulder. Between sizes? Choose the larger size for a relaxed fit.")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    for h, w in (("Size", 30), ("Chest (cm)", 50), ("Body length (cm)", 50)):
        pdf.cell(w, 9, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 11)
    for r in rows:
        for v, w in zip(r, (30, 50, 50)):
            pdf.cell(w, 9, v, border=1, align="C")
        pdf.ln()
    pdf.output(str(path))
    return path


if __name__ == "__main__":
    print(shirt(), size_chart())
