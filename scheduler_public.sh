#!/bin/bash
# A simple task scheduler script
# NOTE: This is a public version that will not run
# Please update this to match the directory structure
# on your computer

#activate environment
source /path/to/venv/bin/activate

# Load environment variables including app password for your email
source /path/to/app_password_file

#Run the Python script
python /path/to/repo/job-scraper/summarize_and_email_jobs.py;

# Deactivate environment
deactivate;
