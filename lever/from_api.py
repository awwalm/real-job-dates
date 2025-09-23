import csv
import os
import re
import requests
from datetime import datetime
import json

# --- Configuration ---
# Some companies using Lever: Netflix, Spotify, Airbnb, Robinhood, etc.
COMPANIES = {
    'netflix': 'netflix', 
    'spotify': 'spotify',
    'airbnb': 'airbnb',
    'robinhood': 'robinhood',
    'figma': 'figma',
    'notion': 'notion',
    'discord': 'discord'
}

ORG = COMPANIES.get(input(f"Enter a company name (must be one of {list(COMPANIES.keys())}): ").lower())
if not ORG: 
    ORG = 'netflix'

CSV_FILE = f"lever_{ORG}_jobs_from_lever.csv"

# Lever API endpoints
JOBS_API_URL = f"https://api.lever.co/v0/postings/{ORG}"
# Alternative postings endpoint (some companies use this)
JOBS_API_URL_ALT = f"https://api.lever.co/v0/postings/{ORG}?mode=json"
# Job detail endpoint for individual postings
JOB_DETAIL_URL = f"https://jobs.lever.co/{ORG}/"

SEARCH_FILTERS = {
    'titles': [
        'engineer', 'backend', 'back end', 'fullstack',
        'full stack', 'developer', 'python', 'javascript',
        'software engineer', 'senior engineer', 'staff engineer'
    ],
    'locations': [
        'canada', 'ireland', 'dublin', 'toronto',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'new zealand',
        'london', 'romania', 'bucharest',
        'united kingdom', 'paris', 'france',
        'amsterdam', 'netherlands', 'melbourne',
        'remote', 'worldwide', 'global'
    ],
}


def search(query: list[str], filters: dict[str, list[str]]):
    """
    Check if job title and location match our filter criteria.
    """
    title_q = query[0] if query[0] else ""
    location_q = query[1] if query[1] else ""
    
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


def get_all_jobs():
    """
    Fetch all jobs from the Lever jobs API and filter payload locally.
    Returns a list of dicts with Title, Location, URL, and ID.
    """
    jobs = []
    
    # Try primary API endpoint first
    try:
        print(f"Trying primary API: {JOBS_API_URL}")
        response = requests.get(JOBS_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"Successfully fetched {len(data)} jobs from primary endpoint")
    except Exception as e:
        print(f"Primary endpoint failed: {e}")
        # Try alternative endpoint
        try:
            print(f"Trying alternative API: {JOBS_API_URL_ALT}")
            response = requests.get(JOBS_API_URL_ALT, timeout=10)
            response.raise_for_status()
            data = response.json()
            print(f"Successfully fetched {len(data)} jobs from alternative endpoint")
        except Exception as e2:
            print(f"Alternative endpoint also failed: {e2}")
            return []

    for job in data:
        # Lever API structure is different from Greenhouse
        title = job.get("text", "")
        
        # Location handling - Lever can have multiple locations
        locations = job.get("categories", {}).get("location", [])
        if isinstance(locations, str):
            location_str = locations
        elif isinstance(locations, list) and locations:
            location_str = ", ".join(locations)
        else:
            location_str = "Location not specified"
        
        # Check if job matches our filters
        if search(query=[title, location_str], filters=SEARCH_FILTERS):
            jobs.append({
                "Title": title,
                "Location": location_str,
                "URL": job.get("hostedUrl", ""),
                "ID": job.get("id", ""),
                "Team": job.get("categories", {}).get("team", [""])[0] if job.get("categories", {}).get("team") else ""
            })
    
    return jobs


