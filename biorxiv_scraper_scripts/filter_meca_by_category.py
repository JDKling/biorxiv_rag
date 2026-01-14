#!/usr/bin/env python3
import os, csv, sys, argparse
from lxml import etree

def parse_args():
    ap = argparse.ArgumentParser(description="Filter bioRxiv MECA packages by subject category.")
    ap.add_argument("--root", required=True, help="Root directory of unpacked MECA (per-month).")
    ap.add_argument("--out", required=True, help="Output directory for kept content (per-month).")
    ap.add_argument("--logs", required=True, help="Directory for logs.")
    ap.add_argument("--keep", action="append", default=[], help="Category to keep (can repeat). Case-insensitive match.")
    return ap.parse_args()

def text_or_none(el):
    return el.text.strip() if el is not None and el.text else None

def lower_set(xs):
    return {x.lower() for x in xs}

def main():
    args = parse_args()
    ROOT_DIR = os.path.abspath(os.path.expanduser(args.root))
    OUT_DIR  = os.path.abspath(os.path.expanduser(args.out))
    LOGS_DIR = os.path.abspath(os.path.expanduser(args.logs))

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

    keep_lc = lower_set(args.keep)
    if not keep_lc:
        print("[WARN] No --keep categories provided; nothing will be selected.", file=sys.stderr)

    meta_path = os.path.join(OUT_DIR, "metadata.csv")
    seen_headers = os.path.exists(meta_path)

    with open(meta_path, "a", newline="", encoding="utf-8") as meta_f:
        w = csv.writer(meta_f)
        if not seen_headers:
            w.writerow([
                "uuid","title","doi","version","license","categories",
                "authors","year","xml_path"
            ])

        # Process flattened XML files directly
        for xml_file in os.listdir(ROOT_DIR):
            if not xml_file.endswith('.xml'):
                continue
                
            xml_path = os.path.join(ROOT_DIR, xml_file)
            uuid = xml_file[:-4]  # Remove .xml extension
            
            try:
                tree = etree.parse(xml_path)
            except Exception as e:
                sys.stderr.write(f"[XML parse error] {xml_path}: {e}\n")
                continue

            # Categories: Extract from subject elements in article-categories
            cats_raw = set()
            
            # Look for subjects in article-categories, especially hwp-journal-coll type
            for el in tree.findall(".//article-categories//subject"):
                if el.text and el.text.strip():
                    cats_raw.add(el.text.strip())
            
            # Also check for keywords if no categories found
            if not cats_raw:
                for el in tree.findall(".//kwd"):
                    if el.text and el.text.strip():
                        cats_raw.add(el.text.strip())

            cats_lc = lower_set(cats_raw)
            keep = bool(keep_lc & cats_lc)

            # Metadata extraction from JATS XML structure
            title = text_or_none(tree.find(".//article-title"))
            doi = text_or_none(tree.find(".//article-id[@pub-id-type='doi']"))
            version = text_or_none(tree.find(".//article-version")) or ""
            
            # Extract license information
            license_text = ""
            lic_el = tree.find(".//license")
            if lic_el is not None:
                href = lic_el.get("{http://www.w3.org/1999/xlink}href")
                if href:
                    license_text = href
                elif lic_el.text:
                    license_text = lic_el.text.strip()
            
            # Extract authors
            authors = []
            for contrib in tree.findall(".//contrib[@contrib-type='author']"):
                name_el = contrib.find(".//name")
                if name_el is not None:
                    surname = text_or_none(name_el.find("surname")) or ""
                    given_names = text_or_none(name_el.find("given-names")) or ""
                    if surname or given_names:
                        full_name = f"{given_names} {surname}".strip()
                        authors.append(full_name)
            
            # Extract publication year
            year = ""
            year_el = tree.find(".//pub-date[@pub-type='epub']/year")
            if year_el is not None:
                year = text_or_none(year_el) or ""

            if keep:
                # Copy XML file to output directory with same filename
                dst = os.path.join(OUT_DIR, xml_file)
                if not os.path.exists(dst):
                    try:
                        with open(xml_path, "rb") as s, open(dst, "wb") as d:
                            d.write(s.read())
                    except Exception as e:
                        sys.stderr.write(f"[copy error] {xml_path} -> {dst}: {e}\n")
                
                w.writerow([
                    uuid, title or "", doi or "", version, license_text,
                    "; ".join(sorted(cats_raw)) if cats_raw else "",
                    "; ".join(authors) if authors else "",
                    year,
                    xml_file
                ])
            else:
                with open(os.path.join(LOGS_DIR, "skipped.txt"), "a", encoding="utf-8") as sf:
                    sf.write(f"{xml_path}\t{'; '.join(sorted(cats_raw))}\n")

if __name__ == "__main__":
    main()