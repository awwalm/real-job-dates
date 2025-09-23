import csv
import os
import re
import requests
from datetime import datetime
import time

# --- Configuration ---
# Companies using Greenhouse with strong visa sponsorship/remote culture
COMPANIES = {
    'stripe': 'stripe',          # Global, excellent visa sponsorship
    'lyft': 'lyft',              # Your original, good sponsorship
    'gitlab': 'gitlab',          # All-remote company
    'coinbase': 'coinbase',      # Global presence, sponsors visas
    'doordash': 'doordash',      # Expanding globally, sponsors
    'robinhood': 'robinhood',    # Growing international presence
    'twilio': 'twilio',          # Global offices, remote-friendly
    'databricks': 'databricks',  # Global presence, sponsors visas
    'canva': 'canva',            # Australia-based, global remote
    'reddit': 'reddit',          # Remote-first culture
}

API_URL_BASE = "https://job-boards.greenhouse.io/embed/job_app?for={}&token="
SEARCH_FILTERS = {
    'titles': [
        'engineer', 'backend', 'back end', 'fullstack',
        'full stack', 'developer', 'python', 'javascript',
        'software engineer', 'senior engineer', 'staff engineer',
        'frontend', 'front end', 'mobile', 'ios', 'android'
    ],
    'locations': [
        'canada', 'ireland', 'dublin', 'toronto',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'new zealand',
        'london', 'romania', 'bucharest',
        'united kingdom', 'paris', 'france',
        'amsterdam', 'netherlands', 'melbourne',
        'remote', 'worldwide', 'global', 'europe',
        'berlin', 'germany', 'stockholm', 'sweden'
    ],
}


def search(query: list[str], filters: dict[str, list[str]]):
    title_q = query[0]
    location_q = query[1]
    titles_matched = False
    locations_matched = False
    
    for title in filters['titles']:
        if title.lower() in title_q.lower():
            titles_matched = True
            break
    
    for location in filters['locations']:
        if location.lower() in location_q.lower():
            locations_matched = True
            break
            
    return titles_matched and locations_matched


def get_all_jobs(company):
    """
    Fetch all jobs from the Greenhouse jobs API and filter payload locally.
    Returns a list of dicts with Title, Location, URL, and Token.
    """
    jobs_api_url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    
    try:
        response = requests.get(jobs_api_url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  ❌ Failed to fetch jobs for {company}: {e}")
        return []

    jobs = []
    for job in data.get("jobs", []):
        if search(query=[job['title'], job["location"]["name"]], filters=SEARCH_FILTERS):
            jobs.append({
                "Company": company.capitalize(),
                "Title": job["title"],
                "Location": job["location"]["name"],
                "URL": job["absolute_url"],
                "Token": job["id"]
            })
    return jobs


def get_published_date(company, token):
    """
    Fetch the 'published_at' date for a given job token.
    Returns a formatted YYYY-MM-DD string or 'Date not found'.
    """
    api_url = f"{API_URL_BASE.format(company)}{token}"
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
                try:
                    parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    # Try without timezone
                    parsed = datetime.strptime(raw_date[:19], "%Y-%m-%dT%H:%M:%S")

            return parsed.strftime("%Y-%m-%d")
        else:
            return "Date not found"
    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Error fetching date for token {token}: {e}")
        return "Date not found"


def save_to_csv(jobs, company):
    """
    Save job list to company-specific CSV file.
    """
    filename = f"greenhouse_{company}_jobs.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Company", "Title", "Token", "Location", "URL", "Date Published"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(jobs)


def process_company(company):
    """
    Process a single company: fetch jobs, get dates, save to CSV.
    """
    print(f"\n🏢 Processing {company.upper()}...")
    
    # Get all matching jobs
    all_jobs = get_all_jobs(company)
    if not all_jobs:
        print(f"  📭 No matching jobs found for {company}")
        return 0
    
    print(f"  📋 Found {len(all_jobs)} matching jobs")
    
    # Get publication dates
    final_jobs = []
    for i, job in enumerate(all_jobs, 1):
        print(f"  [{i:2d}/{len(all_jobs)}] {job['Title'][:40]:<40} ... ", end="")
        pub_date = get_published_date(company, job["Token"])
        print(pub_date)
        job["Date Published"] = pub_date
        final_jobs.append(job)
        
        # Small delay to be respectful to the API
        time.sleep(0.5)
    
    # Sort by date (most recent first)
    def sort_key(job):
        try:
            return datetime.strptime(job['Date Published'], "%Y-%m-%d")
        except:
            return datetime.min
    
    sorted_jobs = sorted(final_jobs, reverse=True, key=sort_key)
    
    # Save to CSV
    save_to_csv(sorted_jobs, company)
    
    # Stats
    dated_jobs = [j for j in sorted_jobs if j['Date Published'] != 'Date not found']
    print(f"  💾 Saved {len(sorted_jobs)} jobs to greenhouse_{company}_jobs.csv")
    print(f"  📊 {len(dated_jobs)} with dates, {len(sorted_jobs) - len(dated_jobs)} without dates")
    
    return len(sorted_jobs)


def main():
    print("🚀 GREENHOUSE BATCH SCRAPER")
    print("=" * 50)
    print(f"Targeting {len(COMPANIES)} companies with strong visa sponsorship/remote culture:")
    for company in COMPANIES.keys():
        print(f"  • {company.capitalize()}")
    
    total_jobs = 0
    successful_companies = 0
    
    for company in COMPANIES.keys():
        try:
            job_count = process_company(company)
            if job_count > 0:
                successful_companies += 1
                total_jobs += job_count
        except KeyboardInterrupt:
            print("\n\n⏹️  Scraping interrupted by user")
            break
        except Exception as e:
            print(f"  💥 Unexpected error processing {company}: {e}")
            continue
    
    print(f"\n🎯 FINAL SUMMARY")
    print("=" * 30)
    print(f"Companies processed: {successful_companies}/{len(COMPANIES)}")
    print(f"Total jobs scraped: {total_jobs}")
    print(f"CSV files created: greenhouse_[company]_jobs.csv")
    
    if total_jobs > 0:
        print(f"\n💡 Pro tip: You can combine all CSVs with:")
        print(f"   cat greenhouse_*_jobs.csv | grep -v '^Company,Title' | sort -t, -k6 -r > all_greenhouse_jobs.csv")


if __name__ == "__main__":
    main()