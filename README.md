# Lab-FBI

# Step 1 — Download the data
Open https://cde.ucr.cjis.gov and click Documents & Downloads (top right).
Scroll to Master File Downloads → Annual Master Files.
In the Master File dropdown choose Supplementary Homicide Report (SHR).
In the Year dropdown choose 2024 and click DOWNLOAD.
Repeat for each year back to 2015, so you have 10 zip files. Hypotheses 1 and 2 are about change over time, so they need several years.
Move all the zips into the data folder. Do not unzip them; the script reads zips directly.

# Step 2 — Create the virtual environment

Run these one at a time in PowerShell, inside the lab folder:

python -m venv csc_lab_env
csc_lab_env\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
If activation is blocked: run Set-ExecutionPolicy -Scope Process RemoteSigned first, then activate again.
If an install fails: your Python is 3.15, which is very new, and some libraries may not support it yet. Install Python 3.13 and create the environment with py -3.13 -m venv csc_lab_env instead.
Extra packages: requirements.txt adds kaleido and vl-convert-python (PNG export for plotly and altair) and python-pptx (for the deck) to the lab’s list.

# Step 3 — Load and clean the data
python 01_load_and_clean.py

01_load_and_clean.py does this, in order:

Reads the fixed-width file. There are no commas; each field sits at fixed character positions in a 268-character line, so the script cuts each line by position. <br>
Decodes FBI codes. For example weapon 12 becomes “Handgun”, relationship WI becomes “Intimate partner”, and state 42 becomes “TX” in the “South” region. <br>
Handles missing and invalid values. Unknown codes (U, 00, UN, 99) become missing values, and newborn or baby age codes become age 0. <br>
Filters rows. It keeps murder and non-negligent manslaughter only, and drops territories. <br>
Draws the missing-data chart with missingno, for your setup slide. <br>
Saves data/shr_clean.csv.

Each row is one incident, described by its first victim and first offender. Mention this as a limitation in your conclusion slide.

# Step 4 — Test the five hypotheses
python 02_hypotheses.py

02_hypotheses.py saves 15 charts into figures/ and prints the numbers behind each one.

#	Hypothesis =Chart 1	= Chart 2	= Chart 3
H1	The 2020 rise was a firearm rise, in every region	= matplotlib indexed lines	= seaborn heatmap	= plotly lines <br>
H2	Women are killed mostly by partners and family, men by acquaintances and strangers, and the gap has not narrowed	= seaborn grouped bars	= altair stacked facets	= plotnine small multiples <br>
H3	The weapon depends on the relationship and the victim’s age	= seaborn heatmap	= plotly sunburst	= bokeh stacked bars <br>
H4	Firearm share varies by state and is highest in the South	= plotly map	= folium map	= seaborn box and dots <br>
H5	Arguments and gang killings are between age peers; felony killings have younger offenders	= matplotlib hexbin	= seaborn violin	= altair dumbbell

