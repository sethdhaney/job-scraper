'''
main.py - Main file for job scraper
'''

## Imports
import requests
import pandas as pd
import json
import textwrap
import time
import os

from tqdm import tqdm
from bs4 import BeautifulSoup
from os.path import dirname, abspath, join


## GLOBALS
CUR_DIR = dirname(abspath(__file__))
DEFAULT_LISTINGS_FN = join(CUR_DIR, 'job_listings.csv')
DEFAULT_EXCEPTIONS_FN = join(CUR_DIR, 'job_exceptions.csv')
DEFAULT_URL = "https://jobs.biospace.com/searchjobs/?Keywords=Senior+Data+Scientist"
KEYWORDS = [
    "digital health",
    "wearable",
    "biomarker",
    "time series",
    "clinical",
    "machine learning",
    "deep learning",
    "signal processing",
    "Parkinson's",
    "neurology",
    "voice",
    "accelerometer"
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"
}

## Main Code
class JobScraper():
    '''
    Parses jobs given a job board url. 
    '''
    def __init__(self, board_url=DEFAULT_URL, previous_jobs_df=None):
        '''
        initializes the scraper
        board_url: str
            url of the job board to scrape
        previous_jobs_df: pd.DataFrame
            dataframe of previous jobs to filter out
        '''
        self.board_url = board_url
        self.previous_jobs_df = previous_jobs_df
        return
    
    def scrape(self, *args, **kwargs):
        '''
        main function
        '''
        #jobs list
        #TODO: handle pagination
        print(f"Fetching job board page...")
        job_urls = self._scrape_all_pages(self.board_url)

        #filter previous jobs
        if self.previous_jobs_df is not None:
            job_urls = [j for j in job_urls if j not in self.previous_jobs_df['url'].tolist()]
            print(f"Filtered to {len(job_urls)} new jobs after removing previous listings.")

        #parse each job
        new_job_df, exceptions_df = self._extract_job_df(job_urls)
        return new_job_df, exceptions_df
    
    def _scrape_all_pages(self, base_url):
        '''
        Scrapes all pages of the job board.
        base_url: str
            url of the job board to scrape
        Returns:
            list of job urls
        '''
        page = 1
        job_urls = []

        while True:
            url = f"{base_url}&Page={page}"
            print(f"Scraping page {page}")

            soup = fetch_page(url)
            jobs = self._extract_job_urls(soup)

            if not jobs:
                break

            job_urls.extend(jobs)
            page += 1
        job_urls = list(set(job_urls))  # Remove duplicates
        return job_urls
    
    def _extract_job_urls(self, soup):
        '''
        Extracts job listings from the job board soup.
        '''
        links = soup.find_all("a", href=True)

        job_urls = []
        print(f"Fetching job urls...")
        for l in tqdm(links):
            info = self.get_jobid_title(l)
            if info is not None:
                job_url = self._get_job_url_from_job_info(info)
                job_urls.append(job_url)
                
        return job_urls
    
    def get_jobid_title(self, link):
        link_str = link.get('href')
        if 'job/' in link_str:
            splits = link_str.split('job/')[1].split('/')
            jobid, title = splits[:2]
            return {'jobid': jobid, 'title': title}
        return None
    
    def _get_job_url_from_job_info(self, job_info):
        return f'https://jobs.biospace.com/job/{job_info["jobid"]}/{job_info["title"]}/'
    
    def _extract_job_df(self, job_urls):
        '''
        Extracts job details for each job URL.
        job_urls: list of str
            list of job URLs to parse
        Returns:    
            pd.DataFrame of job details
            pd.DataFrame of exceptions
        '''
        jobs_data, exceptions = [], []
        print(f"Fetching job dataframe...")
        for url in tqdm(job_urls):
            try: 
                job_data = self.get_job_data(url)
            except Exception as e:
                exceptions.append({'url': url, 'Exception': str(e)})
                print(f"Exception for {url}: {e}")

            job_data['url'] = url
            jobs_data.append(job_data)

        if len(jobs_data) == 0:
            return pd.DataFrame(), pd.DataFrame()
        jobs_df = pd.DataFrame(jobs_data)\
            .sort_values('score', ascending=False)\
            .drop_duplicates(subset='url')\
            .reset_index(drop=True)
        
        exceptions_df = pd.DataFrame(exceptions)
        return jobs_df, exceptions_df

    def get_job_data(self, job_url):
        ''' parses a single job url
        '''
        s = fetch_page(job_url)
        job_data = self._get_job_dict_from_soup(s)
        job_data = self._parse_job_data(job_data)

        return job_data
    
    def _get_job_dict_from_soup(self, s):
        '''what it says
        '''
        script_tag = s.find("script", type="application/ld+json")
        json_text = script_tag.get_text()
        job_data = json.loads(json_text)
        return job_data
    
    def _parse_job_data(self, job_data):
        '''what it says
        '''
        useful_fields = [
            'title', 'description', 'datePosted', 
            'validThrough', 'hiringOrganization', 'jobLocation',
            'employmentType'
            ]
        output_fields = [
            'title', 'company', 'location', 'state', 'city',
            'score', 'matched_keywords', 
            'description', 'datePosted', 'validThrough'  
        ]
        job_data = {field: job_data.get(field, None) for field in useful_fields}

        job_data['company'] = job_data['hiringOrganization'].get('name', None) if job_data['hiringOrganization'] else None
        if len(job_data['jobLocation'])>0:
            jl = job_data['jobLocation'][0]
            job_data['location'] = jl.get('address', None) if jl else None
            job_data['state'] = job_data['location'].get('addressRegion', None) if job_data['location'] else None
            job_data['city'] = job_data['location'].get('addressLocality', None) if job_data['location'] else None
        job_data['description'] = html_job_to_text(job_data['description'])
        matched_kws, score = self._score_description(job_data['description'])
        job_data['score'] = score
        job_data['matched_keywords'] = matched_kws

        return {f: job_data[f] for f in output_fields}
    
    def _score_description(self, text):
        '''
        Scores each job based on keyword matches.
        '''
        
        text = text.lower()
        matched = [kw for kw in KEYWORDS if kw in text]
        return matched, len(matched)


