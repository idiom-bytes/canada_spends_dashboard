import argparse
import asyncio
import pathlib

from playwright.async_api import async_playwright


DEFAULT_FLAGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-software-rasterizer",
    "--disable-setuid-sandbox",
    "--no-zygote",
    "--single-process",
]


async def capture(url: str, output_path: pathlib.Path, delay_ms: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=DEFAULT_FLAGS)
        page = await browser.new_page(viewport={"width": 1280, "height": 720})
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(delay_ms)
        await page.screenshot(path=str(output_path), full_page=True)
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a dashboard screenshot with stable Playwright flags.")
    parser.add_argument("--url", default="http://localhost:8000/index.html")
    parser.add_argument("--output", default="artifacts/dashboard.png")
    parser.add_argument("--delay-ms", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(capture(args.url, pathlib.Path(args.output), args.delay_ms))


if __name__ == "__main__":
    main()
