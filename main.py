# Fiche réponse — OpenMV H7
# Lecture : sujet binaire (10 cases, 2^n), numéro étudiant décimal
# (8 chiffres, une case cochée par colonne), QCM 20x5.
# Affichage dans l'IDE OpenMV (frame buffer + terminal).
#
# Principe de lecture :
#   1. détection des 4 repères carrés noirs aux coins
#   2. homographie image -> fiche (coordonnées PDF de la fiche)
#   3. moyenne de luminosité au centre de chaque case (seuil DARK_LEVEL)

import sensor, image, time

# ----- Dimensions de la fiche (en points PDF, cf. generer_fiche.py) -----
PAGE_W, PAGE_H = 595.0, 842.0
FID = {"tl": (30.0, PAGE_H - 30.0), "tr": (565.0, PAGE_H - 30.0),
       "bl": (30.0, 30.0), "br": (565.0, 30.0)}

BOX = 14.0
OPT_W = 16.0      # largeur colonne option QCM

N_SUJET_BITS = 10
N_ETU_DIGITS = 8
N_QUEST = 20
N_OPTS = 5

SUJET_X = 60.0
SUJET_Y = PAGE_H - 160.0          # y (bas) de la rangée sujet
ETU_X = 60.0
ETU_Y = SUJET_Y - 170.0           # y (bas) de la grille numéro étudiant
QCM_LEFT = 60.0
QCM_TOP = ETU_Y - 40.0
ROW_H = 22.0

DARK_LEVEL = 90    # moyenne ROI sous ce niveau (0-255) = case noircie

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)   # 640x480
sensor.skip_frames(time=1500)

clock = time.clock()


def find_fiducials(img):
    """Retourne {nom: (cx,cy)} des 4 carrés noirs des coins."""
    quads = []
    for b in img.find_blobs([(0, 60)], area_threshold=200,
                            merge=True, margin=20):
        w, h = b.w(), b.h()
        if 0.7 < w / h < 1.4 and b.pixels() > 0.5 * w * h:
            quads.append(b)
    if len(quads) < 4:
        return {}
    quads.sort(key=lambda b: b.cx() + b.cy())      # tl -> br
    tl, br = quads[0], quads[-1]
    rest = quads[1:-1]
    rest.sort(key=lambda b: b.cx() - b.cy())       # tr -> bl
    return {"tl": (tl.cx(), tl.cy()), "br": (br.cx(), br.cy()),
            "tr": (rest[0].cx(), rest[0].cy()),
            "bl": (rest[-1].cx(), rest[-1].cy())}


def homography(src, dst):
    """Calcule H (liste de 9) tel que dst ~ H * src."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    n = 8
    M = [row + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        M[col], M[piv] = M[piv], M[col]
        p = M[col][col]
        if abs(p) < 1e-9:
            return None
        M[col] = [v / p for v in M[col]]
        for r in range(n):
            if r != col and M[r][col] != 0:
                f = M[r][col]
                M[r] = [a - f * c for a, c in zip(M[r], M[col])]
    return [M[i][8] for i in range(n)] + [1.0]


def apply_h(h, x, y):
    d = h[6] * x + h[7] * y + h[8]
    return (h[0] * x + h[1] * y + h[2]) / d, (h[3] * x + h[4] * y + h[5]) / d


def box_dark(img, h, x, y, box):
    """True si la case de coin bas-gauche fiche (x,y) est noircie.
    ROI 8x8 px pour les petites cases (10 pt), 10x10 pour les QCM (14 pt)."""
    u, w = apply_h(h, x + box / 2, y + box / 2)
    half = 5 if box >= 14.0 else 4
    roi = (int(u - half), int(w - half), half * 2, half * 2)
    return img.get_statistics(roi=roi).mean() < DARK_LEVEL


def read_binary(img, h, x0, y0, n_bits):
    """Lit une rangée binaire : case de rang n vaut 2^n si noircie."""
    val = 0
    bits = []
    for n in range(n_bits):
        if box_dark(img, h, x0 + n * 14.0, y0, 10.0):
            val += 2 ** n
            bits.append(1)
        else:
            bits.append(0)
    return val, bits


def read_digits(img, h, x0, y0, n_digits):
    """Lit une grille décimale : une case 0-9 cochée par colonne.
    Retourne le nombre (int) ou None si une colonne est vide/ambiguë."""
    DBOX, DGAP_X, DGAP_Y = 10.0, 14.0, 12.0
    s = ""
    for d in range(n_digits):
        cx = x0 + d * DGAP_X
        digit = None
        for v in range(10):
            if box_dark(img, h, cx, y0 + (9 - v) * DGAP_Y, DBOX):
                if digit is None:
                    digit = v
                else:
                    digit = -1      # plusieurs cases -> colonne invalide
        if digit is None or digit < 0:
            return None
        s += str(digit)
    return int(s)


def read_qcm(img, h):
    """Retourne {question: [options cochées]}."""
    res = {}
    for q in range(N_QUEST):
        yy = QCM_TOP - 32 - q * ROW_H
        checked = []
        for i in range(N_OPTS):
            bx = QCM_LEFT + 55 + i * OPT_W
            if box_dark(img, h, bx, yy, BOX):
                checked.append("ABCDE"[i])
        res[q + 1] = checked
    return res


while True:
    clock.tick()
    img = sensor.snapshot()
    fids = find_fiducials(img)

    if len(fids) == 4:
        src = [fids["tl"], fids["tr"], fids["bl"], fids["br"]]
        dst = [FID["tl"], FID["tr"], FID["bl"], FID["br"]]
        h = homography(src, dst)
        if h:
            sujet, s_bits = read_binary(img, h, SUJET_X, SUJET_Y, N_SUJET_BITS)
            etu = read_digits(img, h, ETU_X, ETU_Y, N_ETU_DIGITS)
            qcm = read_qcm(img, h)

            print("---- FICHE ----")
            print("Sujet    : %d  (bits %s)" % (sujet, s_bits))
            print("Numero etudiant : %s" % (etu if etu is not None else "<invalide>"))
            for q in sorted(qcm):
                if qcm[q]:
                    print("Q%02d -> %s" % (q, ",".join(qcm[q])))
            for k, (cx, cy) in fids.items():
                img.draw_cross(cx, cy, size=10)
    else:
        img.draw_string(10, 10, "Repaires non trouves (%d/4)" % len(fids))
