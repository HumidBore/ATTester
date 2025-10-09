#!/usr/bin/env python3
import argparse
import os
import re
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MiB

def find_numeric_bin_parts(directory: Path):
    """
    Trova file con nome numerico e estensione .bin (es. 1.bin, 002.bin)
    e restituisce una lista di tuple (numero_int, Path) ordinata per numero.
    """
    numeric_re = re.compile(r"^(\d+)\.bin$")
    parts = []
    for p in directory.iterdir():
        if p.is_file():
            m = numeric_re.match(p.name)
            if m:
                parts.append((int(m.group(1)), p))
    parts.sort(key=lambda x: x[0])
    return parts

def ensure_contiguous(parts, required_n=None, start=1):
    if not parts:
        raise ValueError("Nessun file .bin numerico trovato nella cartella.")
    max_found = parts[-1][0]
    N = required_n if required_n is not None else max_found
    part_map = {num: path for num, path in parts}
    missing = [i for i in range(start, N + 1) if i not in part_map]
    if missing:
        raise ValueError(f"Mancano i seguenti file: {', '.join(str(i) + '.bin' for i in missing)}")
    ordered_paths = [part_map[i] for i in range(start, N + 1)]
    return N, ordered_paths

def merge_parts_to_mp3(parts_paths, output_path: Path, trim_last_bytes=15):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as out_f:
        for idx, part in enumerate(parts_paths, start=1):
            with part.open("rb") as in_f:
                if idx < len(parts_paths):
                    # Copia tutti i byte
                    while True:
                        chunk = in_f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        out_f.write(chunk)
                else:
                    # Ultimo file: copia tranne gli ultimi N byte
                    in_f.seek(0, os.SEEK_END)
                    size = in_f.tell()
                    read_limit = max(0, size - trim_last_bytes)
                    in_f.seek(0)
                    remaining = read_limit
                    while remaining > 0:
                        chunk = in_f.read(min(CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        out_f.write(chunk)
                        remaining -= len(chunk)
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description="Concatena file binari numerati (.bin) in un unico file .mp3, "
                    "rimuovendo gli ultimi 15 byte dall'ultimo file."
    )
    parser.add_argument("-d", "--dir", default=".", help="Cartella contenente i file .bin (default: .)")
    parser.add_argument("-o", "--output", default="output.mp3", help="File MP3 di destinazione")
    parser.add_argument("-n", "--num", type=int, default=None, help="Numero massimo N (facoltativo)")
    parser.add_argument("--start", type=int, default=1, help="Numero iniziale (default: 1)")
    parser.add_argument("--trim", type=int, default=15, help="Byte da rimuovere alla fine dell'ultimo file (default: 15)")
    args = parser.parse_args()

    directory = Path(args.dir).resolve()
    output_path = Path(args.output).resolve()

    if not directory.exists():
        raise SystemExit(f"Errore: la cartella '{directory}' non esiste.")
    if output_path.exists():
        print(f"Attenzione: sovrascriverò '{output_path}'.")

    parts = find_numeric_bin_parts(directory)
    try:
        N, ordered_paths = ensure_contiguous(parts, required_n=args.num, start=args.start)
    except ValueError as e:
        raise SystemExit(str(e))

    print(f"Trovati {len(ordered_paths)} file .bin da {args.start} a {N}.")
    print(f"L'ultimo file verrà accorciato di {args.trim} byte.")
    print(f"Unione in: {output_path}")

    merged = merge_parts_to_mp3(ordered_paths, output_path, trim_last_bytes=args.trim)
    print(f"Fatto! File creato: {merged}")

if __name__ == "__main__":
    main()
