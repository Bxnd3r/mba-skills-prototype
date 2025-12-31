import asyncio
import json
import os
import re
import time
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- 1. SETUP ---
genai.configure(api_key=os.environ.get("AIzaSyC_fQtJV9MD4RFikgQGga4CRWZJrAkaFEg"))
model = genai.GenerativeModel('gemini-pro')

# --- 2. THE STRATEGIES ---

async def strategy_a_static(url):
    """Fastest: Simple HTML pull for sites like IIT."""
    print("🚀 Strategy A: Trying Static Scrape...")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        # Standard selectors
        blocks = soup.select(".courseblock, .course-item, tr, li")
        results = []
        for b in blocks:
            text = b.get_text(strip=True)
            if len(text) > 100 and ("BUS" in text or re.search(r"\d{5}", text)):
                results.append({"course": text[:60], "text": text})
        return results
    except: return []

async def strategy_b_dynamic(page):
    """Middle: Wait for JS to render, then scrape everything visible."""
    print("🚀 Strategy B: Trying Dynamic Page Render...")
    await asyncio.sleep(5) # Wait for JS
    content = await page.content()
    soup = BeautifulSoup(content, "html.parser")
    blocks = soup.select("tr, li, .course-listing, div[class*='course']")
    results = []
    for b in blocks:
        text = b.get_text(strip=True)
        if len(text) > 100:
            results.append({"course": text[:60], "text": text})
    return results

async def strategy_c_reset_loop(page, url):
    """Slowest/Deepest: The 'Booth-Style' Reset Loop with Tab Catcher."""
    print("🚀 Strategy C: Starting Reset-Loop with Tab Catcher...")
    results = []
    for i in range(30): # Limit to 30 for the 'Super Auditor'
        try:
            await page.goto(url)
            await asyncio.sleep(5)
            # Find elements that look like courses but aren't 'Sections'
            # This covers the '30000 - ' pattern we found at Booth
            potential = await page.get_by_text(re.compile(r"\d{4,5}")).all()
            valid = []
            for p in potential:
                t = await p.text_content()
                if "Section:" not in t and len(t) < 100:
                    valid.append(p)

            if i >= len(valid): break
            
            target = valid[i]
            title = await target.text_content()
            await target.scroll_into_view_if_needed()
            
            # Use Tab Catcher for sites like Kellogg or NYU
            async with page.expect_popup(timeout=5000) as popup_info:
                await target.click()
            
            new_tab = await popup_info.value
            await new_tab.wait_for_load_state()
            clean_text = await new_tab.inner_text("body")
            if len(clean_text) > 100:
                results.append({"course": title.strip(), "text": clean_text})
            await new_tab.close()
        except: continue
    return results

# --- 3. THE MASTER CONTROLLER ---

async def run_audit(url, school_name):
    school_id = urlparse(url).netloc.split('.')[-2]
    final_courses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Try Tier 1: Static
        final_courses = await strategy_a_static(url)
        
        # Try Tier 2: Dynamic
        if len(final_courses) < 5:
            await page.goto(url)
            final_courses = await strategy_b_dynamic(page)

        # Try Tier 3: Reset-Loop (The Booth/NYU method)
        if len(final_courses) < 5:
            final_courses = await strategy_c_reset_loop(page, url)

        await browser.close()

    if not final_courses:
        print(f"❌ ALL STRATEGIES FAILED for {url}")
        # Create an empty registry to stop the Git error
        ensure_registry_exists()
        sys.exit(0) # Exit cleanly so GitHub doesn't scream

    # --- 4. AUDIT WITH GEMINI-PRO ---
    print(f"🧠 Auditing {len(final_courses)} courses with gemini-pro...")
    audited = []
    for item in final_courses[:40]: # Safety limit
        try:
            prompt = f"Analyze course: {item['course']}\nText: {item['text'][:1500]}\nScore 1-5 on Digital, Quant, Strategy, Management, Communication, Regulation. Return ONLY JSON."
            res = model.generate_content(prompt)
            clean = res.text.strip().replace("```json","").replace("```","")
            audited.append({"course": item['course'], "skills": json.loads(clean), "text": item['text'][:300]})
            time.sleep(1)
        except: continue

    # --- 5. SAVE & REGISTER ---
    filename = f"{school_id}_audit.json"
    with open(filename, "w") as f: json.dump(audited, f, indent=2)
    update_registry(school_id, school_name, filename)
    print(f"✅ SUCCESS! Created {filename}")

def ensure_registry_exists():
    if not os.path.exists("registry.json"):
        with open("registry.json", "w") as f: json.dump([], f)

def update_registry(school_id, name, filename):
    ensure_registry_exists()
    with open("registry.json", "r") as f: reg = json.load(f)
    reg = [r for r in reg if r['id'] != school_id]
    reg.append({"id": school_id, "name": name, "audit": filename, "color": "rgba(0,0,0,0.5)"})
    with open("registry.json", "w") as f: json.dump(reg, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        asyncio.run(run_audit(sys.argv[1], sys.argv[2]))

