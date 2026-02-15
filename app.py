"""
QR Contact Card Generator - Flask Web Application
Sompalli & Co | CA Community Tool
"""

from flask import Flask, render_template, request, jsonify, send_file
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

app = Flask(__name__)

def build_vcard(data):
    """Build a vCard 3.0 string from form data."""
    lines = ["BEGIN:VCARD", "VERSION:3.0"]

    full_name = data.get("name", "").strip()
    if full_name:
        parts = full_name.split(" ", 1)
        first = parts[0]
        last  = parts[1] if len(parts) > 1 else ""
        lines.append(f"FN:{full_name}")
        lines.append(f"N:{last};{first};;;")

    if data.get("org"):
        lines.append(f"ORG:{data['org'].strip()}")
    if data.get("title"):
        lines.append(f"TITLE:{data['title'].strip()}")
    if data.get("phone"):
        lines.append(f"TEL;TYPE=CELL:{data['phone'].strip()}")
    if data.get("phone2"):
        lines.append(f"TEL;TYPE=WORK:{data['phone2'].strip()}")
    if data.get("email"):
        lines.append(f"EMAIL;TYPE=INTERNET:{data['email'].strip()}")
    if data.get("website"):
        url = data['website'].strip()
        if url and not url.startswith("http"):
            url = "https://" + url
        lines.append(f"URL:{url}")
    if data.get("address"):
        lines.append(f"ADR;TYPE=WORK:;;{data['address'].strip()};;;;")
    if data.get("linkedin"):
        lines.append(f"X-SOCIALPROFILE;type=linkedin:{data['linkedin'].strip()}")
    if data.get("note"):
        lines.append(f"NOTE:{data['note'].strip()}")

    lines.append("END:VCARD")
    return "\r\n".join(lines)


def generate_qr_image(vcard_str, color_scheme):
    """Generate a styled QR code image and return as base64 PNG."""

    schemes = {
        "navy":   {"fill": "#0D2B55", "back": "#FFFFFF", "banner": "#0D2B55", "accent": "#F5C842"},
        "green":  {"fill": "#1A4731", "back": "#FFFFFF", "banner": "#1A4731", "accent": "#4ADE80"},
        "maroon": {"fill": "#6B0F1A", "back": "#FFFFFF", "banner": "#6B0F1A", "accent": "#FCA5A5"},
        "black":  {"fill": "#111111", "back": "#FFFFFF", "banner": "#111111", "accent": "#F59E0B"},
        "purple": {"fill": "#3B0764", "back": "#FFFFFF", "banner": "#3B0764", "accent": "#C084FC"},
    }
    scheme = schemes.get(color_scheme, schemes["navy"])

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard_str)
    qr.make(fit=True)

    qr_img = qr.make_image(
        fill_color=scheme["fill"],
        back_color=scheme["back"]
    ).convert("RGBA")

    qr_w, qr_h = qr_img.size
    banner_h = 80
    canvas = Image.new("RGBA", (qr_w, qr_h + banner_h), "#FFFFFF")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, qr_h), (qr_w, qr_h + banner_h)], fill=scheme["banner"])

    # Fonts
    try:
        font_name   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
        font_sub    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_scan   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", 10)
    except IOError:
        font_name = font_sub = font_scan = ImageFont.load_default()

    def cx(text, font):
        bb = draw.textbbox((0, 0), text, font=font)
        return (qr_w - (bb[2] - bb[0])) // 2

    draw.text((cx("Scan to Save Contact", font_name), qr_h + 8),
              "Scan to Save Contact", font=font_name, fill=scheme["accent"])
    draw.text((cx("📱 vCard Contact QR Code", font_sub), qr_h + 32),
              "📱 vCard Contact QR Code", font=font_sub, fill="#FFFFFF")
    draw.text((cx("Works with iPhone & Android Camera", font_scan), qr_h + 56),
              "Works with iPhone & Android Camera", font=font_scan, fill="#AACBFF")

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", quality=95)
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "Name is required"}), 400

    color = data.get("color", "navy")
    vcard = build_vcard(data)
    img_b64 = generate_qr_image(vcard, color)

    return jsonify({
        "success": True,
        "image":   img_b64,
        "vcard":   vcard,
    })


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    color = data.get("color", "navy")
    vcard = build_vcard(data)
    img_b64 = generate_qr_image(vcard, color)

    img_bytes = base64.b64decode(img_b64)
    buf = io.BytesIO(img_bytes)
    buf.seek(0)

    name_slug = data.get("name", "contact").replace(" ", "_").lower()
    return send_file(
        buf,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"{name_slug}_qr_contact.png"
    )


if __name__ == "__main__":
    print("=" * 50)
    print("  QR Contact Card Generator")
    print("  Sompalli & Co")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)