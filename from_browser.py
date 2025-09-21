import csv
import os
import re
import time
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# --- Configuration ---
CSV_FILE = "stripe_jobs_from_browser.csv"
INITIAL_JOBS_URL = (
    "https://stripe.com/jobs/search?"
    "query=Engineer"  # or query=Developer  or whatever you want
    "&remote_locations=Asia+Pacific--Malaysia+Remote"  # and any location you want too
    "&office_locations=Asia+Pacific--Melbourne"
    "&office_locations=Asia+Pacific--Singapore"
    "&office_locations=Asia+Pacific--Sydney"
    "&office_locations=Europe--Amsterdam"
    "&office_locations=Europe--Bucharest"
    "&office_locations=Europe--Dublin"
    "&office_locations=Europe--London"
    "&office_locations=Europe--Paris"
    "&office_locations=North+America--Toronto"
)
API_URL_BASE = "https://job-boards.greenhouse.io/embed/job_app?for=stripe&token="


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
    """
    m = re.search(r"/jobs/listing/[^/]+/(\d+)", url)
    if not m:
        m = re.search(r"/listing/[^/]+/(\d+)", url)
    return m.group(1) if m else None


def get_jobs_with_selenium(url):
    """
    Use Selenium to load the job search page and extract job details.
    """
    driver = get_driver()
    driver.get(url)

    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/jobs/listing']")))

    job_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/listing']")
    location_elements = driver.find_elements(By.XPATH, "//a[contains(@href, 'jobs/listing')]/parent::td/parent::*/td[3]")

    jobs = []
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

    driver.quit()
    return jobs


def get_published_date(token):
    """
    Fetch the 'published_at' date for a given job token.
    """
    api_url = f"{API_URL_BASE}{token}"
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
        return "Date not found"


def load_existing_tokens(filename):
    """Reads existing CSV and returns set of tokens to avoid duplicates."""
    tokens = set()
    if os.path.isfile(filename):
        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("URL", "")
                if "jobs/listing" in url:
                    token = extract_token(url)
                    if token:
                        tokens.add(token)
    return tokens


def save_to_csv(jobs):
    """
    Dedup and save jobs to CSV.
    """
    seen_tokens = load_existing_tokens(CSV_FILE)

    new_jobs = []
    for job in jobs:
        url = job["URL"]
        if "jobs/listing" in url:
            token = extract_token(job["URL"])
            if not token:
                print(f"Warning: Could not extract token from {job['URL']}")
                continue
            if token in seen_tokens:
                continue
            job["Token"] = token
            job["Date Published"] = get_published_date(token)
            new_jobs.append(job)

    if not new_jobs:
        print("No new jobs to add.")
        return

    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Token", "Title", "Location", "URL", "Date Published"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(CSV_FILE).st_size == 0:
            writer.writeheader()

        writer.writerows(new_jobs)

    print(f"Saved {len(new_jobs)} new jobs to {CSV_FILE}.")


def main():
    print("Fetching job listings with Selenium...")
    jobs = get_jobs_with_selenium(INITIAL_JOBS_URL)
    print(f"Found {len(jobs)} jobs on search page.")
    save_to_csv(jobs)
    print("Done.")


if __name__ == "__main__":
    main()
