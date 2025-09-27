# Expose job posting dates across major tech companies

Most job boards deliberately hide when roles were actually published, 
which makes it hard to know if you're looking at a fresh opportunity 
or something that's been sitting there for ages (seriously, who wants to apply for a role posted 756 centuries ago?).  
This project pulls the real posting dates from companies' underlying ***Greenhouse*** and ***Lever*** data, 
so you can make better decisions before applying and stop wasting time on ghost jobs.

**Note: This project is not affiliated with or endorsed by any of the companies or job platforms mentioned. 
It simply uses their public job board endpoints. Use responsibly.**

## What's Inside

### **Single Company Scrapers**
Targeted searches with user input:
- **Greenhouse scraper**: Works with Stripe, Lyft, and other Greenhouse-powered boards
- **Lever scraper**: Works with Netflix, Spotify, Airbnb, and other Lever-powered boards

### **Batch Scrapers** 
Scrape multiple companies automatically:
- **Greenhouse batch**: 10 visa-friendly companies (Stripe, GitLab, Coinbase, DoorDash, etc.)
- **Lever batch**: 10 global/remote-first companies (Netflix, Spotify, Figma, Discord, etc.)

All scrapers are optimized for locations like Canada, Ireland, Singapore, Australia, UK, Netherlands, and remote opportunities - basically anywhere that's not a visa nightmare.

## Features

- Extracts job listings directly from company job boards
- Aggressively hunts down hidden `published_at` and `createdAt` fields 
- Saves results into clean CSV files for easy sorting/filtering
- **Batch processing**: Scrape 20+ companies in one go
- **Individual CSVs**: Each company gets its own file for better organization
- **Smart filtering**: Only grabs engineering roles in target locations
- **Rate limiting**: Respectful delays to avoid getting blocked
- **Fallback strategies**: Multiple approaches to extract dates when companies try to hide them

## Requirements

- Python 3.9+ (tested on Python 3.10)
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

Each module has single and batch company scrapers (`.py` files you can execute or customized as you wish),
 with the choice of API or frontend oriented extraction.

## Companies Covered <sup>*</sup>

> [!NOTE]  
> \* This list is constantly being updated and is only provisional.

> [!TIP]  
> \* Customization is a walk in the park, you are highly encouraged to merge helpful improvements.

### Greenhouse Platform
- **Stripe** - Global payments, excellent visa sponsorship
- **GitLab** - All-remote company
- **Coinbase** - Global crypto exchange
- **DoorDash** - Expanding globally
- **Robinhood** - Growing international presence
- **Twilio** - Global offices, remote-friendly
- **Databricks** - Global presence, sponsors visas
- **Canva** - Australia-based, global remote
- **Reddit** - Remote-first culture
- **Lyft** - Good sponsorship track record

### Lever Platform
- **Netflix** - Global streaming giant
- **Spotify** - European HQ, global remote-friendly
- **Airbnb** - Global platform
- **Figma** - Remote-first design tools
- **Notion** - Distributed team
- **Discord** - Remote culture, global hiring
- **GitHub** - Microsoft-owned, global presence
- **Shopify** - Canadian HQ, global offices
- **Palantir** - Global presence, sponsors visas
- **Mixpanel** - Global analytics, remote-friendly

## Why These Companies?

Personal preferences aside, all selected companies have:
- Strong track record of visa sponsorship
- Global or remote-first culture  
- Active hiring in target locations (Canada, EU, APAC, etc.)
- Engineering-focused roles
- Transparent about remote work policies

## Extensions & Pull Requests

There are other mega-robust scrapers repo doing sort of the same thing as this one,
but not much attention is given to extracting the actual posting dates. If you can help
with this, you are more than welcomed to make a PR.

## Helpful Resources

* https://www.jobscan.co/blog/greenhouse-ats-what-job-seekers-need-to-know

## Disclaimer

THIS PROJECT IS FOR PERSONAL AND EDUCATIONAL USE. 
IT ONLY INTERACTS WITH PUBLICLY AVAILABLE ENDPOINTS.
PLEASE AVOID EXCESSIVE API REQUESTS AND BE MINDFUL THAT COMPANIES 
OR JOB PLATFORMS MAY CHANGE THEIR SETUP AT ANY TIME.
DON'T BE A D*CK TO THEIR SERVERS!