def fetch_page(url, delay=1.0):
    '''Gets a web page and returns processed soup'''
    time.sleep(delay)  # <-- delay BEFORE the request
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def html_job_to_text(html: str, wrap_width: int = 88) -> str:
    '''Creates a human readable version of an html job description and 
    removes tags like <p> or <li> etc.
    '''
    soup = BeautifulSoup(html, "html.parser")

    lines = []

    for element in soup.body or soup.children:
        if getattr(element, "name", None) in ["p", "div"]:
            text = element.get_text(" ", strip=True)
            if text:
                lines.append(text)
                lines.append("")

        elif element.name == "ul":
            for li in element.find_all("li", recursive=False):
                bullet = li.get_text(" ", strip=True)
                lines.append(f"- {bullet}")
            lines.append("")

    # Cleanup
    text = "\n".join(lines)
    text = text.replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.splitlines())

    # Optional wrapping for readability
    wrapped = []
    for block in text.split("\n\n"):
        wrapped.append(
            textwrap.fill(block, width=wrap_width, replace_whitespace=False)
        )

    return "\n\n".join(wrapped).strip()


## Entrypoint
if __name__=='__main__':
    if os.path.exists(DEFAULT_LISTINGS_FN):
        previous_jobs_df = pd.read_csv(DEFAULT_LISTINGS_FN)
        previous_exceptions_df = pd.read_csv(DEFAULT_EXCEPTIONS_FN)
    else:
        previous_jobs_df = None

    cls = JobScraper(board_url=DEFAULT_URL, previous_jobs_df=previous_jobs_df)
    new_jobs_df, new_exceptions_df = cls.scrape()
    
    #combine with previous jobs
    if previous_jobs_df is not None:
        jobs_df = pd.concat([previous_jobs_df, new_jobs_df], ignore_index=True)
        exceptions_df = pd.concat([previous_exceptions_df, new_exceptions_df], ignore_index=True)
    else:
        jobs_df = new_jobs_df
        exceptions_df = new_exceptions_df

    jobs_df.to_csv(DEFAULT_LISTINGS_FN, index=False)
    exceptions_df.to_csv(DEFAULT_EXCEPTIONS_FN, index=False)
