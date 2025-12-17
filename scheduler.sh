#!/bin/bash
# A simple task scheduler script

#activate environment
source /Users/sethhaney/.venv/job-scraper/bin/activate;

# Load environment variables
source /Users/sethhaney/.secrets

#Run the Python script
python /Users/sethhaney/Career_Documents/Koneksa-termination/job-scraper/summarize_and_email_jobs.py;

# Deactivate environment
deactivate;
