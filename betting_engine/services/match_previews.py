from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import time


class MatchPreviews:
    """
    Service to scrape match previews from Forebet preview links.
    Extracts HTML content from <p> tags for display in Vue.js frontend.
    """

    def __init__(self, data_dir=None, headless=True):
        """
        Initialize the preview scraper.

        Args:
            data_dir: Directory containing the JSON files. Defaults to betting_data/
            headless: Whether to run browser in headless mode
        """
        if data_dir is None:
            # Get the project root (assuming this file is in betting_engine/services/)
            project_root = Path(__file__).parent.parent.parent
            self.data_dir = project_root / 'betting_data'
        else:
            self.data_dir = Path(data_dir)
        
        self.headless = headless

    def load_tips(self, date_str):
        """
        Load tips file.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            List of dictionaries containing tips data
        """
        file_path = self.data_dir / f'forebet_tips_{date_str}.json'
        if not file_path.exists():
            raise FileNotFoundError(f"Tips file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def extract_preview_html(self, html_content: str) -> Optional[str]:
        """
        Extract preview HTML content from page HTML.
        Looks for content within <td class="contentmiddle"> and extracts <p> tags.

        Args:
            html_content: Raw HTML content from the page

        Returns:
            HTML string containing only the preview paragraphs, or None if not found
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find the content container
        # First, try <td class="contentmiddle">
        content_container = soup.find('td', class_='contentmiddle')
        
        # If not found, try other common containers
        if not content_container:
            content_container = soup.find('div', class_='contentmiddle')
        
        if not content_container:
            # Try to find main content area
            content_container = soup.find('div', {'id': 'content'}) or soup.find('article')
        
        # If still not found, use body as fallback
        if not content_container:
            content_container = soup.find('body')
        
        if not content_container:
            return None
        
        # Extract all <p> tags from the container
        paragraphs = content_container.find_all('p')
        
        if not paragraphs:
            return None
        
        # Build HTML string from paragraphs
        preview_html = ''
        for p in paragraphs:
            # Get the HTML content of the paragraph (preserving inner HTML)
            p_html = str(p)
            preview_html += p_html + '\n'
        
        return preview_html.strip()

    def scrape_preview(self, page: Page, preview_url: str) -> Optional[str]:
        """
        Scrape preview content from a preview URL.

        Args:
            page: Playwright page object
            preview_url: URL to the preview page

        Returns:
            HTML string containing preview paragraphs, or None if failed
        """
        try:
            # Navigate to preview page
            page.goto(preview_url, timeout=60000, wait_until="domcontentloaded")
            time.sleep(2)  # Wait for content to load
            
            # Get page HTML content
            html_content = page.content()
            
            # Extract preview HTML
            preview_html = self.extract_preview_html(html_content)
            
            return preview_html
            
        except Exception as e:
            print(f"  ✗ Error scraping preview from {preview_url}: {e}")
            return None

    def scrape_and_update(self, date_str: str, output_filename: Optional[str] = None) -> str:
        """
        Load tips, scrape previews, and save updated data.

        Args:
            date_str: Date string in YYYY-MM-DD format
            output_filename: Optional custom output filename. Defaults to forebet_tips_with_previews_YYYY-MM-DD.json

        Returns:
            Path to the saved output file
        """
        # Load tips
        tips = self.load_tips(date_str)
        
        # Filter tips that have preview links
        tips_with_previews = [tip for tip in tips if tip.get('preview_link')]
        
        if not tips_with_previews:
            print(f"No tips with preview links found for date {date_str}")
            # Still save the tips without previews
            if output_filename:
                output_path = self.data_dir / output_filename
            else:
                output_path = self.data_dir / f'forebet_tips_with_previews_{date_str}.json'
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(tips, f, indent=2, ensure_ascii=False)
            
            return str(output_path)
        
        print(f"Found {len(tips_with_previews)} tips with preview links")
        
        # Scrape previews using Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Create a dictionary to map match_id to preview HTML
                previews_dict = {}
                
                for i, tip in enumerate(tips_with_previews, 1):
                    preview_link = tip.get('preview_link')
                    match_id = tip.get('match_id')
                    home_team = tip.get('home_team', 'Unknown')
                    away_team = tip.get('away_team', 'Unknown')
                    
                    print(f"[{i}/{len(tips_with_previews)}] Scraping preview for {home_team} vs {away_team}...")
                    print(f"  URL: {preview_link}")
                    
                    preview_html = self.scrape_preview(page, preview_link)
                    
                    if preview_html:
                        previews_dict[match_id] = preview_html
                        print(f"  ✓ Preview scraped successfully ({len(preview_html)} characters)")
                    else:
                        print(f"  ✗ Failed to scrape preview")
                    
                    # Small delay between requests
                    time.sleep(1)
                
                # Update tips with preview HTML
                for tip in tips:
                    match_id = tip.get('match_id')
                    if match_id in previews_dict:
                        tip['preview_html'] = previews_dict[match_id]
                    else:
                        tip['preview_html'] = None
                
            finally:
                browser.close()
        
        # Determine output filename
        if output_filename:
            output_path = self.data_dir / output_filename
        else:
            output_path = self.data_dir / f'forebet_tips_with_previews_{date_str}.json'
        
        # Save updated tips
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tips, f, indent=2, ensure_ascii=False)
        
        return str(output_path)

