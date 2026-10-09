# Supercharge your job search filters across major tech companies

Manually tweaking job search filters for preferences across several companies 
can be really tiring.

Some companies also deliberately conceal the original job posting dates.

These factors constitute an unnecessary headache which is what this tool aims to tackle.

### Core Motive

This project provides **sophisticated and fully customizable search filters** 
that are easily extensible. And then, pulls the real posting dates from companies' 
underlying ATS backend (currently limited to ***Greenhouse*** and ***Lever*** 
with plans to expand), so you can make better decisions 
before applying and stop wasting time on ghost jobs.

### Precision in Preferences
You can craft highly precise and granular filters to whatever extent you deem feasible,
by manipulating the `search_filters` mapping and `search()` functions 
in the source files, and test as required. There are also countless other ways
you can explore to design your own filters as required.

**NOTE: This project is not affiliated with or endorsed by any of the companies or job platforms mentioned. 
It simply uses their public job board endpoints. USE RESPONSIBLY.**

## What's Inside

### **Batch Scrapers** 
Scrape multiple companies automatically:
- **Greenhouse batch**: 10 visa-friendly companies (Stripe, GitLab, Coinbase, DoorDash, etc.)
- **Lever batch**: 10 global/remote-first companies (Netflix, Spotify, Figma, Discord, etc.)

<details>
<summary>⚠️ <b>View Deprecated Configuration Guide (Legacy)</b></summary>

### **Single Company Scrapers**
> [!WARNING]
> **This feature has been deprecated.**
> ~~Targeted searches with user input:~~
> - ~~**Greenhouse scraper**: Works with Stripe, Lyft, and other Greenhouse-powered boards~~
> - ~~**Lever scraper**: Works with Netflix, Spotify, Airbnb, and other Lever-powered boards~~

</details>
<br>

All scrapers are optimized by default for locations like Canada, Ireland, Singapore, 
Australia, UK, Netherlands, and remote opportunities - basically anywhere that's not a visa nightmare.
But you can always change these as you wish.

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
> \* Most recent list is in the source files.

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