import csv
import os
import pprint
import re
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import companies


def get_driver():
    """Initialize a Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # comment this out if you want to see browser
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    return driver


def extract_token(url: str) -> str | None:
    """
    Extract the Greenhouse job token (numeric id) from a Stripe job URL.
    Examples:
      https://stripe.com/jobs/listing/.../7165710
      https://boards.greenhouse.io/stripe/jobs/7165710
      https://stripe.com/jobs/search?gh_jid=7206401
    """
    m = re.search(r"gh_jid=(\d+)", url)
    if not m:
        m = re.search(r"/listing/[^/]+/(\d+)", url)
        if not m:
            m = re.search(r"/jobs/listing/[^/]+/(\d+)", url)
    return m.group(1) if m else None


def get_jobs_with_selenium(org: companies.OrgConfig):
    """
    Use Selenium to load the job search page and extract job details.
    """
    page = 1
    jobs = []
    while page:
        driver = get_driver()
        driver.get(org.get_job_board_url() + f"&page={page}")

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located((
            # By.CSS_SELECTOR, "a[href*='/jobs/search?gh_jid']")))
            By.XPATH, "//tr[@class='job-post']/td/a[1]")))

        # job_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='gh_jid=']")
        job_elements = driver.find_elements(By.XPATH, "//tr[@class='job-post']/td/a[1]")
        location_elements = driver.find_elements(By.XPATH, "//tr[@class='job-post']/descendant::p[2]")

        for job_elem, location_elem in zip(job_elements, location_elements):
            try:
                job_url = job_elem.get_attribute("href")
                job_title = job_elem.text.strip()
                location = location_elem.text.__str__().strip()

                jobs.append({
                    "Title": job_title,
                    "Location": location,
                    "URL": job_url
                })
            except Exception as e:
                print(f"Error parsing job element: {e}")
                continue
        
        try:
            driver.find_element(By.XPATH, 
                f"//button[@class='pagination__link' and @aria-label='Go to page {page + 1}']")
            page += 1
        except NoSuchElementException:
            print("Iterated through all pages")
            page = None
            break

    driver.quit()
    return jobs


def get_published_date(token: str, org: companies.OrgConfig):
    """
    Fetch the 'published_at' date for a given job token.
    """
    api_url = f"{org.get_api_url()}{token}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        match = re.search(r'"published_at":\s*"([^"]+)"', response.text)
        if match:
            raw_date = match.group(1)
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
                try:
                    parsed = datetime.strptime(raw_date, fmt)
                    return parsed.strftime("%Y-%m-%d")
                except ValueError:
                    pass
        return "Date not found"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching published_at for {token}: {e}")
        print(f"date not found for {api_url}, using base date 1970-01-01...")
        return "1970-01-01" #"Date not found"


def load_existing_tokens(filename):
    """Reads existing CSV and returns set of tokens to avoid duplicates."""
    tokens = set()
    if os.path.isfile(filename):
        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("URL", "")
                if "gh_jid" in url:
                    token = extract_token(url)
                    if token:
                        tokens.add(token)
    return tokens


def save_to_csv(jobs, org: companies.OrgConfig):
    """
    Dedup and save jobs to CSV.
    """
    file = org.get_csv_file()
    seen_tokens = load_existing_tokens(file)

    new_jobs = []
    for job in jobs:
        location_words = set(job["Location"].lower().replace("remote", "").split(" "))

        # Custom location filtering (mainly in Airbnb's case which does not support location filtering)
        if org.is_use_exceptions():
            org_locations: set = org.get_default_locations()
            if len(location_words.intersection(org_locations)) == 0:
                continue
        
        # Senior roles exclusion filter
        if org.is_exclude_senior_roles():
            role_words = set(job["Title"].lower().split(" "))
            excluded_roles = org.get_excluded_roles()
            if len(role_words.intersection(excluded_roles)) > 0:
                continue
        
        # Unwanted locations exclusion filter
        if org.is_exclude_unwanted_locations():
            excluded_locations = org.get_excluded_locations()
            if len(excluded_locations.intersection(location_words)) > 0 and \
                len(location_words.intersection(org_locations)) == 0:
                continue

        url = job["URL"]
        if "gh_jid" in url:
            token = extract_token(job["URL"])
            if not token:
                print(f"Warning: Could not extract token from {job['URL']}")
                continue
            if token in seen_tokens:
                continue
            job["Token"] = token
            job["Date Published"] = get_published_date(token, org)
            new_jobs.append(job)

    if not new_jobs:
        print("No new jobs to add.")
        return

    new_jobs = sorted(new_jobs, reverse=True, key=lambda d: datetime.strptime(
        d['Date Published'], "%Y-%m-%d"))

    file_exists = os.path.isfile(file)
    with open(file, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Token", "Title", "Location", "URL", "Date Published"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(file).st_size == 0:
            writer.writeheader()

        writer.writerows(new_jobs)

    print(f"Saved {len(new_jobs)} new jobs to {file}.")


def main():
    search_kw = ['Engineer']
    orgs = [
        companies.OrgConfig(name='snapmobileinc', keywords=search_kw, exclude_senior_roles=True),
        companies.OrgConfig(name='stripe', keywords=search_kw, exclude_senior_roles=True),
        companies.OrgConfig(name='lyft', keywords=search_kw, exclude_senior_roles=True),
        companies.OrgConfig(name='airbnb', keywords=search_kw, special_exceptions=True, exclude_senior_roles=True),
    ]
    for org in orgs:
        try:
            print(f"Fetching job listings for `{org}` with Selenium...")
            pprint.pprint(vars(org))
            jobs = get_jobs_with_selenium(org)
            print(f"Found {len(jobs)} jobs on search page.")
            save_to_csv(jobs, org)
        except Exception as e:
            print(f"Something went wrong:\n {e}")
    print("Done.")


if __name__ == "__main__":
    main()
