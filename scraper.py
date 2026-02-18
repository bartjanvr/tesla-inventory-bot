import asyncio
import requests
from datetime import datetime
from playwright.async_api import async_playwright

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFtuNUR2cjtH92CvXnbIR8jSi2m2bQ6gC0AF0l4nQPg37cUJpL4LoMKMo68VKxwzA/exec"

TESLA_URL = "https://www.tesla.com/nl_NL/inventory/used/my?arrangeby=plh&zip=2013WL&range=0"

async def scrape():
    cars = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TESLA_URL, timeout=60000)
        await page.wait_for_timeout(8000)

        data = await page.content()

        # Extract JSON from page
        json_data = await page.evaluate("""
            () => window.__NEXT_DATA__
        """)

        vehicles = json_data.get("props", {}) \
                            .get("pageProps", {}) \
                            .get("inventory", {}) \
                            .get("results", [])

        for v in vehicles:
            car = {
                "VIN": v.get("VIN", ""),
                "DateAdded": datetime.now().strftime("%Y-%m-%d"),
                "Link": "https://www.tesla.com" + v.get("VehicleDetailUrl", ""),
                "Title": v.get("TrimName", ""),
                "Mileage": v.get("Odometer", ""),
                "Price": v.get("PurchasePrice", ""),
                "FirstRegistration": v.get("FirstRegistrationDate", ""),
                "Range": v.get("Range", ""),
                "Color": v.get("PAINT", ""),
                "Wheels": v.get("WHEELS", ""),
                "Interior": v.get("INTERIOR", ""),
                "Towbar": "Yes" if "TOWING" in str(v.get("OptionCodes", "")) else "No"
            }

            cars.append(car)

        await browser.close()

    return cars


async def main():
    vehicles = await scrape()

    for car in vehicles:
        requests.post(WEBHOOK_URL, json=car)

    print(f"Sent {len(vehicles)} vehicles.")


if __name__ == "__main__":
    asyncio.run(main())
