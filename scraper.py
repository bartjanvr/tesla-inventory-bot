
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
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Visit Tesla page
        await page.goto(TESLA_URL, timeout=60000)
        await page.wait_for_timeout(8000)  # wait for content to load

        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        # Tesla lists cars in divs with data-testid="inventory-card"
        cards = soup.find_all("div", {"data-testid": "inventory-card"})

        for card in cards:
            title = card.find("h5")
            price = card.find("span", string=lambda x: x and "€" in x)
            mileage = card.find("li", string=lambda x: x and "km" in x)
            first_reg = card.find("li", string=lambda x: x and "Datum eerste registratie" in x)
            link = card.find("a", href=True)
            range_km = card.find("li", string=lambda x: x and "km" in x and "actieradius" in x.lower())
            color = card.find("li", string=lambda x: x and "kleur" in x.lower())
            wheels = card.find("li", string=lambda x: x and "wielen" in x.lower())
            interior = card.find("li", string=lambda x: x and "interieur" in x.lower())
            towbar = card.find("li", string=lambda x: x and "trekhaak" in x.lower())

            car = {
                "Link": "https://www.tesla.com" + link["href"] if link else "",
                "Title": title.text.strip() if title else "",
                "Price": price.text.strip() if price else "",
                "Mileage": mileage.text.strip() if mileage else "",
                "First Registration": first_reg.text.strip() if first_reg else "",
                "Range": range_km.text.strip() if range_km else "",
                "Color": color.text.strip() if color else "",
                "Wheels": wheels.text.strip() if wheels else "",
                "Interior Color": interior.text.strip() if interior else "",
                "Has Towbar": towbar.text.strip() if towbar else "",
            }

            cars.append(car)

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
