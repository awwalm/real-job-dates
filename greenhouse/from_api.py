import csv
import os
import re
import requests
from datetime import datetime

# --- Configuration ---
COMPANIES = {'lyft': 'lyft', 'stripe': 'stripe'}
ORG = COMPANIES.get(input(f"Enter a company name (must be one of {list(COMPANIES.keys())}): ").lower())
if not ORG: ORG = 'stripe'
CSV_FILE = f"{ORG}_jobs_from_api.csv"
JOBS_API_URL = f"https://boards-api.greenhouse.io/v1/boards/{ORG}/jobs"
API_URL_BASE = f"https://job-boards.greenhouse.io/embed/job_app?for={ORG}&token="
SEARCH_FILTERS = {
    'titles': [
        'engineer', 'backend', 'back end', 'fullstack',
        'full stack', 'developer', 'python', 'javascript'
    ],
    'locations': [
        'canada', 'ireland', 'dublin', 'toronto',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'new zealand',
        'london', 'romania', 'bucharest',
        'united kingdom', 'paris', 'france',
        'amsterdam', 'netherlands', 'melbourne'
    ],
}



def search(query: list[str], filters: dict[str, list[str]]):
    title_q = query[0]
    location_q = query[1]
    titles_matched = False
    locations_matched = False
    for title, location in zip(filters['titles'], filters['locations']):
        if not titles_matched and title.lower() in title_q.lower():
            titles_matched = True
        if not locations_matched and location.lower() in location_q.lower():
            locations_matched = True
        if locations_matched and titles_matched:
            return True
    return titles_matched and locations_matched


def get_all_jobs():
    """
    Fetch all jobs from the Greenhouse jobs API and filter payload locally.
    Returns a list of dicts with Title, Location, URL, and Token.
    """
    response = requests.get(JOBS_API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data.get("jobs", []):
        if search(query=[job['title'], job["location"]["name"]], filters=SEARCH_FILTERS):
            jobs.append({
                "Title": job["title"],
                "Location": job["location"]["name"],
                "URL": job["absolute_url"],
                "Token": job["id"]
            })
    return jobs


def get_published_date(token):
    """
    Fetch the 'published_at' date for a given job token.
    Returns a formatted YYYY-MM-DD string or 'Date not found'.
    """
    api_url = f"{API_URL_BASE}{token}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        match = re.search(r'"published_at":\s*"([^"]+)"', response.text)
        if match:
            raw_date = match.group(1)

            # Handle both with and without milliseconds, with timezone
            try:
                parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            except ValueError:
                parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")

            return parsed.strftime("%Y-%m-%d")
        else:
            return "Date not found"
    except requests.exceptions.RequestException as e:
        print(f"Error fetching published_at for {token}: {e}")
        return "Date not found"


def save_to_csv(jobs, filename=CSV_FILE):
    """
    Save job list to CSV file.
    """
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Title", "Token", "Location", "URL", "Date Published"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(jobs)


def main():
    print("Fetching jobs list...")
    all_jobs = get_all_jobs()
    print(f"Found {len(all_jobs)} jobs.")

    final_jobs = []
    for job in all_jobs:
        print(f"Fetching publish date for '{job['Title']}'...")
        pub_date = get_published_date(job["Token"])
        print(pub_date)
        job["Date Published"] = pub_date
        final_jobs.append(job)

    print(f"Writing {len(final_jobs)} jobs to {CSV_FILE}...")
    # save_to_csv(final_jobs)
    save_to_csv(sorted(final_jobs, reverse=True, key=lambda d: datetime.strptime(
        d['Date Published'], "%Y-%m-%d"))
    )
    print("Done.")


if __name__ == "__main__":
    main()
