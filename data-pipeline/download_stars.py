"""
Generate a comprehensive bright star catalog from VizieR Hipparcos
Output: hipparcos_bright.csv (~40,000 stars, Vmag < 8.5)
Run once: python download_stars.py
"""

import os
import sys
import csv

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hipparcos_bright.csv")

def main():
    print("Downloading Hipparcos bright star catalog (Vmag < 8.5)...")
    print("This may take a minute...")

    try:
        from astroquery.vizier import Vizier
    except ImportError:
        print("ERROR: astroquery not installed.")
        print("Run: pip install astroquery")
        sys.exit(1)

    Vizier.ROW_LIMIT = 100000

    # Try CDS Strasbourg (primary), then mirrors
    for server in ["cdsarc.u-strasbg.fr", "vizier.cds.unistra.fr", "vizier.hia.nrc.ca"]:
        try:
            Vizier.VIZIER_SERVER = server
            print(f"  Trying {server}...")
            result = Vizier.query_constraints(
                catalog="I/239/hip_main",
                Vmag="<8.5",
                columns=["HIP", "RAJ2000", "DEJ2000", "Vmag", "Plx", "SpType"],
            )
            if result and len(result) > 0:
                break
        except Exception as e:
            print(f"  Failed: {e}")
            continue

    if not result or len(result) == 0:
        print("\nAll VizieR servers failed.")
        print("Try manual download:")
        print("  https://cdsarc.u-strasbg.fr/viz-bin/Cat?I/239")
        sys.exit(1)

    table = result[0]
    print(f"\nDownloaded {len(table)} stars!")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["HIP", "RA", "Dec", "Vmag", "Plx", "SpType"])
        for row in table:
            try:
                hip = int(row["HIP"])
                ra = float(row["RAJ2000"])
                dec = float(row["DEJ2000"])
                vmag = float(row["Vmag"]) if row["Vmag"] else 9.0
                plx = float(row["Plx"]) if row["Plx"] else 0
                sp = str(row["SpType"]).strip() if row["SpType"] else ""
                writer.writerow([hip, ra, dec, vmag, plx, sp])
            except (ValueError, KeyError):
                continue

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"Saved: {OUTPUT} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