def get_published_date(job_id, job_url):
    """
    Fetch the 'createdAt' or publication date for a given job.
    Lever is tricky - we'll try multiple approaches.
    Returns a formatted YYYY-MM-DD string or 'Date not found'.
    """
    
    # Method 1: Try to get it from the individual job API endpoint
    try:
        individual_api_url = f"https://api.lever.co/v0/postings/{ORG}/{job_id}"
        response = requests.get(individual_api_url, timeout=10)
        response.raise_for_status()
        job_data = response.json()
        
        # Look for createdAt field
        if "createdAt" in job_data:
            created_at = job_data["createdAt"]
            # Lever timestamps are usually in milliseconds
            if isinstance(created_at, int):
                if created_at > 1e12:  # Milliseconds
                    created_at = created_at / 1000
                parsed = datetime.fromtimestamp(created_at)
                return parsed.strftime("%Y-%m-%d")
            elif isinstance(created_at, str):
                # Try to parse ISO format
                try:
                    parsed = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    return parsed.strftime("%Y-%m-%d")
                except:
                    pass
        
        print(f"Method 1 failed for job {job_id}, trying method 2...")
        
    except Exception as e:
        print(f"Method 1 error for job {job_id}: {e}")
    
    # Method 2: Scrape the job posting page HTML (similar to your Greenhouse approach)
    if job_url:
        try:
            response = requests.get(job_url, timeout=10)
            response.raise_for_status()
            
            # Look for various date patterns in the HTML
            date_patterns = [
                r'"createdAt":\s*(\d+)',  # Timestamp in milliseconds
                r'"createdAt":\s*"([^"]+)"',  # ISO string
                r'data-created="([^"]+)"',  # HTML data attribute
                r'Posted on ([A-Za-z]+ \d+, \d{4})',  # Human readable date
                r'posting-date[^>]*>([^<]+)',  # CSS class based
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    
                    # Try to parse as timestamp first
                    try:
                        timestamp = int(date_str)
                        if timestamp > 1e12:  # Milliseconds
                            timestamp = timestamp / 1000
                        parsed = datetime.fromtimestamp(timestamp)
                        return parsed.strftime("%Y-%m-%d")
                    except:
                        pass
                    
                    # Try to parse as date string
                    try:
                        # Handle various date formats
                        if 'T' in date_str:  # ISO format
                            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:  # Try common formats
                            for fmt in ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"]:
                                try:
                                    parsed = datetime.strptime(date_str, fmt)
                                    return parsed.strftime("%Y-%m-%d")
                                except:
                                    continue
                    except:
                        pass
        
        except Exception as e:
            print(f"Method 2 error for job {job_id}: {e}")
    
    return "Date not found"


def save_to_csv(jobs, filename=CSV_FILE):
    """
    Save job list to CSV file.
    """
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["Title", "ID", "Team", "Location", "URL", "Date Published"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(jobs)


def main():
    print(f"Fetching jobs list for {ORG}...")
    all_jobs = get_all_jobs()
    print(f"Found {len(all_jobs)} matching jobs.")
    
    if not all_jobs:
        print("No jobs found. This could mean:")
        print("1. The company doesn't use Lever")
        print("2. They have no jobs matching your filters")
        print("3. Their API endpoint is different")
        return

    final_jobs = []
    for i, job in enumerate(all_jobs, 1):
        print(f"[{i}/{len(all_jobs)}] Fetching publish date for '{job['Title'][:50]}...'")
        pub_date = get_published_date(job["ID"], job["URL"])
        print(f"  → {pub_date}")
        job["Date Published"] = pub_date
        final_jobs.append(job)

    print(f"\nWriting {len(final_jobs)} jobs to {CSV_FILE}...")
    
    # Sort by date (most recent first), but handle "Date not found" entries
    def sort_key(job):
        try:
            return datetime.strptime(job['Date Published'], "%Y-%m-%d")
        except:
            return datetime.min  # Put "Date not found" entries at the end
    
    save_to_csv(sorted(final_jobs, reverse=True, key=sort_key))
    print("Done.")
    
    # Summary stats
    dated_jobs = [j for j in final_jobs if j['Date Published'] != 'Date not found']
    print(f"\nSummary:")
    print(f"  Total jobs: {len(final_jobs)}")
    print(f"  With dates: {len(dated_jobs)}")
    print(f"  Without dates: {len(final_jobs) - len(dated_jobs)}")


if __name__ == "__main__":
    main()