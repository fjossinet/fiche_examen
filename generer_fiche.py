#!/usr/bin/env python3
"""Génère le modèle de fiche réponse (PDF A4) pour lecture par OpenMV H7.

Structure :
  - 4 repères noirs aux coins (calibration caméra)
  - Sujet : 3 chiffres (0-9)
  - Anonymat : 6 chiffres (0-9)
  - QCM : 20 questions x 5 options (A-E)
"""
import math

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4  # 595 x 842 pt

BOX = 14.0        # taille d'une case (pt)
GAP_X = 22.0      # écart horizontal entre colonnes de chiffres
GAP_Y = 20.0      # écart vertical entre rangées
OPT_W = 16.0      # largeur colonne option QCM

# Coordonnées des repères de coin (centres), en points
FID = {
    "tl": (30.0, PAGE_H - 30.0),
    "tr": (PAGE_W - 30.0, PAGE_H - 30.0),
    "bl": (30.0, 30.0),
    "br": (PAGE_W - 30.0, 30.0),
}
FID_SIZE = 16.0


def draw_fiducial(c, x, y):
    c.setFillColorRGB(0, 0, 0)
    c.rect(x - FID_SIZE / 2, y - FID_SIZE / 2, FID_SIZE, FID_SIZE, fill=1, stroke=0)


def draw_digit_row(c, x, y, n_digits, label):
    """Une rangée de n_digits colonnes de 0-9. Retourne la bbox (x0,y0,x1,y1)."""
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0)
    c.drawString(x, y + 10 * GAP_Y + 12, label)
    for d in range(n_digits):
        cx = x + d * GAP_X
        c.setFont("Helvetica", 6)
        c.drawCentredString(cx + BOX / 2, y + 10 * GAP_Y + 2, str(d))
        for v in range(10):
            yy = y + (9 - v) * GAP_Y
            c.setStrokeGray(0.4)
            c.setLineWidth(0.7)
            c.rect(cx, yy, BOX, BOX, fill=0, stroke=1)
            c.setFont("Helvetica", 5)
            c.setFillGray(0.35)
            c.drawCentredString(cx + BOX / 2, yy + BOX / 2 - 2, str(v))
            c.setFillGray(0)
    return (x, y, x + (n_digits - 1) * GAP_X + BOX, y + 10 * GAP_Y)


def draw_box(c, x, y, w, h):
    c.setStrokeGray(0.4)
    c.setLineWidth(0.7)
    c.rect(x, y, w, h, fill=0, stroke=1)


def generate(path="fiche_reponse.pdf"):
    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("Fiche reponse - OpenMV H7")

    for name, (x, y) in FID.items():
        draw_fiducial(c, x, y)

    # Titre
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 55, "FICHE REPONSE")
    c.setFont("Helvetica", 8)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 68,
                        "Noircir au stylo noir les cases choisies")

    # --- Zone sujet (3 chiffres) ---
    sujet_x = 60.0
    sujet_y = PAGE_H - 320.0
    sb = draw_digit_row(c, sujet_x, sujet_y, 3, "SUJET (3 chiffres)")

    # --- Zone anonymat (6 chiffres), à droite ---
    anon_x = sujet_x + 3 * GAP_X + 60.0
    draw_digit_row(c, anon_x, sujet_y, 6, "ANONYMAT (6 chiffres)")

    # --- Zone QCM : 20 questions x 5 options ---
    qcm_top = sujet_y - 50.0
    qcm_left = 60.0
    letters = ["A", "B", "C", "D", "E"]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(qcm_left, qcm_top + 5, "REPONSES (une case par question)")
    for i, L in enumerate(letters):
        c.drawCentredString(qcm_left + 55 + i * OPT_W, qcm_top + 5, L)

    qcm_boxes = []
    row_h = 22.0
    for q in range(20):
        yy = qcm_top - 14 - q * row_h
        c.setFont("Helvetica", 8)
        c.setFillGray(0)
        c.drawString(qcm_left, yy + 4, f"Q{q + 1:02d}")
        for i in range(5):
            bx = qcm_left + 55 + i * OPT_W
            draw_box(c, bx, yy, BOX, BOX)
            qcm_boxes.append((q + 1, L, bx, yy))

    c.showPage()
    c.save()
    print(f"{path} généré ({PAGE_W:.0f}x{PAGE_H:.0f} pt)")


if __name__ == "__main__":
    generate()
