#!/usr/bin/env python3
"""Génère le modèle de fiche réponse (PDF A4) pour lecture par OpenMV H7.

Structure :
  - 4 repères noirs aux coins (calibration caméra)
  - Sujet : 1 rangée de 10 cases binaire (valeur = somme des 2^n des cases noircies)
  - Anonymat : 1 rangée de 20 cases binaire
  - QCM : 20 questions x 5 options (A-E)
"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

PAGE_W, PAGE_H = A4  # 595 x 842 pt

BOX = 14.0        # taille d'une case QCM (pt)
OPT_W = 16.0      # largeur colonne option QCM

DBOX = 10.0       # taille d'une case chiffre (plus petite)
DGAP_X = 14.0     # écart horizontal entre colonnes de chiffres
DGAP_Y = 12.0     # écart vertical entre rangées de chiffres

# Coordonnées des repères de coin (centres), en points
FID = {
    "tl": (30.0, PAGE_H - 30.0),
    "tr": (PAGE_W - 30.0, PAGE_H - 30.0),
    "bl": (30.0, 30.0),
    "br": (PAGE_W - 30.0, 30.0),
}
FID_SIZE = 16.0

N_SUJET_BITS = 10   # sujet binaire : 0..999
N_ETU_DIGITS = 8    # numéro étudiant décimal : 8 chiffres


def draw_fiducial(c, x, y):
    c.setFillColorRGB(0, 0, 0)
    c.rect(x - FID_SIZE / 2, y - FID_SIZE / 2, FID_SIZE, FID_SIZE, fill=1, stroke=0)


def draw_binary_row(c, x, y, n_bits):
    """Rangée binaire : case de rang n (gauche -> droite) vaut 2^n si noircie."""
    c.setStrokeGray(0.4)
    c.setLineWidth(0.6)
    for n in range(n_bits):
        c.rect(x + n * 14.0, y, DBOX, DBOX, fill=0, stroke=1)


def draw_digit_grid(c, x, y, n_digits, label):
    """Grille décimale : n_digits colonnes de 10 cases, chaque ligne
    étiquetée par son chiffre (0 en haut, 9 en bas) à gauche des cases."""
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0)
    c.drawString(x, y + 10 * DGAP_Y + 8, label)
    c.setStrokeGray(0.4)
    c.setLineWidth(0.6)
    for v in range(10):
        yy = y + (9 - v) * DGAP_Y
        c.setFont("Helvetica-Bold", 9)
        c.setFillGray(0)
        c.drawRightString(x - 4, yy + DBOX / 2 - 3, str(v))
        for d in range(n_digits):
            c.rect(x + d * DGAP_X, yy, DBOX, DBOX, fill=0, stroke=1)
    return (x, y, x + (n_digits - 1) * DGAP_X + DBOX, y + 10 * DGAP_Y)


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

    # --- Zone sujet : 10 cases binaires ---
    sujet_x = 60.0
    sujet_y = PAGE_H - 160.0
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0)
    c.drawString(sujet_x, sujet_y + DBOX + 8, "SUJET")
    draw_binary_row(c, sujet_x, sujet_y, N_SUJET_BITS)

    # --- Zone numéro étudiant : 8 chiffres décimaux ---
    etu_x = 60.0
    etu_y = sujet_y - 170.0            # bas de la grille
    draw_digit_grid(c, etu_x, etu_y, N_ETU_DIGITS, "NUMERO ETUDIANT")

    # --- Zone QCM : 20 questions x 5 options ---
    qcm_top = etu_y - 40.0
    qcm_left = 60.0
    letters = ["A", "B", "C", "D", "E"]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(qcm_left, qcm_top, "REPONSES (une case par question)")
    for i, L in enumerate(letters):
        c.drawCentredString(qcm_left + 55 + i * OPT_W + BOX / 2, qcm_top - 12, L)

    row_h = 22.0
    for q in range(20):
        yy = qcm_top - 32 - q * row_h
        c.setFont("Helvetica", 8)
        c.setFillGray(0)
        c.drawString(qcm_left, yy + 4, f"Q{q + 1:02d}")
        for i in range(5):
            bx = qcm_left + 55 + i * OPT_W
            draw_box(c, bx, yy, BOX, BOX)

    c.showPage()
    c.save()
    print(f"{path} généré ({PAGE_W:.0f}x{PAGE_H:.0f} pt)")


if __name__ == "__main__":
    generate()
