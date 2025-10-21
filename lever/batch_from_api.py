import csv
import os
import re
import requests
from datetime import datetime
import time

# --- Configuration ---
# Companies using Lever with strong visa sponsorship/remote culture
CSV_FILE = os.getcwd() + "/lever/data/from_api_lever_{}_jobs.csv"
FIELDNAMES = [
    "Company", 
    "Title", 
    "ID", 
    "Team", 
    "Location", 
    "URL", 
    "Date Published", 
    "Local Date Published"
]
COMPANIES = {
    #  'mistral': 'mistral',
    # 'bluematrix': 'bluematrix',
    # 'eyeline': 'eyeline',
    'apolloresearch': 'apolloresearch',
    'influur': 'influur',
    'payjoy': 'payjoy',
    'pingwind': 'pingwind',
    'loadsmart': 'loadsmart',
    'bounteous': 'bounteous',
    'vida': 'vida',
    'brillio-2': 'brillio-2',
    'the-sia-foundation': 'the-sia-foundation',
    'symphony': 'symphony',
    'bestEgg': 'bestEgg',
    'oxylabs': 'oxylabs',
    'binance': 'binance',
    'rover': 'rover',
    'todaytixgroup': 'todaytixgroup',
    'margo-group': 'margo-group',
    'myob-2': 'myob-2',
    'animocabrands': 'animocabrands',
    'kraken123': 'kraken123',
    'allegiantair': 'allegiantair',
    'netflix': 'netflix',        # Global presence, excellent compensation
    'spotify': 'spotify',        # European HQ, global remote-friendly
    'palantir': 'palantir',     # Global presence, sponsors visas
}

SEARCH_FILTERS = {
    'titles': {
        'engineer', 'backend', 'back end', 'fullstack', 'full-stack',
        'full stack', 'developer', 'python', 'javascript',
        'software engineer', 'senior engineer', 'staff engineer',
        'frontend', 'front end', 'mobile', 'ios', 'android',
        'devops', 'platform', 'infrastructure', 'data engineer'
    },
    'locations': {
        'LT', 'IE', 'AU', 'SG', 'KSA', 'NZ', 'CA', 'QC', 'VC', 'MB', 'BC', 
        'ireland', 'dublin', 'athlone', 
        'canada', 'toronto', 'vancouver', 'british columbia', 'montreal',
        'ontario', 'halifax', 'nova scotia', 'edmonton', 'quebec',
        'singapore', 'malaysia', 'kuala lumpur',
        'australia', 'sydney', 'melbourne', 'brisbane',
        'new south wales', 'nsw', 'new zealand', 'wellington', 'auckland',
        'united kingdom', 'u.k.', 'uk', 'london', 'leeds', 'bristol', 
        'belfast', 'eidinburgh', 'cardiff', 'manchester', 'birmingham',
        'romania', 'bucharest', 'lithuania', 'vilnius',
        'poland', 'warsaw', 'prague', 'czech', 'czechia',
        'paris', 'france', 'belgium', 'bruges',
        'amsterdam', 'netherlands',
        'worldwide', 'global', 'europe', # 'remote',
        'berlin', 'germany', 'stockholm', 'sweden',
        'doha', 'qatar', 'muscat', 'oman', 'bahrain', 
        'riyadh', 'saudi', 'arabia', 'ksa', 'kuwait',
        'bangkok', 'thailand', 'ho chi minh', 'vietnam',
        'johannesburg', 'south africa', 'tunisia', 'sychelles', 'mauritius',
    },
    'excluded_roles': {
        'senior', 'principal', 'manager', 'staff',
        'sr ', 'sr', 'snr', 'sr.', 'snr.',
        'director', 'lead', 'head', 'chief',
    },
    'excluded_locations': {
        'usa', 'u.s.a.', 'u.s.a', 'u.s.', 'u.s', 'us',
        'united states', 'united states of america',
        'india', 'china', 'korea', 'russia',
    }
}


def search_old(query: list[str], filters: dict[str, list[str]]):
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


