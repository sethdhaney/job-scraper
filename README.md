# Job Scraper
This folder contains the code to run a web scraper to grab jobs from a job board. 

As many of the job boards are particularly designed to defend against automated scraping,
this one targets [BioSpace](https://jobs.biospace.com/). It uses many assumptions about the structure of web pages to do it's job and is not likely to work on other websites.



# Usage

## Enviornment 
Before doing anything create a new python environment and install the dependencies with `pip install -r requirements.txt`. 

## Scraper
The main class to perform the scraping is in `job_scraper.py`. This can be run standalone with `python job_scraper.py`. This should produce `job_listings.csv` and `exceptions.csv`. These are a table of jobs (each is scored by the number of matched keywords) and a list of exceptions (i.e., http errors during scraping).



## Emailer
The main class to digest the job listing and send an automated email to me is given in `summarize_and_email_jobs.py`. This can also be run from the command line `python summarize_and_email_jobs.py`. 

## Scheduler
The script `scheduler.sh`, which actually doesn't schedule anything, activates the virtual environment and runs the emailer. 

I have scheduled `scheduler.sh` to run by editing the `crontab` and adding 

`0 8 * * * /path/to/repo/job-scraper/  scheduler.sh`
