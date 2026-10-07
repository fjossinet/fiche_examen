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

BOX = 14.0        # taille d'une case (pt)
GAP_X = 18.0      # écart horizontal entre cases binaires
OPT_W = 16.0      # largeur colonne option QCM

# Coordonnées des repères de coin (centres), en points
FID = {
    "tl": (30.0, PAGE_H - 30.0),
    "tr": (PAGE_W - 30.0, PAGE_H - 30.0),
    "bl": (30.0, 30.0),
    "br": (PAGE_W - 30.0, 30.0),
}
FID_SIZE = 16.0

N_SUJET_BITS = 10   # 0..999
N_ANON_BITS = 20     # 0..999999


def draw_fiducial(c, x, y):
    c.setFillColorRGB(0, 0, 0)
    c.rect(x - FID_SIZE / 2, y - FID_SIZE / 2, FID_SIZE, FID_SIZE, fill=1, stroke=0)


def draw_binary_row(c, x, y, n_bits):
    """Rangée binaire : case de rang n (gauche -> droite) vaut 2^n si noircie."""
    for n in range(n_bits):
        cx = x + n * GAP_X
        c.setStrokeGray(0.4)
        c.setLineWidth(0.7)
        c.rect(cx, y, BOX, BOX, fill=0, stroke=1)
    return (x, y, x + (n_bits - 1) * GAP_X + BOX, y + BOX)


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
                        "Noircir au stylo noir les cases choisies (encodage binaire)")

    # --- Zone sujet : 10 cases binaires ---
    sujet_x = 60.0
    sujet_y = PAGE_H - 160.0
    c.setFont("Helvetica-Bold", 9)
    c.setFillGray(0)
    c.drawString(sujet_x, sujet_y + BOX + 8, "SUJET")
    draw_binary_row(c, sujet_x, sujet_y, N_SUJET_BITS)

    # --- Zone numéro étudiant : 20 cases binaires ---
    anon_x = 60.0
    anon_y = sujet_y - 60.0
    c.drawString(anon_x, anon_y + BOX + 8, "NUMERO ETUDIANT")
    draw_binary_row(c, anon_x, anon_y, N_ANON_BITS)

    # --- Zone QCM : 20 questions x 5 options ---
    qcm_top = anon_y - 50.0
    qcm_left = 60.0
    letters = ["A", "B", "C", "D", "E"]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(qcm_left, qcm_top, "REPONSES (une case par question)")
    for i, L in enumerate(letters):
        c.drawCentredString(qcm_left + 55 + i * OPT_W, qcm_top - 12, L)

    row_h = 22.0
    for q in range(20):
        yy = qcm_top - 14 - q * row_h
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