def search(query: list[str], filters: dict[str, list[str]|set[str]]):
    # return True 
    title_q = set(re.split('\W+', query[0].lower())).union(set(query[0].lower().split(" ")))
    location_q = set(re.split('\W+', query[1].lower())).union(set(query[1].lower().split(" ")))

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

    for role in title_q: # excluded_roles:
        if role in excluded_roles: # title_q:
            roles_exclusion_passed = False
            return False
    
    for title in title_q: # titles:
        if title in titles: # title_q:
            titles_matched = True
            break
    
    for location in location_q: # locations:
        if location in locations: # location_q:
            locations_matched = True
            break
    
    # Debugging purposes
    # print(f"""WHAT FAILED?
    #       titles and locations: {title_q} :: {location_q}
    #       title matched: {titles_matched}
    #       location matched: {locations_matched}
    #       roles exclusion passed: {roles_exclusion_passed}
    #       locations exclusion passed: {locations_exclusion_passed}\n""")
            
    return titles_matched and \
            locations_matched and \
            roles_exclusion_passed and \
            locations_exclusion_passed


def get_all_jobs(company):
    """
    Fetch all jobs from the Lever jobs API and filter payload locally.
    Returns a list of dicts with Title, Location, URL, and ID.
    """
    # jobs_api_url = f"https://api.lever.co/v0/postings/{company}"
    jobs_api_url_alt = f"https://api.lever.co/v0/postings/{company}?mode=json"
    
    jobs = []
    
    # Try primary API endpoint first
    try:
        response = requests.get(jobs_api_url_alt, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e2:
        print(f"  ❌ Failed to fetch jobs for {company}: {e2}")
        return []

    for job in data:
        # Lever API structure
        title = job.get("text", "")
        
        # Location handling - Lever can have multiple locations
        country = job.get("country")
        locations = job.get("categories", {}).get("location", [])
        if isinstance(locations, str):
            location_str = locations
        elif isinstance(locations, list) and locations:
            location_str = ", ".join(locations)
        else:
            location_str = "Location not specified" if not country else country
        
        # Check if job matches our filters
        if search(query=[title, location_str], filters=SEARCH_FILTERS):
            jobs.append({
                "Company": company.capitalize(),
                "Title": title,
                "Location": location_str,
                "URL": job.get("hostedUrl", ""),
                "ID": job.get("id", ""),
                "Team": job.get("categories", {}).get("team", [""])[0] if job.get("categories", {}).get("team") else ""
            })
    
    return jobs


def get_published_date(company, job_id, job_url):
    """
    Fetch the 'createdAt' or publication date for a given job.
    Returns a formatted YYYY-MM-DD string or 'Date not found'.
    """
    
    # Method 1: Try individual job API endpoint
    try:
        individual_api_url = f"https://api.lever.co/v0/postings/{company}/{job_id}"
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
                # Original timezone (usually UTC for most APIs)
                original_tz = parsed.strftime("%Y-%m-%d %H:%M:%S %Z")
                
                # Convert to local timezone
                local_time = parsed.astimezone()  # Converts to system local timezone
                local_tz = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                
                return {
                    'original': original_tz,      # e.g., "2024-01-15 14:30:25 UTC"
                    'local': local_tz             # e.g., "2024-01-15 09:30:25 EST"
                }
            elif isinstance(created_at, str):
                # Try to parse ISO format
                try:
                    parsed = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        # Original timezone (usually UTC for most APIs)
                    original_tz = parsed.strftime("%Y-%m-%d %H:%M:%S %Z")
                    
                    # Convert to local timezone
                    local_time = parsed.astimezone()  # Converts to system local timezone
                    local_tz = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                    
                    return {
                        'original': original_tz,      # e.g., "2024-01-15 14:30:25 UTC"
                        'local': local_tz             # e.g., "2024-01-15 09:30:25 EST"
                    }
                except:
                    pass
        
    except Exception as e:
        pass  # Silently fail and try method 2
    
    # Method 2: Scrape the job posting page HTML
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
                r'"publishedAt":\s*(\d+)',  # Alternative field name
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
                        # Original timezone (usually UTC for most APIs)
                        original_tz = parsed.strftime("%Y-%m-%d %H:%M:%S %Z")
                        
                        # Convert to local timezone
                        local_time = parsed.astimezone()  # Converts to system local timezone
                        local_tz = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                        
                        return {
                            'original': original_tz,      # e.g., "2024-01-15 14:30:25 UTC"
                            'local': local_tz             # e.g., "2024-01-15 09:30:25 EST"
                        }
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
                                    # Original timezone (usually UTC for most APIs)
                                    original_tz = parsed.strftime("%Y-%m-%d %H:%M:%S %Z")
                                    
                                    # Convert to local timezone
                                    local_time = parsed.astimezone()  # Converts to system local timezone
                                    local_tz = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                                    
                                    return {
                                        'original': original_tz,      # e.g., "2024-01-15 14:30:25 UTC"
                                        'local': local_tz             # e.g., "2024-01-15 09:30:25 EST"
                                    }
                                except:
                                    continue
                    except:
                        pass
        
        except Exception as e:
            pass
    
    return {
        'original': "1970-01-01 00:00:00",
        'local': "1970-01-01 00:00:00"
    }


def save_to_csv_old(jobs, company):
    """
    Save job list to company-specific CSV file.
    """
    filename = CSV_FILE.format(company)  # f"lever_{company}_jobs.csv"
    file_exists = os.path.isfile(filename)
    
    with open(filename, "a", newline="", encoding="utf-8") as f:
        fieldnames = FIELDNAMES
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists or os.stat(filename).st_size == 0:
            writer.writeheader()

        writer.writerows(jobs)


def save_to_csv(jobs, company, clean_sweep=False):
    """
    Save or update job list to a company-specific CSV file.

    - Deduplicates jobs by 'ID'
    - Preserves 'Local Date Published' from existing rows (if present)
    - If clean_sweep=True, overwrites the file completely without merging
    """
    filename = CSV_FILE.format(company)
    fieldnames = FIELDNAMES

    if not clean_sweep and os.path.isfile(filename):
        # Step 1: Load existing data
        existing = {}
        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[row["ID"]] = row

        # Step 2: Merge — preserve 'Local Date Published' where possible
        for job in jobs:
            job_id = job["ID"]
            if job_id in existing:
                old_row = existing[job_id]
                if old_row.get("Local Date Published"):
                    job["Local Date Published"] = old_row["Local Date Published"]
            existing[job_id] = job

        merged_jobs = list(existing.values())

    else:
        # Clean sweep: just write what was passed in
        merged_jobs = jobs

    # Step 3: Write everything (overwrite mode)
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_jobs)

    print(f"Saved {len(merged_jobs)} unique jobs to {filename}{' (clean sweep)' if clean_sweep else ''}")


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
        pub_date = get_published_date(company, job["ID"], job["URL"])
        print(pub_date)
        job["Date Published"] = pub_date['original']
        job["Local Date Published"] = pub_date['local']
        final_jobs.append(job)
        
        # Small delay to be respectful to the API
        time.sleep(0.7)  # Lever seems more rate-limited than Greenhouse
    
    # Sort by date (most recent first)
    def sort_key(job):
        try:
            return datetime.strptime(job['Date Published'], "%Y-%m-%d")
        except:
            return datetime.min
    
    sorted_jobs = sorted(final_jobs, reverse=True, key=sort_key)
    
    # Save to CSV
    save_to_csv(sorted_jobs, company, True)
    
    # Stats
    dated_jobs = [j for j in sorted_jobs if j['Date Published'] != '1970-01-01 00:00:00']
    print(f"  💾 Saved {len(sorted_jobs)} jobs to lever_{company}_jobs.csv")
    print(f"  📊 {len(dated_jobs)} with dates, {len(sorted_jobs) - len(dated_jobs)} without dates")
    
    return len(sorted_jobs)


def main():
    print("🚀 LEVER BATCH SCRAPER")
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
    
    print(f"\n🎯 FINAL SUMMARY")
    print("=" * 30)
    print(f"Companies processed: {successful_companies}/{len(COMPANIES)}")
    print(f"Total jobs scraped: {total_jobs}")
    print(f"CSV files created: lever_[company]_jobs.csv")
    
    if total_jobs > 0:
        print(f"\n💡 Pro tip: You can combine all CSVs with:")
        print(f"   cat lever_*_jobs.csv | grep -v '^Company,Title' | sort -t, -k7 -r > all_lever_jobs.csv")


if __name__ == "__main__":
    main()