# 📇 QR Contact Card Generator
### Sompalli & Co · CA Community Tool

> A professional Flask web application that generates **vCard QR codes**.
> When scanned, the QR code automatically prompts the phone to save the contact — no app required.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [Features](#features)
- [How the QR Code Works](#how-the-qr-code-works)
- [API Endpoints](#api-endpoints)
- [Colour Themes](#colour-themes)
- [Troubleshooting](#troubleshooting)
- [About](#about)

---

## 🌟 Overview

This tool allows Chartered Accountants and professionals to instantly generate a **contact QR code** from a simple web form. The QR code uses the **vCard 3.0** standard, which is universally recognised by both iPhone and Android cameras. No third-party scanner app is needed — just point the camera and tap "Add Contact".

---

## 📁 Project Structure

```
qr_contact_app/
├── app.py                  ← Flask backend (routes + QR generation logic)
├── requirements.txt        ← Python dependencies
├── templates/
│   └── index.html          ← Frontend UI (HTML + CSS + JavaScript)
└── README.md               ← This file
```

---

## 📦 Requirements

| Package | Version | Purpose |
|---|---|---|
| `flask` | >= 2.3.0 | Web framework — runs the server and handles routes |
| `qrcode[pil]` | >= 7.4.2 | Generates the QR code image |
| `pillow` | >= 10.0.0 | Image processing — adds banner, fonts, and colours |

---

## ⚙️ Installation

**Step 1 — Make sure Python is installed (3.8 or above)**
```bash
python --version
```

**Step 2 — (Optional) Create a virtual environment**
```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac / Linux
source venv/bin/activate
```

**Step 3 — Install all dependencies**
```bash
pip install -r requirements.txt
```

---

## 🚀 How to Run

```bash
python app.py
```

Then open your browser and go to:
```
http://localhost:5000
```

To stop the server, press `Ctrl + C` in the terminal.

---

## ✨ Features

- ✅ **10 contact fields** — Name, Title, Organisation, Mobile, Work Phone, Email, Website, LinkedIn, Address, Note
- ✅ **5 professional colour themes** — Navy Blue, Forest Green, Maroon, Charcoal Black, Royal Purple
- ✅ **Instant QR preview** — appears on the right panel as soon as you click Generate
- ✅ **Download PNG** — saves a high-resolution QR image named after the person
- ✅ **Copy to clipboard** — paste directly into WhatsApp, email, or anywhere
- ✅ **View raw vCard data** — toggle to inspect the encoded contact string
- ✅ **Pre-filled with real data** — form opens ready to use, just click Generate
- ✅ **Mobile compatible** — works with iPhone Camera and all Android phones

---

## 📱 How the QR Code Works

The QR code encodes a **vCard 3.0** string — the universal contact card format.

```
BEGIN:VCARD
VERSION:3.0
FN:Praveen Sompalli
N:Sompalli;Praveen;;;
ORG:Sompalli & Co
TITLE:Qualified Chartered Accountant
TEL;TYPE=CELL:+918686018476
EMAIL;TYPE=INTERNET:praveen@sompalliandco.com
URL:https://sompalliandco.com/about
END:VCARD
```

**How to scan:**
1. Open your phone **Camera** (no app needed)
2. Point it at the QR code
3. A notification appears — tap **"Add Contact"**
4. All details are saved automatically ✓

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Loads the web form |
| `POST` | `/generate` | Generates QR code, returns base64 PNG + vCard string |
| `POST` | `/download` | Generates and downloads QR code as PNG file |

**Sample `/generate` request body:**
```json
{
  "name":    "Praveen Sompalli",
  "title":   "Qualified Chartered Accountant",
  "org":     "Sompalli & Co",
  "phone":   "+918686018476",
  "email":   "praveen@sompalliandco.com",
  "website": "https://sompalliandco.com/about",
  "color":   "navy"
}
```

---

## 🎨 Colour Themes

| Theme | Hex Code | Best For |
|---|---|---|
| Navy Blue | `#0D2B55` | Finance, Legal, Corporate |
| Forest Green | `#1A4731` | Sustainability, Healthcare |
| Maroon | `#6B0F1A` | Traditional, Premium |
| Charcoal Black | `#111111` | Modern, Minimalist |
| Royal Purple | `#3B0764` | Creative, Tech |

---

## 🛠️ Troubleshooting

**Port already in use?**
```bash
# Run on a different port
python app.py --port 8080
# Or edit app.py and change port=5000 to port=8080
```

**Module not found error?**
```bash
pip install -r requirements.txt
```

**QR code not scanning?**
- Ensure good lighting when scanning
- Keep camera steady for 1–2 seconds
- Try increasing screen brightness

---

## 👤 About

**Praveen Sompalli**
Qualified Chartered Accountant
📧 praveen@sompalliandco.com
📞 +918686018476
🌐 https://sompalliandco.com/about

---

*Built with ❤️ for the CA Community by Sompalli & Co*