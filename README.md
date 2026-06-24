# Katsuya File Converter (ASCII) 🎴

---

## ✅ Fonctionnalités (options menu)
Le menu propose 20 conversions/utilitaires :

1. **PNG -> JPG**
2. **JPG/JPEG -> PNG**
3. **TXT -> JSON** (`{"text": ...}`)
4. **JSON -> TXT** (extrait `text` ou `data.text`)
5. **JSON -> JSON** (normaliser/valider)
6. **CSV -> JSON** (1ère ligne = en-têtes, sortie = array d’objets)
7. **JSON array -> JSONL**
8. **JSONL -> JSON** (array)
9. **PDF -> TXT** (si `pdftotext` dispo, sinon fallback)
10. **HTML -> TXT** (strip tags basique)
11. **TXT -> UPPER**
12. **TXT -> LOWER**
13. **TXT -> GZIP** (`.txt.gz`)
14. **GZIP -> TXT**
15. **TXT -> BASE64**
16. **BASE64 -> TEXTE** (génère `.decoded.txt` si c’est du texte)
17. **TXT -> zlib** (`.zlib.bin`)
18. **zlib -> TXT** (tentative)
19. **Copier avec nouvelle extension** (utility)
20. **Renommer avec suffix** (utility)

---

## 🧰 Pré-requis
### Python
Installe **Python 3**.

### Pillow (uniquement pour PNG/JPG)
```bat
pip install pillow
```

### pdftotext (option PDF)
L’option PDF utilise `pdftotext` (outil externe). Si absent, le script fait un fallback.

---

## ▶️ Lancer le script
Depuis `C:/Users/ADMIN/Desktop` :

```bat
python python-scripts/katsuya_converter.py
```

Puis :
1. Choisis une **option** (1..20)
2. Colle les chemins des fichiers à convertir (1 par ligne)
3. Fais une ligne vide pour lancer la conversion

---

## 📤 Dossier de sortie
Le script crée / utilise :
- `C:/Users/ADMIN/Desktop/python-scripts/output/`

Les fichiers convertis y sont générés.

---

## Exemple rapide
1) Convertir une image :
- Choix : `1) PNG -> JPG`
- Colle :
  - `C:/Users/ADMIN/Desktop/test.png`
- Ligne vide

2) Convertir du texte :
- Choix : `3) TXT -> JSON`
- Colle :
  - `C:/Users/ADMIN/Desktop/note.txt`

---



