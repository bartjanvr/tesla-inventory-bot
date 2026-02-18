
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import requests

# ===================== CONFIG =====================
TESLA_URL = "https://www.tesla.com/nl_NL/inventory/used/my?CATEGORY=PAWD,PRAWD,LRAWD&arrangeby=plh&zip=2013WL&range=0"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxFtuNUR2cjtH92CvXnbIR8jSi2m2bQ6gC0AF0l4nQPg37cUJpL4LoMKMo68VKxwzA/exec"

# ===================== SCRAPER =====================
async def scrape():
    cars = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            locale="nl-NL"
        )

        page = await context.new_page()

        await page.goto(TESLA_URL, timeout=60000)
        await page.wait_for_load_state("networkidle")

        # Scroll to force lazy load
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(5000)

        html = await page.content()

        print("Page length:", len(html))  # DEBUG

        soup = BeautifulSoup(html, "lxml")
        cards = soup.find_all("div", {"data-testid": "inventory-card"})

        print("Found cards:", len(cards))  # DEBUG

        await browser.close()

    return cars

# ===================== GOOGLE SHEETS PUSH =====================
def push_to_google_sheet(vehicles):
    today = datetime.now().strftime("%Y-%m-%d")
    for car in vehicles:
        car["Date Scraped"] = today

    payload = {"vehicles": vehicles}
    response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
    print("Status code:", response.status_code)
    if response.status_code != 200:
        print("Response text:", response.text)
    else:
        print(f"Sent {len(vehicles)} cars.")

# ===================== MAIN =====================
async def main():
    vehicles = await scrape()
    if not vehicles:
        print("No cars found — check Tesla page or headers!")
        return
    push_to_google_sheet(vehicles)

if __name__ == "__main__":
    asyncio.run(main())
