"""
STEP 1 - Load and clean the FBI Supplementary Homicide Report (SHR) master files.

Input : every .zip or .txt file you put in the  data/  folder
        (downloaded from https://cde.ucr.cjis.gov -> Documents & Downloads
         -> Master File Downloads -> Supplementary Homicide Report (SHR))
Output: data/shr_clean.csv            one tidy row per homicide incident
        figures/00_missing_matrix.png missing-data picture made with missingno

Run:  python 01_load_and_clean.py
"""
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # draw to files, do not open windows
import matplotlib.pyplot as plt
import missingno as msno
import numpy as np
import pandas as pd

DATA = Path("data")
FIG = Path("figures")
FIG.mkdir(exist_ok=True)

# --------------------------------------------------------------------------
# 1. RECORD LAYOUT
# The master file is "fixed width": no commas, every field sits at a fixed
# character position in a 268-character line. Positions below are
# (first, last), counted from 1, as in the FBI record description that
# comes with the download. We only read the header + first victim/offender.
# --------------------------------------------------------------------------
RECORD_LENGTH = 268
LAYOUT = {
    "state_code":      (2, 3),
    "ori":             (4, 10),
    "year2":           (14, 15),
    "population":      (16, 24),
    "agency":          (32, 55),
    "month":           (62, 63),
    "homicide_type":   (71, 71),
    "situation":       (75, 75),
    "victim_age":      (76, 77),
    "victim_sex":      (78, 78),
    "victim_race":     (79, 79),
    "victim_ethnic":   (80, 80),
    "offender_age":    (81, 82),
    "offender_sex":    (83, 83),
    "offender_race":   (84, 84),
    "offender_ethnic": (85, 85),
    "weapon":          (86, 87),
    "relationship":    (88, 89),
    "circumstance":    (90, 91),
    "extra_victims":   (93, 95),
    "extra_offenders": (96, 98),
}

