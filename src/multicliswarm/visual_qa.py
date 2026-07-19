import os
import logging

logger = logging.getLogger("multicliswarm.visual_qa")

def take_screenshot_sync(html_file_path: str, output_image_path: str) -> bool:
    """
    Uses playwright to take a screenshot of a local HTML file.
    Returns True if successful, False otherwise.
    """
    try:
        from playwright.sync_api import sync_playwright
        
        abs_path = os.path.abspath(html_file_path)
        file_url = f"file://{abs_path}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(file_url)
            page.screenshot(path=output_image_path, full_page=True)
            browser.close()
        return True
    except ImportError:
        logger.warning("Playwright not installed. Skipping Visual QA.")
        return False
    except Exception as e:
        logger.warning(f"Failed to take screenshot with playwright: {e}\n(Tip: Run 'playwright install' if browsers are missing)")
        return False
