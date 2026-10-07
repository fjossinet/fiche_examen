# Fiche réponse — OpenMV H7
# Lecture : numéro de sujet (3 chiffres), anonymat (6 chiffres), QCM 20x5.
# Affichage dans l'IDE OpenMV (frame buffer + terminal).
#
# Principe :
#   1. seuillage Otsu -> cases noircies = blobs
#   2. détection des 4 repères carrés aux coins -> correction de perspective
#   3. lecture des cases dans des grilles virtuelles ancrées sur les repères

import sensor, image, time, math

# ----- Dimensions de la fiche (en points PDF, cf. generer_fiche.py) -----
PAGE_W, PAGE_H = 595.0, 842.0
FID = {"tl": (30.0, PAGE_H - 30.0), "tr": (565.0, PAGE_H - 30.0),
       "bl": (30.0, 30.0), "br": (565.0, 30.0)}
FID_SIZE = 16.0

BOX = 14.0
GAP_X, GAP_Y = 22.0, 20.0
OPT_W = 16.0

N_SUJET = 3      # chiffres sujet
N_ANON = 6        # chiffres anonymat
N_QUEST = 20
N_OPTS = 5

SUJET_X = 60.0
SUJET_Y = PAGE_H - 320.0 - 10 * GAP_Y          # origine basse de la grille chiffres
ANON_X = SUJET_X + 3 * GAP_X + 60.0
QCM_LEFT = 60.0
QCM_TOP = SUJET_Y + 10 * GAP_Y - 50.0           # y (haut) de la zone QCM
ROW_H = 22.0

FILL_RATIO = 0.35   # fraction de surface noire pour considérer une case cochée

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.VGA)   # 640x480
sensor.skip_frames(time=1500)

DARK_LEVEL = 90    # moyenne ROI sous ce niveau (0-255) = case noircie

clock = time.clock()


def find_fiducials(img):
    """Retourne {nom: (cx,cy)} des 4 carrés noirs des coins."""
    quads = []
    for b in img.find_blobs([(0, 60)], area_threshold=200,
                            merge=True, margin=20):
        w, h = b.w(), b.h()
        if 0.7 < w / h < 1.4 and b.pixels() > 0.5 * w * h:
            quads.append(b)
    pts = {}
    if len(quads) < 4:
        return pts
    quads.sort(key=lambda b: b.cx() + b.cy())      # tl -> br
    pts["tl"], pts["br"] = quads[0], quads[-1]
    rest = quads[1:-1]
    rest.sort(key=lambda b: b.cx() - b.cy())       # tr -> bl
    pts["tr"], pts["bl"] = rest[0], rest[-1]
    return {k: (v.cx(), v.cy()) for k, v in pts.items()}


def homography(src, dst):
    """Calcule H (3x3, liste de 9) tel que dst ~ H * src."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    # résolution Gauss 8x8
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
    h = [M[i][8] for i in range(n)] + [1.0]
    return h


def apply_h(h, x, y):
    d = h[6] * x + h[7] * y + h[8]
    return (h[0] * x + h[1] * y + h[2]) / d, (h[3] * x + h[4] * y + h[5]) / d


def read_grid(img, h, x0, y0, n_digits, values):
    """Lit une grille de chiffres : retourne la liste des chiffres (ou None)."""
    out = []
    for d in range(n_digits):
        cx = x0 + d * GAP_X
        digit = None
        for v in range(10):
            # centre de la case valeur v de la colonne d
            px = cx + BOX / 2
            py = y0 + (9 - v) * GAP_Y + BOX / 2
            u, w = apply_h(h, px, py)
            roi = (int(u - 5), int(w - 5), 10, 10)
            if img.get_statistics(roi=roi).mean() < DARK_LEVEL:
                if digit is None:
                    digit = v
                else:
                    digit = -1  # plusieurs cases -> erreur
        out.append(digit)
    return out


def read_qcm(img, h):
    """Retourne {question: [options cochées]}."""
    res = {}
    for q in range(N_QUEST):
        yy = QCM_TOP - 14 - q * ROW_H
        checked = []
        for i in range(N_OPTS):
            bx = QCM_LEFT + 55 + i * OPT_W
            px, py = bx + BOX / 2, yy + BOX / 2
            u, w = apply_h(h, px, py)
            roi = (int(u - 5), int(w - 5), 10, 10)
            if img.get_statistics(roi=roi).mean() < DARK_LEVEL:
                checked.append("ABCDE"[i])
        res[q + 1] = checked
    return res


while True:
    clock.tick()
    img = sensor.snapshot()
    fids = find_fiducials(img)

    if len(fids) == 4:
        # repères image -> repères fiche (points PDF)
        src = [fids["tl"], fids["tr"], fids["bl"], fids["br"]]
        dst = [FID["tl"], FID["tr"], FID["bl"], FID["br"]]
        h = homography(src, dst)
        if h:
            sujet = read_grid(img, h, SUJET_X, SUJET_Y, N_SUJET, 10)
            anon = read_grid(img, h, ANON_X, SUJET_Y, N_ANON, 10)
            qcm = read_qcm(img, h)

            print("---- FICHE ----")
            print("Sujet    :", sujet)
            print("Anonymat :", anon)
            for q in sorted(qcm):
                if qcm[q]:
                    print("Q%02d -> %s" % (q, ",".join(qcm[q])))
            # dessiner les repères trouvés
            for k, (cx, cy) in fids.items():
                img.draw_cross(cx, cy, size=10)
    else:
        img.draw_string(10, 10, "Repaires non trouves (%d/4)" % len(fids))
