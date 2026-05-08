import csv
import os
import re
import requests
from datetime import datetime
import time

# --- Configuration ---
# Companies using Greenhouse with strong visa sponsorship/remote culture
CSV_FILE = os.getcwd() + "/greenhouse/data/from_api_gh_{}_jobs.csv"
API_URL_BASE = "https://job-boards.greenhouse.io/embed/job_app?for={}&token="
FIELDNAMES = [
    "Company", 
    "Title", 
    "Token", 
    "Location", 
    "URL", 
    "Date Published", 
    "Local Date Published", 
    "Date Updated", 
    "Local Date Updated"
]
COMPANIES = {
    # 'addepar1': 'addepar1',  # NOT visa friendly !!!
    'wehrtyou': 'wehrtyou',  # hudson river trading
    'gradyent': 'gradyent',
    'silvare': 'silvare',
    'wolt': 'wolt',
    'axicorpfinancialservicesptyltd': 'axicorpfinancialservicesptyltd',
    'checkr': 'checkr',
    'vividseatsllc': 'vividseatsllc',
    'complyadvantage': 'complyadvantage',
    'navvis': 'navvis',
    'anthropic': 'anthropic',
    'appian': 'appian',
    'trustpilot': 'trustpilot',
    'capco': 'capco',
    'wrike': 'wrike',
    'chalkinc': 'chalkinc',
    # 'grafanalabs': 'grafanalabs',
    'transcendinc': 'transcendinc',
    'altium': 'altium',
    'hubspot': 'hubspot',
    'intercom': 'intercom',
    'thoughtworks': 'thoughtworks',
    'tamara': 'tamara',
    'bolcomen': 'bolcomen',
    'mavensecuritiesholdingltd': 'mavensecuritiesholdingltd',  # Registered UK sponsor
    'polyai': 'polyai',
    'sofiastars': 'sofiastars',
    'oldmissioncapital': 'oldmissioncapital',
    'atomicmachines': 'atomicmachines',
    'b2c2': 'b2c2',
    'airbnb': 'airbnb',
    'coursera': 'coursera',
    'lightspeed': 'lightspeed',
    'accenturefederalservices': 'accenturefederalservices',
    # 'akunacapital': 'akunacapital',
    'wpp': 'wpp',
    'lighthouse': 'lighthouse',
    'yougov': 'yougov',
    'datadog': 'datadog',
    'eucalyptus': 'eucalyptus',
    'rtbhouse': 'rtbhouse',
    'mixpanel': 'mixpanel',
    'agoda': 'agoda',            # Known for SEA relocation and visa sponsorship
    'stripe': 'stripe',          # Global, excellent visa sponsorship
    'lyft': 'lyft',              # proritizes local talent; reluctant to offer sponsorship
    'gitlab': 'gitlab',          # All-remote company
    'coinbase': 'coinbase',      # Global presence, sponsors visas
    'tripadvisor': 'tripadvisor',
    'robinhood': 'robinhood',    # Growing international presence
    'twilio': 'twilio',          # Global offices, remote-friendly
    'databricks': 'databricks',  # Global presence, sponsors visas
    'snapmobileinc': 'snapmobileinc',
    'reddit': 'reddit',          # Remote-first culture
    'pinterest': 'pinterest',
    'chanzuckerbergbiohub': 'chanzuckerbergbiohub',
    'verkada': 'verkada',        # Pledges to get visa for offer receivers
    'towerresearchcapital': 'towerresearchcapital',
}
SEARCH_FILTERS = {
    'titles': {
        'engineer', 'backend', 'back end', 'fullstack', 'full-stack',
        'full stack', 'developer', 'python', 'django',
        'javascript', 'node', 'nodejs', 'node.js', 
        'software engineer', 'customer', 'platform', 'mobile',
        'android', 'infrastructure', 'forward deployed', 
        'support',
        'support engineer', 'support analyst', 'system analyst',
        'system support', 'software support', 'product support',
        'tech support', 'technical support', 'support specialist',
    },
    'locations': {
        # Generic
        'flexible', 'worldwide', 'global', 'multiple', 'emea', 'apac',

        # Scandinavia
        'norway', 'sweden', 'finland', 'iceland', 'helsinki', 'denmark', 
        'oslo', 'malmo',

        # --- Lithuania ---
        'LT', 'lithuania', 'vilnius', 'kaunas', 'klaipeda',

        # --- Ireland ---
        'IE', 'ireland', 'dublin', 'athlone', 'cork', 'limerick', 'galway', 'waterford',

        # --- Australia ---
        'AU', 'australia', 'sydney', 'melbourne', 'brisbane', 
        'perth', 'adelaide', 'canberra', 'hobart', 'darwin', 
        'new south wales', 'queensland', 'victoria',

        # --- Singapore ---
        'SG', 'singapore',

        # --- Saudi Arabia ---
        'KSA', 'ksa', 'saudi', 'arabia', 'riyadh', 'jeddah', 'dammam', 'khobar', 'mecca', 'medina',

        # --- New Zealand ---
        'NZ', 'new zealand', 'wellington', 'auckland', 'hamilton', 'christchurch', 'dunedin',

        # --- Canada ---
        'CA', 'QC', 'MB', 'BC', 'canada', 'ontario', 'british columbia', 'alberta',
        'saskatchewan', 'manitoba', 'quebec', 'nova scotia', 'new brunswick', 'newfoundland',
        'toronto', 'vancouver', 'montreal', 'edmonton', 'calgary', 'halifax', 'ottawa',
        'winnipeg', 'victoria',

        # --- United Kingdom ---
        'united kingdom', 'u.k.', 'uk', 'london', 'leeds', 'bristol', 
        'belfast', 'edinburgh', 'cardiff', 'manchester', 'birmingham', 
        'glasgow', 'liverpool', 'newcastle', 'nottingham', 'sheffield',

        # --- Romania ---
        'romania', 'bucharest', 'cluj-napoca', 'iasi', 'timisoara', 'brasov',

        # --- Poland ---
        'poland', 'warsaw', 'krakow', 'wroclaw', 'poznan', 'gdansk', 'lodz',

        # --- Czech Republic ---
        'prague', 'czech', 'czechia', 'brno', 'ostrava', 'plzen',

        # --- France ---
        'france', 'paris', 'lyon', 'marseille', 'toulouse', 'lille',
        'bordeaux', 'nice', 'nantes', 'strasbourg',

        # --- Belgium ---
        'belgium', 'bruges', 'brussels', 'ghent', 'antwerp', 'leuven',

        # --- Netherlands ---
        'amsterdam', 'netherlands', 'rotterdam', 'the hague', 'utrecht', 'eindhoven', 'groningen',

        # --- Germany ---
        'berlin', 'germany', 'munich', 'frankfurt', 'stuttgart', 'hamburg', 
        'cologne', 'dusseldorf', 'dresden', 'leipzig',

        # --- Sweden ---
        'stockholm', 'sweden', 'gothenburg', 'malmo', 'uppsala', 'lund',

        # --- Finland ---
        'finland', 'helsinki', 'tampere', 'espoo', 'oulu',

        # --- Denmark ---
        'denmark', 'copenhagen', 'aarhus', 'odense', 'aalborg',

        # --- Austria ---
        'austria', 'vienna', 'graz', 'salzburg', 'innsbruck', 'linz',

        # --- Switzerland ---
        'switzerland', 'zurich', 'geneva', 'lausanne', 'basel', 'bern', 'lugano',

        # --- Slovenia ---
        'slovenia', 'ljubljana', 'maribor',

        # --- Croatia ---
        'croatia', 'zagreb', 'split', 'rijeka',

        # --- Estonia ---
        'estonia', 'tallinn', 'tartu', 'narva',

        # --- Latvia ---
        'latvia', 'riga', 'jelgava', 'daugavpils',

        # --- Cyprus ---
        'cyprus', 'nicosia', 'limassol', 'larnaca', 'paphos',

        # --- Thailand ---
        'bangkok', 'thailand', 'chiang mai', 'phuket', 'pattaya',

        # --- Vietnam ---
        'ho chi minh', 'vietnam', 'hanoi', 'da nang', 'can tho',

        # --- Qatar / GCC residuals ---
        'doha', 'qatar', 'muscat', 'oman', 'bahrain', 'kuwait', 'kuwait city',

        # --- Africa* ---
        'johannesburg', 'rsa', 'south africa', 'tunisia', 'tunis', 'seychelles', 'mahe', 'mauritius', 'port louis',

        # --- Global / Remote ---
        'worldwide', 'global', 'global remote', 'global/remote', 'remote/global',
        
        # --- Hungary ---
        # 'hungary', 'budapest', 'szeged', 'debrecen',
     
        # --- Portugal ---
        'portugal', 'lisbon', 'porto', 'braga', 'aveiro', 'coimbra',

        # --- Spain ---
        # 'spain', 'barcelona', 'madrid', 'valencia', 'malaga', 'seville', 'bilbao',
        
        # --- Slovakia ---
        # 'slovakia', 'bratislava', 'kosice', 'presov',
        
        # --- Malaysia ---
        # 'malaysia', 'kuala lumpur', 'selangor', 'penang', 'johor bahru', 'sabah', 'sarawak', 'malacca',
    },
    'excluded_roles': {
        'android', 'frontend', 'front-end',
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


def search(query: list[str], filters: dict[str, list[str]|set[str]]):
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
    is_good = False
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        is_good = True
    except ValueError:
        parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")
        is_good = True
    finally:
        if not is_good:  # API returns garbage or `null` data values, just default to a fallback
                return {
            'original': "1970-01-01 00:00:00",
            'local': "1970-01-01 00:00:00"
        }
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


def save_to_csv_old(jobs, company):
    """
    Save job list to company-specific CSV file.
    """
    filename = CSV_FILE.format(company)  # os.getcwd() + f"/greenhouse/vacancies/from_api_gh_{company}_jobs.csv"
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
        print(f"  [{i:2d}/{len(all_jobs)}] {job['Title'][:60]:<60} ...  Published: {job['Local Date Published'][:20]}  Updated: {job['Local Date Updated'][:20]}  {job['URL']}")
        final_jobs.append(job)
        
        # Small delay to be respectful to the API
        time.sleep(0.5)
    
    # Sort by date (most recent first)
    def sort_key(job):
        try:
            return datetime.strptime(job['Date Published'], "%Y-%m-%d")
        except:
            return datetime.min
    
    sorted_jobs = sorted(final_jobs, reverse=True, key=lambda d: datetime.strptime(
        d['Date Published'][:-6], "%Y-%m-%d %H:%M:%S %Z"
    ))  # sorted(final_jobs, reverse=True, key=sort_key)
    
    # Save to CSV
    save_to_csv(sorted_jobs, company, True)
    
    # Stats
    dated_jobs = [j for j in sorted_jobs if '1970' not in j['Date Published']]
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
            print(f"  💥 Unexpected error processing {company}: {e, e.__traceback__.__str__}")
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