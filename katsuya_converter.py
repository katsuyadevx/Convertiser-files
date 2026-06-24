#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import shutil
import csv
import subprocess
import base64
from pathlib import Path
import zlib

try:
    from PIL import Image
except Exception:
    Image = None

ASCII_KATSUYA = r"""
   /\_/\
  ( o.o )   へ( ^o^) へ  KATSUYA  CONVERTER
   > ^ <
"""


def colorize(text: str, rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"


def animated_logo(steps: int = 18, delay_s: float = 0.03):
    """Animation mini du logo + dégradé."""
    try:
        import time

        for i in range(steps):
            t = i / max(1, steps - 1)
            r = int(255 * min(1, max(0, t * 1.2)))
            g = int(255 * min(1, max(0, (1 - abs(t - 0.5) * 2))))
            b = int(255 * min(1, max(0, (1 - t) * 1.2)))

            sys.stdout.write("\r")
            sys.stdout.write(colorize(ASCII_KATSUYA, (r, g, b)))
            sys.stdout.flush()
            time.sleep(delay_s)

        sys.stdout.write("\r")
        sys.stdout.write(colorize(ASCII_KATSUYA, (255, 230, 120)))
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception:
        print(ASCII_KATSUYA)


def print_menu():
    lines = [
        "=== MENU KATSUYA (conversion fichiers) ===",
        "1) PNG -> JPG",
        "2) JPG/JPEG -> PNG",
        "3) TXT -> JSON ({\"text\": ...})",
        "4) JSON -> TXT (extrait text / data.text)",
        "5) JSON -> JSON (normaliser/valider)",
        "6) CSV -> JSON (en-têtes -> array d’objets)",
        "7) JSON array -> JSONL (1 objet par ligne)",
        "8) JSONL -> JSON (array)",
        "9) PDF -> TXT (si pdftotext, sinon fallback copie brute .txt)",
        "10) HTML -> TXT (strip tags basique)",
        "11) TXT -> UPPER",
        "12) TXT -> LOWER",
        "13) TXT -> GZIP (.gz)",
        "14) GZIP (.gz) -> TXT",
        "15) TEXT -> BASE64",
        "16) BASE64 -> TEXTE",
        "17) TXT -> zlib (comp)",
        "18) zlib -> TXT (tentative)",
        "19) Copier avec nouvelle extension (utility)",
        "20) Renommer (suffix + _nom_<suffix>) (utility)",
        "0) Quitter",
    ]

    steps = max(1, len(lines) - 1)
    for i, line in enumerate(lines):
        t = i / steps
        r = int(255 * min(1, max(0, t * 1.2)))
        g = int(255 * min(1, max(0, (1 - abs(t - 0.5) * 2))))
        b = int(255 * min(1, max(0, (1 - t) * 1.2)))
        try:
            print(colorize(line, (r, g, b)))
        except Exception:
            print(line)


def ensure_pillow():
    if Image is None:
        print("Erreur: Pillow n’est pas installé. Lance: pip install pillow")
        sys.exit(1)


def ask_paths():
    print("\nColle les chemins des fichiers à convertir, un par ligne.")
    print("Ex: C:/Users/.../image.png")
    print("Laisse une ligne vide quand c’est fini.\n")

    lines = []
    while True:
        try:
            s = input().strip()
        except EOFError:
            break
        if not s:
            break
        lines.append(s)

    if not lines:
        print("Aucun fichier sélectionné.")
        return []

    paths = []
    for s in lines:
        p = Path(s)
        if not p.exists() or not p.is_file():
            print(f"Ignoré (introuvable): {s}")
            continue
        paths.append(p)

    return paths


def output_dir_for(script_path: Path) -> Path:
    out = script_path.parent / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def safe_stem(p: Path) -> str:
    return p.stem


def convert_image(p: Path, out_dir: Path, target_kind: str):
    ensure_pillow()
    with Image.open(p) as im:
        if target_kind == "jpg":
            im = im.convert("RGB")
            out_path = out_dir / f"{safe_stem(p)}.jpg"
            im.save(out_path, "JPEG", quality=95, optimize=True)
            return out_path
        if target_kind == "png":
            out_path = out_dir / f"{safe_stem(p)}.png"
            im.save(out_path)
            return out_path
    raise ValueError(f"target_kind inconnu: {target_kind}")


def txt_to_json(p: Path, out_dir: Path):
    text = p.read_text(encoding="utf-8", errors="replace")
    out_path = out_dir / f"{safe_stem(p)}.json"
    out_path.write_text(json.dumps({"text": text}, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def json_to_txt(p: Path, out_dir: Path):
    data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    text = None
    if isinstance(data, dict):
        if isinstance(data.get("text"), str):
            text = data.get("text")
        elif isinstance(data.get("data"), dict) and isinstance(data.get("data", {}).get("text"), str):
            text = data.get("data", {}).get("text")
    if text is None:
        text = json.dumps(data, ensure_ascii=False, indent=2)
    out_path = out_dir / f"{safe_stem(p)}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def normalize_json(p: Path, out_dir: Path):
    data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    out_path = out_dir / f"{safe_stem(p)}.normalized.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def csv_to_json(p: Path, out_dir: Path):
    sample = "\n".join(p.read_text(encoding="utf-8", errors="replace").splitlines()[:50])
    delimiter = ','
    if ';' in sample and sample.count(';') >= sample.count(','):
        delimiter = ';'

    with p.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        rows = [row for row in reader]

    out_path = out_dir / f"{safe_stem(p)}.json"
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def json_array_to_jsonl(p: Path, out_dir: Path):
    data = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(data, list):
        raise ValueError("Le JSON ne contient pas une array (liste).")
    out_path = out_dir / f"{safe_stem(p)}.jsonl"
    lines = [json.dumps(item, ensure_ascii=False) for item in data]
    out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return out_path


def jsonl_to_json_array(p: Path, out_dir: Path):
    arr = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        arr.append(json.loads(line))
    out_path = out_dir / f"{safe_stem(p)}.json"
    out_path.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def pdf_to_txt(p: Path, out_dir: Path):
    out_path = out_dir / f"{safe_stem(p)}.txt"
    try:
        subprocess.run(
            ["pdftotext", str(p), str(out_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if out_path.exists() and out_path.stat().st_size > 0:
            return out_path
    except Exception:
        pass
    shutil.copy2(p, out_path)
    return out_path


def html_to_txt_basic(p: Path, out_dir: Path):
    import re
    raw = p.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    out_path = out_dir / f"{safe_stem(p)}.txt"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def txt_upper(p: Path, out_dir: Path):
    text = p.read_text(encoding="utf-8", errors="replace")
    out_path = out_dir / f"{safe_stem(p)}.upper.txt"
    out_path.write_text(text.upper(), encoding="utf-8")
    return out_path


def txt_lower(p: Path, out_dir: Path):
    text = p.read_text(encoding="utf-8", errors="replace")
    out_path = out_dir / f"{safe_stem(p)}.lower.txt"
    out_path.write_text(text.lower(), encoding="utf-8")
    return out_path


def txt_to_gzip(p: Path, out_dir: Path):
    import gzip
    raw = p.read_bytes()
    out_path = out_dir / f"{safe_stem(p)}.txt.gz"
    with gzip.open(out_path, "wb") as f:
        f.write(raw)
    return out_path


def gzip_to_txt(p: Path, out_dir: Path):
    import gzip
    raw = gzip.open(p, "rb").read()
    out_path = out_dir / f"{safe_stem(p)}.txt"
    out_path.write_bytes(raw)
    return out_path


def txt_to_base64(p: Path, out_dir: Path):
    raw = p.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    out_path = out_dir / f"{safe_stem(p)}.base64.txt"
    out_path.write_text(b64, encoding="utf-8")
    return out_path


def base64_to_txt(p: Path, out_dir: Path):
    s = "".join(p.read_text(encoding="utf-8", errors="replace").split())
    raw = base64.b64decode(s.encode("ascii"), validate=False)
    out_bin = out_dir / f"{safe_stem(p)}.decoded.bin"
    out_bin.write_bytes(raw)
    try:
        out_txt = out_dir / f"{safe_stem(p)}.decoded.txt"
        out_txt.write_text(raw.decode("utf-8"), encoding="utf-8")
        return out_txt
    except Exception:
        return out_bin


def txt_to_zlib_comp(p: Path, out_dir: Path):
    raw = p.read_bytes()
    comp = zlib.compress(raw, level=9)
    out_path = out_dir / f"{safe_stem(p)}.zlib.bin"
    out_path.write_bytes(comp)
    return out_path


def zlib_to_txt(p: Path, out_dir: Path):
    comp = p.read_bytes()
    raw = zlib.decompress(comp)
    out_path = out_dir / f"{safe_stem(p)}.txt"
    try:
        out_path.write_text(raw.decode("utf-8"), encoding="utf-8")
    except Exception:
        out_path.write_bytes(raw)
    return out_path


def utility_copy_with_new_ext(p: Path, out_dir: Path, target_ext: str):
    target_ext = target_ext.lower().lstrip('.')
    out_path = out_dir / f"{safe_stem(p)}.{target_ext}"
    shutil.copy2(p, out_path)
    return out_path


def utility_rename_suffix(p: Path, suffix: str):
    new_path = p.with_name(f"{p.stem}_{suffix}{p.suffix}")
    p.rename(new_path)
    return new_path


def main():
    script_path = Path(__file__).resolve()
    out_dir = output_dir_for(script_path)

    animated_logo()
    print(f"Output: {out_dir}")

    while True:
        print_menu()
        choice = input("Choix: ").strip()
        if choice == "0":
            print("Bye.")
            return

        paths = ask_paths()
        if not paths:
            continue

        try:
            results = []

            if choice == "1":
                for p in paths:
                    if p.suffix.lower() != ".png":
                        print(f"Ignoré (pas PNG): {p.name}")
                        continue
                    results.append(convert_image(p, out_dir, "jpg"))
            elif choice == "2":
                for p in paths:
                    if p.suffix.lower() not in {".jpg", ".jpeg"}:
                        print(f"Ignoré (pas JPG/JPEG): {p.name}")
                        continue
                    results.append(convert_image(p, out_dir, "png"))
            elif choice == "3":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_to_json(p, out_dir))
            elif choice == "4":
                for p in paths:
                    if p.suffix.lower() != ".json":
                        print(f"Ignoré (pas JSON): {p.name}")
                        continue
                    results.append(json_to_txt(p, out_dir))
            elif choice == "5":
                for p in paths:
                    if p.suffix.lower() != ".json":
                        print(f"Ignoré (pas JSON): {p.name}")
                        continue
                    results.append(normalize_json(p, out_dir))
            elif choice == "6":
                for p in paths:
                    if p.suffix.lower() != ".csv":
                        print(f"Ignoré (pas CSV): {p.name}")
                        continue
                    results.append(csv_to_json(p, out_dir))
            elif choice == "7":
                for p in paths:
                    if p.suffix.lower() != ".json":
                        print(f"Ignoré (pas JSON): {p.name}")
                        continue
                    results.append(json_array_to_jsonl(p, out_dir))
            elif choice == "8":
                for p in paths:
                    if p.suffix.lower() != ".jsonl":
                        print(f"Ignoré (pas JSONL): {p.name}")
                        continue
                    results.append(jsonl_to_json_array(p, out_dir))
            elif choice == "9":
                for p in paths:
                    if p.suffix.lower() != ".pdf":
                        print(f"Ignoré (pas PDF): {p.name}")
                        continue
                    results.append(pdf_to_txt(p, out_dir))
            elif choice == "10":
                for p in paths:
                    if p.suffix.lower() not in {".html", ".htm"}:
                        print(f"Ignoré (pas HTML): {p.name}")
                        continue
                    results.append(html_to_txt_basic(p, out_dir))
            elif choice == "11":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_upper(p, out_dir))
            elif choice == "12":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_lower(p, out_dir))
            elif choice == "13":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_to_gzip(p, out_dir))
            elif choice == "14":
                for p in paths:
                    if p.suffix.lower() != ".gz":
                        print(f"Ignoré (pas .gz): {p.name}")
                        continue
                    results.append(gzip_to_txt(p, out_dir))
            elif choice == "15":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_to_base64(p, out_dir))
            elif choice == "16":
                for p in paths:
                    # accepte .txt/.base64/.b64 ou autres texte base64
                    if p.suffix.lower() not in {".txt", ".base64", ".b64", ".bin"} and not p.suffix.lower().startswith('.txt'):
                        print(f"Ignoré (fichier attendu BASE64 texte): {p.name}")
                        continue
                    results.append(base64_to_txt(p, out_dir))
            elif choice == "17":
                for p in paths:
                    if p.suffix.lower() != ".txt":
                        print(f"Ignoré (pas TXT): {p.name}")
                        continue
                    results.append(txt_to_zlib_comp(p, out_dir))
            elif choice == "18":
                for p in paths:
                    results.append(zlib_to_txt(p, out_dir))
            elif choice == "19":
                target_ext = input("Extension cible (ex: png/jpg/txt/json/pdf): ").strip().lstrip('.').lower()
                if not target_ext:
                    print("Extension cible invalide.")
                    continue
                for p in paths:
                    results.append(utility_copy_with_new_ext(p, out_dir, target_ext))
            elif choice == "20":
                suffix = input("Suffixe (ex: v2, converted): ").strip()
                if not suffix:
                    print("Suffixe invalide.")
                    continue
                for p in paths:
                    results.append(utility_rename_suffix(p, suffix))
            else:
                print("Choix invalide.")
                continue

            if results:
                print("\n✅ Terminé. Fichiers générés / modifiés :")
                for r in results:
                    print(f" - {r}")
            else:
                print("\nAucun fichier converti.")

        except Exception as e:
            print(f"Erreur pendant conversion: {e}")


if __name__ == "__main__":
    main()

