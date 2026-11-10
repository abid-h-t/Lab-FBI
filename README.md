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