# --------------------------------------------------------------------------
# 2. CODE BOOKS - turn FBI codes into readable labels
# --------------------------------------------------------------------------
STATE = {  # FBI numeric state code -> postal abbreviation
    "01": "AL", "02": "AZ", "03": "AR", "04": "CA", "05": "CO", "06": "CT",
    "07": "DE", "08": "DC", "09": "FL", "10": "GA", "11": "ID", "12": "IL",
    "13": "IN", "14": "IA", "15": "KS", "16": "KY", "17": "LA", "18": "ME",
    "19": "MD", "20": "MA", "21": "MI", "22": "MN", "23": "MS", "24": "MO",
    "25": "MT", "26": "NE", "27": "NV", "28": "NH", "29": "NJ", "30": "NM",
    "31": "NY", "32": "NC", "33": "ND", "34": "OH", "35": "OK", "36": "OR",
    "37": "PA", "38": "RI", "39": "SC", "40": "SD", "41": "TN", "42": "TX",
    "43": "UT", "44": "VT", "45": "VA", "46": "WA", "47": "WV", "48": "WI",
    "49": "WY", "50": "AK", "51": "HI",
}
REGION = {}
for _region, _states in {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest":   "IL IN MI OH WI IA KS MN MO NE ND SD",
    "South":     "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
    "West":      "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}.items():
    for _s in _states.split():
        REGION[_s] = _region

SEX = {"M": "Male", "F": "Female"}                       # U -> missing
RACE = {"W": "White", "B": "Black", "I": "American Indian",
        "A": "Asian", "P": "Pacific Islander"}           # U -> missing
ETHNIC = {"H": "Hispanic", "N": "Not Hispanic"}          # U -> missing

WEAPON_GROUP = {
    "11": "Other firearm", "12": "Handgun", "13": "Other firearm",
    "14": "Other firearm", "15": "Other firearm",
    "20": "Knife", "30": "Blunt object", "40": "Hands or feet",
    "50": "Other", "55": "Other", "60": "Other", "65": "Other",
    "70": "Other", "75": "Other", "80": "Other", "85": "Other", "90": "Other",
}
FIREARM_CODES = {"11", "12", "13", "14", "15"}

REL_GROUP = {}
for _group, _codes in {
    "Intimate partner": "HU WI CH CW BF GF XH XW HO",
    "Family":           "MO FA SO DA BR SI IL SF SM SS SD OF",
    "Acquaintance":     "NE AQ EE ER FR OK",
    "Stranger":         "ST",
}.items():                                               # UN -> missing
    for _c in _codes.split():
        REL_GROUP[_c] = _group

CIRC_GROUP = {}
for _group, _codes in {
    "Felony-related":   "02 03 05 06 07 09 10 17 18 19 26 70",
    "Argument / brawl": "40 42 43 44 45",
    "Gang-related":     "46 47",
    "Other":            "32 41 48 49 60 80 81",
}.items():                                               # 99 -> missing
    for _c in _codes.split():
        CIRC_GROUP[_c] = _group


# --------------------------------------------------------------------------
# 3. READ THE RAW FILES
# --------------------------------------------------------------------------
def split_records(raw_bytes):
    """Turn the bytes of one master file into a list of text records."""
    text = raw_bytes.decode("latin-1")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # some master files have no line breaks at all: cut every 268 characters
    if len(lines) == 1 and len(lines[0]) > 2 * RECORD_LENGTH:
        one = lines[0]
        lines = [one[i:i + RECORD_LENGTH] for i in range(0, len(one), RECORD_LENGTH)]
    return [ln for ln in lines if len(ln) >= 98]


def read_all_files():
    records = []
    for path in sorted(DATA.iterdir()):
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                for member in z.namelist():
                    if member.lower().endswith((".pdf", ".doc", ".docx", ".xlsx", ".xls", "/")):
                        continue                          # skip documentation
                    recs = split_records(z.read(member))
                    print(f"{path.name} -> {member}: {len(recs):,} records")
                    records += recs
        elif path.suffix.lower() in (".txt", ".dat", ""):
            if path.is_file():
                recs = split_records(path.read_bytes())
                print(f"{path.name}: {len(recs):,} records")
                records += recs
    if not records:
        raise SystemExit("No SHR records found. Put the downloaded .zip files in the data/ folder.")
    return records


def parse(records):
    """Cut every record into columns using LAYOUT."""
    cols = {name: [r[a - 1:b].strip() for r in records] for name, (a, b) in LAYOUT.items()}
    return pd.DataFrame(cols)


def clean_age(col):
    """NB = newborn, BB = baby under 1 year -> 0;  00 = unknown -> missing."""
    age = pd.to_numeric(col, errors="coerce")
    age[col == "00"] = np.nan
    age[col.isin(["NB", "BB"])] = 0
    return age


# --------------------------------------------------------------------------
# 4. CLEAN
# --------------------------------------------------------------------------
def clean(raw):
    df = pd.DataFrame()
    yy = pd.to_numeric(raw["year2"], errors="coerce")
    df["year"] = np.where(yy >= 60, 1900 + yy, 2000 + yy)
    df["month"] = pd.to_numeric(raw["month"], errors="coerce")
    df["state"] = raw["state_code"].map(STATE)
    df["region"] = df["state"].map(REGION)
    df["agency"] = raw["agency"]
    df["homicide_type"] = raw["homicide_type"]
    df["situation"] = raw["situation"]

    df["victim_age"] = clean_age(raw["victim_age"])
    df["victim_sex"] = raw["victim_sex"].map(SEX)
    df["victim_race"] = raw["victim_race"].map(RACE)
    df["victim_ethnic"] = raw["victim_ethnic"].map(ETHNIC)
    df["offender_age"] = clean_age(raw["offender_age"])
    df["offender_sex"] = raw["offender_sex"].map(SEX)
    df["offender_race"] = raw["offender_race"].map(RACE)

    df["weapon_code"] = raw["weapon"]
    df["weapon_group"] = raw["weapon"].map(WEAPON_GROUP)
    df["firearm"] = raw["weapon"].isin(FIREARM_CODES)
    df["rel_code"] = raw["relationship"]
    df["rel_group"] = raw["relationship"].map(REL_GROUP)
    df["circ_code"] = raw["circumstance"]
    df["circ_group"] = raw["circumstance"].map(CIRC_GROUP)

    before = len(df)
    # keep murder / non-negligent manslaughter only (A); drop negligent (B)
    df = df[df["homicide_type"] == "A"]
    # drop rows outside the 50 states + DC (territories, bad codes)
    df = df.dropna(subset=["state", "year"])
    df["year"] = df["year"].astype(int)
    print(f"\nRows read: {before:,}  ->  rows kept after cleaning: {len(df):,}")
    return df.reset_index(drop=True)


def sanity_check(raw):
    """If these numbers are low, the column positions do not match your file."""
    checks = {
        "state code recognised": raw["state_code"].isin(STATE.keys()).mean(),
        "victim sex is M/F/U":   raw["victim_sex"].isin(["M", "F", "U"]).mean(),
        "weapon code recognised": raw["weapon"].isin(WEAPON_GROUP.keys()).mean(),
        "homicide type is A/B":  raw["homicide_type"].isin(["A", "B"]).mean(),
    }
    print("\nLayout sanity check (should all be close to 100%):")
    for label, share in checks.items():
        print(f"  {label:<24} {share:6.1%}")
    if min(checks.values()) < 0.90:
        print("  WARNING: the layout looks wrong for this file. Compare LAYOUT with "
              "the record description document inside the downloaded zip.")


if __name__ == "__main__":
    raw = parse(read_all_files())
    sanity_check(raw)
    df = clean(raw)

    print("\nIncidents per year:")
    print(df["year"].value_counts().sort_index().to_string())
    print("\nShare of missing values per column (%):")
    print(df.isna().mean().mul(100).round(1).to_string())

    # missingno: white gaps = missing values
    cols = ["victim_age", "victim_sex", "victim_race", "victim_ethnic", "offender_age",
            "offender_sex", "offender_race", "weapon_group", "rel_group", "circ_group"]
    sample = df[cols].sample(min(2000, len(df)), random_state=1)
    msno.matrix(sample, figsize=(12, 6), fontsize=10, sparkline=False)
    plt.title("Missing data in the cleaned SHR sample (missingno)", fontsize=14)
    plt.savefig(FIG / "00_missing_matrix.png", dpi=150, bbox_inches="tight")
    plt.close("all")

    df.to_csv(DATA / "shr_clean.csv", index=False)
    print("\nSaved data/shr_clean.csv and figures/00_missing_matrix.png")
