import os
import asyncio
from playwright.async_api import async_playwright

DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")

async def download_atis_excel():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        # headless=True 로 설정하여 화면이 없는 GitHub 서버에서도 동작하도록 수정
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("ATIS 페이지 접속 중...")
        await page.goto("https://atis.kotsu.or.kr/ATIS/stts/sttsEnggAt/sttsAtAc.do", wait_until="networkidle")

        # 엑셀 다운로드 버튼 클릭
        async with page.expect_download(timeout=60000) as download_info:
            # 엑셀 다운로드 버튼 (id 또는 onclick 속성 기반 선택)
            await page.click("a:has-text('엑셀'), button:has-text('엑셀'), #excelDownBtn, [onclick*='excel']")

        download = await download_info.value
        save_path = os.path.join(DOWNLOAD_DIR, "atis_aircraft_status.xlsx")
        await download.save_as(save_path)
        
        print(f"다운로드 완료: {save_path}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_atis_excel())
