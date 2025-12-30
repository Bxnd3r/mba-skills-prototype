import asyncio
from playwright.async_api import async_playwright
import json
import random
from datetime import datetime
import os

# Curated Boshkoska-aligned Roles
MBA_OCCUPATIONS = [
    "Management Analyst / Strategy Consultant", "Project Management Specialist", "Business Continuity Planner", "Chief Executive / Chief Operating Officer", "Chief Sustainability Officer", "Marketing Manager", "Market Research Analyst & Marketing Specialist", "Sales Manager", "Public Relations Manager", "Fundraising Manager", "Financial Manager", "Treasurer & Controller", "Investment Fund Manager", "Financial & Investment Analyst", "Financial Quantitative Analyst", "Personal Financial Advisor", "Credit Analyst", "Budget Analyst", "Loan Officer", "Insurance Underwriter", "Risk Management Specialist", "Supply‑chain Manager", "Transportation, Storage & Distribution Manager", "Purchasing Manager", "Cost Estimator / Cost Analyst", "Industrial Production Manager", "Operations Research Analyst", "General & Operations Manager", "Human Resources Manager", "Compensation & Benefits Manager", "Training & Development Manager", "Business Intelligence Analyst", "Computer & Information Systems Manager", "Information‑Technology Project Manager", "Medical & Health Services Manager", "Sustainability Specialist / Corporate Sustainability Manager"

]

LOCATIONS = ["Chicago, IL", "United States"]

async def scrape_full_data(keyword, location, limit=5):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Randomizing User Agent to look human
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        
        url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}"
        await page.goto(url)
        await asyncio.sleep(random.uniform(4, 7))

        jobs = []
        # Find the job card links
        cards = await page.locator('.base-card__full-link').all()
        
        for i in range(min(len(cards), limit)):
            try:
                await cards[i].click()
                await asyncio.sleep(random.uniform(3, 5))
                
                # Extracting specific data points
                title = await page.locator('.topcard__title').inner_text()
                # LinkedIn often has a "Show More" button for descriptions
                try:
                    await page.click('button.show-more-less-html__button--more', timeout=2000)
                except:
                    pass
                
                raw_desc = await page.locator('.description__text').inner_text()
                
                # CLEANING: Remove typical fluff/company headers
                # We split by common headers and take the core
                clean_desc = raw_desc.split("About the company")[0].strip()

                jobs.append({
                    "query": keyword,
                    "location": location,
                    "title": title.strip(),
                    "description": clean_desc,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                print(f"✅ Logged: {title[:25]} in {location}")
            except:
                continue
                
        await browser.close()
        return jobs

async def main():
    master_file = "market_data_corpus.json"
    
    # Load existing data to append to the same file
    if os.path.exists(master_file):
        with open(master_file, "r") as f:
            all_data = json.load(f)
    else:
        all_data = []

    for loc in LOCATIONS:
        for job in MBA_OCCUPATIONS:
            results = await scrape_full_data(job, loc)
            all_data.extend(results)
            # EXTENDED DELAY: To stay under the radar for 30 days
            print(f"⏳ Sleeping 45s between queries...")
            await asyncio.sleep(45) 

    with open(master_file, "w") as f:
        json.dump(all_data, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())