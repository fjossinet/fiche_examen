# Fiche réponse — OpenMV H7

Lecture automatique de fiches réponse d'examen par caméra OpenMV H7, pour
alimenter un projet de visualisation de résultats.

## Structure de la fiche (A4)

- **4 repères noirs** aux coins : calibration / correction de perspective
- **Sujet** : 1 rangée de 10 cases binaire — la case de rang n (de gauche à droite) vaut 2^n si noircie (0–999)
- **Numéro étudiant** : 8 chiffres décimaux — grille de 8 colonnes × 10 lignes (0 à 9), une case cochée par colonne
- **QCM** : 30 questions × 5 options (A–E), en 2 colonnes de 15

Les réponses QCM sont noircies au stylo noir. Le sujet est encodé en binaire
(somme des poids 2^n des cases noircies, en partant de la gauche) ; le numéro
étudiant est décimal (une case cochée par colonne de la grille).

## Contenu

| Fichier | Rôle |
|---|---|
| `generer_fiche.py` | Génère le modèle de fiche imprimable (`fiche_reponse.pdf`, nécessite `reportlab`) |
| `fiche_reponse.pdf` | Modèle de fiche prêt à imprimer |
| `main.py` | Script MicroPython à copier sur l'OpenMV H7 (affichage IDE) |

## Utilisation

1. **Générer la fiche** : `python3 generer_fiche.py` puis imprimer en A4,
   à 100 % (sans mise à l'échelle).
2. **Côté caméra** : copier `main.py` sur l'OpenMV H7 (IDE OpenMV →
   Tools → Save open script to OpenMV Cam), ou simplement l'exécuter
   depuis l'IDE connecté.
3. **Lecture** : placer la fiche bien à plat, éclairage uniforme, caméra
   perpendiculaire à la feuille. Résultats affichés dans le terminal de
   l'IDE : numéro de sujet, anonymat, réponses cochées par question.

## Principe de détection

1. Capture VGA en niveaux de gris.
2. Détection des 4 repères carrés (blobs noirs quasi pleins) aux coins.
3. Calcul d'une homographie image → fiche : chaque case est localisée par
   ses coordonnées *sur la fiche*, indépendamment de l'angle/position de la
   caméra.
4. Pour chaque case, la moyenne de luminosité d'un petit ROI au centre est
   comparée au seuil `DARK_LEVEL` (réglable, par défaut 90/255).

## Réglages

- `DARK_LEVEL` : seuil « case cochée » ; à ajuster selon stylo et éclairage.
- `sensor.set_framesize` : VGA par défaut ; passer à `sensor.HD` si plus de
  finesse nécessaire (la H7 le supporte).
- Le terminal affiche aussi le motif binaire du sujet (liste de 0/1) pour
  vérifier la lecture. Un numéro étudiant avec une colonne vide ou ambiguë
  est signalé `<invalide>`.

## Étapes suivantes possibles

- Export des résultats sur carte SD (CSV/JSON) ou en UART.
- Liaison avec le projet de visualisation ARN.
- Anti-fraude : détection de ratures (plusieurs cases par question).
