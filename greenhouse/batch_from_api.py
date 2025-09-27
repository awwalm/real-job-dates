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
    'tripadvisor': 'tripadvisor',
    'robinhood': 'robinhood',    # Growing international presence
    'twilio': 'twilio',          # Global offices, remote-friendly
    'databricks': 'databricks',  # Global presence, sponsors visas
    'snapmobileinc': 'snapmobileinc',
    'reddit': 'reddit',          # Remote-first culture
    'pinterest': 'pinterest',
}

API_URL_BASE = "https://job-boards.greenhouse.io/embed/job_app?for={}&token="
SEARCH_FILTERS = {
    'titles': {
        'engineer', 'backend', 'back end', 'fullstack',
        'full stack', 'developer', 'python', 'javascript',
        'software engineer', 'senior engineer', 'staff engineer',
        'frontend', 'front end', 'mobile', 'ios', 'android'
    },
    'locations': {
        'canada', 'ireland', 'dublin', 'toronto',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'new zealand',
        'london', 'romania', 'bucharest',
        'united kingdom', 'paris', 'france',
        'amsterdam', 'netherlands', 'melbourne',
        'worldwide', 'global', 'europe', # 'remote',
        'berlin', 'germany', 'stockholm', 'sweden'
    },
    'excluded_roles': {
        'senior', 'principal', 'manager', 'staff',
        'sr', 'snr', 'sr.', 'snr.',
        'director', 'lead',
    },
    'excluded_locations': {
        'usa', 'u.s.a.', 'u.s.a', 'u.s.', 'u.s.', 'us',
        'united states', 'united states of america',
        'india', 'china', 'korea',
    }
}


def search(query: list[str], filters: dict[str, list[str]|set[str]]):
    title_q = set(query[0].lower().split(" "))
    location_q = set(query[1].lower().split(" "))

    excluded_locations = filters['excluded_locations']
    excluded_roles = filters['excluded_roles']
    titles = filters['titles']
    locations = filters['locations']

    titles_matched = False
    locations_matched = False
    roles_exclusion_passed = True
    locations_exclusion_passed = True

    if len(excluded_locations.intersection(location_q)) > 0 and \
        len(excluded_locations.intersection(locations)) == 0:
        locations_exclusion_passed = False
        return False

    for role in excluded_roles:
        if role in title_q:
            roles_exclusion_passed = False
            return False
    
    for title in titles:
        if title in title_q:
            titles_matched = True
            break
    
    for location in locations:
        if location in location_q:
            locations_matched = True
            break
            
    return titles_matched and \
            locations_matched and \
            roles_exclusion_passed and \
            locations_exclusion_passed


failed_companies = []
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
        failed_companies.append(company)
        return []

    jobs = []
    for job in data.get("jobs", []):
        if search(query=[job['title'], job["location"]["name"]], filters=SEARCH_FILTERS):
            published_date = get_formatted_date(job["first_published"])
            updated_date = get_formatted_date(job["updated_at"])
            jobs.append({
                "Company": company.capitalize(),
                "Title": job["title"],
                "Location": job["location"]["name"],
                "URL": job["absolute_url"],
                "Token": job["id"],
                "Date Published": published_date['original'],
                "Local Date Published": published_date['local'],
                "Date Updated": updated_date['original'],
                "Local Date Updated": updated_date['local'],
            })
            
    return jobs
    

def get_formatted_date(raw_date):
    # Handle both with and without milliseconds, with timezone
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%f%z")
    except ValueError:
        parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")
    # Original timezone (usually UTC for most APIs)
    original_tz = parsed.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # Convert to local timezone
    local_time = parsed.astimezone()  # Converts to system local timezone
    local_tz = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    return {
        'original': original_tz,      # e.g., "2024-01-15 14:30:25 UTC"
        'local': local_tz             # e.g., "2024-01-15 09:30:25 EST"
    }
    # return parsed.strftime("%Y-%m-%d")


def save_to_csv(jobs, company):
    """
    Save job list to company-specific CSV file.
    """
    filename = f"from_api_gh_{company}_jobs.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Company", "Title", "Token", "Location", "URL", "Date Published", "Local Date Published", "Date Updated", "Local Date Updated"]
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
        print(f"  [{i:2d}/{len(all_jobs)}] {job['Title'][:40]:<40} ...  Published: {job['Date Published']}  Updated: {job['Date Updated']}")
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
    if len(failed_companies) > 1: print(*failed_companies, sep="\n")
    print(f"Total jobs scraped: {total_jobs}")
    print(f"CSV files created: from_api_gh_[company]_jobs.csv")
    
    if total_jobs > 0:
        print(f"\n💡 Pro tip: You can combine all CSVs with:")
        print(f"   cat from_api_gh_*_jobs.csv | grep -v '^Company,Title' | sort -t, -k6 -r > from_api_gh_all_jobs.csv")


if __name__ == "__main__":
    main()