from playwright.async_api import async_playwright

async def visit_report(target_url, password, username='admin'):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        await page.goto('https://localhost:5000/login')

        await page.fill('#username', username)
        await page.fill('#password', password)
        await page.click('button[type="submit"]')

        await page.wait_for_load_state("networkidle")
        
        print(f"[+] Visiting: {target_url}")
        await page.goto(target_url)

        await page.wait_for_load_state("networkidle")

        await browser.close()