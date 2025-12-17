'''
summarize_and_email_jobs.py - 
Summarize new job listings and emails a digest of them.
'''

#Import necessary libraries
import pandas as pd
import os
import smtplib

from email.message import EmailMessage
from job_scraper import JobScraper, DEFAULT_LISTINGS_FN


#GLOBALS
DEFAULT_SENDER_EMAIL = 'sethdhaney@gmail.com'
DEFAULT_RECIPIENT_EMAIL = 'sethdhaney@gmail.com'


#Main Class
class JobDigestEmailer():
    '''
    Summarizes new job listings and emails a digest.
    '''
    def __init__(self, recipient_email, sender_email, sender_password, previous_jobs_file=DEFAULT_LISTINGS_FN):
        '''
        Initializes the emailer.
        recipient_email: str
            email to send the digest to
        sender_email: str
            email to send the digest from
        sender_password: str
            password for the sender email
        previous_jobs_file: str
            file path to previous jobs csv
        '''
        self.recipient_email = recipient_email
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.previous_jobs_file = previous_jobs_file
        return
    
    def get_previous_jobs(self):
        '''
        Loads previous jobs from file.
        '''
        try:
            previous_jobs_df = pd.read_csv(self.previous_jobs_file)
            print(f"Loaded {len(previous_jobs_df)} previous jobs from {self.previous_jobs_file}.")
        except FileNotFoundError:
            previous_jobs_df = pd.DataFrame(columns=['title', 'company', 'state', 'city', 'url', 'score'])
            print(f"No previous jobs file found. Starting fresh.")
        return previous_jobs_df
    
    def save_new_jobs(self, new_jobs_df):
        '''
        Saves new jobs to file.
        '''
        new_jobs_df.to_csv(self.previous_jobs_file, index=False)
        print(f"Saved {len(new_jobs_df)} new jobs to {self.previous_jobs_file}.")
        return
    
    def create_email_content(self, new_jobs_df):
        '''
        Creates email content summarizing new jobs.
        '''
        #filter to only jobs with score > 0
        new_jobs_df = new_jobs_df.query('score > 0').reset_index(drop=True)

        #Catch no new jobs
        if len(new_jobs_df) == 0:
            return None
        
        #Create digest content
        subject = f"Found {len(new_jobs_df)} new job listings."
        content = subject + f"\n\nMax score: {new_jobs_df['score'].max()}\n"
        content += f"Mean score: {new_jobs_df['score'].mean():.2f}\n"
        content += f"------------------------\n\n"
        content += "New Job Listings:\n"

        MAX_ROWS = 10
        for idx, row in new_jobs_df.iterrows():
            content += f"Title: {row['title']}\nCompany: {row['company']}\n"\
                f"State: {row['state']}\nCity: {row['city']}\n"\
                f"URL: {row['url']}\nScore: {row['score']}\n\n"
            if idx + 1 >= MAX_ROWS:
                content += f"...and {len(new_jobs_df) - MAX_ROWS} more listings.\n"
                break
        return subject, content
    
    def send_job_digest(self):
        '''
        Main function to send job digest email.
        '''
        
        previous_jobs = self.get_previous_jobs()
        scraper = JobScraper(previous_jobs_df=previous_jobs)
        new_jobs_df, exceptions_df = scraper.scrape()
        subject, email_content = self.create_email_content(new_jobs_df)

        if email_content is None:
            print("No new jobs found. No email sent.")
            return

        send_email(
            subject=subject,
            body=email_content,
            to_email=self.recipient_email,
            from_email=self.sender_email,
            from_password=self.sender_password
        )
        
        if previous_jobs is not None:
            jobs_df = pd.concat([previous_jobs, new_jobs_df], ignore_index=True)
        else:
            jobs_df = new_jobs_df
        if not jobs_df.empty:
            self.save_new_jobs(jobs_df)
        
        return

def send_email(subject, body, to_email, from_email, from_password):

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, from_password)
        server.send_message(msg)


#Main entry point
if __name__=='__main__':
    emailer = JobDigestEmailer(
        recipient_email=DEFAULT_RECIPIENT_EMAIL,
        sender_email=DEFAULT_SENDER_EMAIL,
        sender_password=os.getenv('EMAIL_PASSWORD', 'PASSWORD_NOT_SET')
    )
    emailer.send_job_digest()
