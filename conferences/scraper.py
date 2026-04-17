import asyncio
import re
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


def clean_markdown(text):
    """Remove markdown links and formatting from extracted text"""
    if not text:
        return ""
    # Remove markdown links [text](url) -> keep only text
    text = re.sub(r'\[([^\]]+)\]\([^\)]*\)', r'\1', text)
    # Remove markdown images ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
    # Remove any remaining ] or [ artifacts
    text = re.sub(r'[\]\[\(\)]', '', text)
    # Remove bold/italic markers
    text = re.sub(r'\*\*|\*|__|_', '', text)
    # Remove raw URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove "TECHNICAL SPONSORS" and footer text (common website junk)
    text = re.sub(r'TECHNICAL SPONSORS.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Home Sitemap.*', '', text, flags=re.IGNORECASE)
    # Clean whitespace
    text = ' '.join(text.split())
    return text.strip()


class ConferenceScraper:
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        self.run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for="css:body",
            remove_overlay_elements=True,
            word_count_threshold=10
        )
    
    async def scrape_url(self, url):
        """Scrape the university website and return raw content"""
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url=url,
                    config=self.run_config
                )
                
                if result.success:
                    return {
                        'status': 'success',
                        'url': url,
                        'markdown': result.markdown,
                        'html': result.html,
                        'title': result.metadata.get('title', 'Unknown'),
                    }
                else:
                    return {
                        'status': 'error',
                        'message': result.error_message,
                        'url': url
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'url': url
            }
    
    def extract_conference_info(self, content):
        """Extract structured conference data using patterns"""
        markdown = content.get('markdown', '')
        url = content.get('url', '')
        lines = [l.strip() for l in markdown.split('\n') if l.strip()]
        text = ' '.join(lines[:100])
        
        data = {
            'conference_name': '',
            'acronym': '',
            'year': '',
            'dates': '',
            'location': '',
            'website': url,
            'description': '',
            'submission_deadline': None,
            'notification_date': None,
            'topics': [],
            'organizers': []
        }
        
        # Extract Conference Name (cleaned)
        patterns = [
            r'(?:the\s+)?(\d+(?:st|nd|rd|th)\s+(?:International|National|IEEE)\s+Conference\s+(?:on|for)\s+[^[\n]{10,100})',
            r'(PAIS|ICSA|CSTEM|CISTEM|SPLAI|AIDH|CSA|COSI|EDIS|MCCSAI|ICSMACS|CoSI)\s+20\d{2}',
            r'(International|National)\s+(?:Conference|Symposium|Workshop)\s+on\s+[^[\n]{10,100}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(0).strip()
                if len(name) > 15:
                    # CLEAN THE NAME - remove markdown
                    data['conference_name'] = clean_markdown(name)
                    break
        
        # If still empty, try getting from first meaningful line
        if not data['conference_name']:
            for line in lines[:20]:
                cleaned = clean_markdown(line)
                if len(cleaned) > 20 and 'conference' in cleaned.lower():
                    data['conference_name'] = cleaned[:100]
                    break
        
        # Extract Acronym
        acronyms = re.findall(r'\b(PAIS|ICSA|CSTEM|CISTEM|SPLAI|AIDH|CSA|COSI|EDIS|MCCSAI|ICSMACS|CoSI)\b', text, re.IGNORECASE)
        if acronyms:
            data['acronym'] = acronyms[0].upper()
        
        # Extract Year
        year_match = re.search(r'20(2[4-9]|3[0-9])', text)
        if year_match:
            data['year'] = year_match.group(0)
        
                   # Extract Dates - IMPROVED
        dates_found = []
        
        # Pattern 1: Full month name + day + year (e.g., "May 12-14, 2026" or "May 12, 2026")
        pattern1 = re.findall(r'(?i)(?:january|february|march|april|may|june|july|august|september|october|november|december)[\s,]+(?:\d{1,2}(?:-\d{1,2})?[\s,]*)+20\d{2}', text)
        dates_found.extend(pattern1)
        
        # Pattern 2: Day + Month + Year (e.g., "12-14 May 2026")
        pattern2 = re.findall(r'(?i)\d{1,2}(?:-\d{1,2})?[\s,]+(?:january|february|march|april|may|june|july|august|september|october|november|december)[\s,]+20\d{2}', text)
        dates_found.extend(pattern2)
        
        # Pattern 3: Look in conference name specifically (e.g., "PAIS 2026, May 12-14")
        if data['conference_name']:
            name_date = re.search(r'(?i)(?:\d{1,2}[-])?(?:january|february|march|april|may|june|july|august|september|october|november|december)[\s,]+\d{1,2}(?:-\d{1,2})?,?[\s]*20\d{2}', data['conference_name'])
            if name_date:
                dates_found.append(name_date.group(0))
        
        # Pattern 4: Look for "Important Dates" or "Conference Dates" section in markdown
        if not dates_found:
            # Search for date sections
            date_section = re.search(r'(?i)(?:important dates|conference dates|date)[^\n]*\n(.*?)(?:\n\n|\Z)', markdown[:3000], re.DOTALL)
            if date_section:
                section_text = date_section.group(1)
                # Try to find any date in this section
                section_dates = re.findall(r'(?i)(?:january|february|march|april|may|june|july|august|september|october|november|december)[\s,]*\d{1,2}(?:-\d{1,2})?,?[\s]*20\d{2}', section_text)
                dates_found.extend(section_dates)
        
        # Clean and set the date
        if dates_found:
            # Take the first match and clean it
            raw_date = dates_found[0].strip()
            # Remove extra spaces
            data['dates'] = re.sub(r'\s+', ' ', raw_date)
        else:
            data['dates'] = ''

                   
        # Extract Location (Algerian cities)
        cities = ['alger', 'oran', 'constantine', 'annaba', 'blida', 'batna', 'djelfa', 'setif', 'biskra', 'bejaia', 'tlemcen', 'ouargla', 'tebessa', 'tizi ouzou', 'mostaganem', 'msila', 'medea', 'chlef', 'souk ahras', 'tipaza', 'mila', 'aflou', 'el oued']
        for city in cities:
            if city.lower() in text.lower():
                data['location'] = city.title() + ", Algeria"
                break
        
        # Extract Description (cleaned)
        for line in lines:
            if len(line) > 50 and not line.startswith('http'):
                cleaned = clean_markdown(line)
                if len(cleaned) > 50:
                    if any(word in cleaned.lower() for word in ['conference', 'international', 'research', 'paper', 'symposium']):
                        data['description'] = cleaned[:300]
                        break
        
        # Extract Topics (cleaned with junk filter)
        topics_match = re.search(r'(?i)(?:topics|tracks|themes)[\s:]+(.*?)(?:\n\n|\Z)', text, re.DOTALL)
        if topics_match:
            topics_text = topics_match.group(1)
            topics = re.findall(r'[•\-\*]\s*([^\n]+)', topics_text)
            
            # Filter out common menu/footer text
            junk_keywords = ['sponsor', 'home', 'sitemap', 'privacy policy', 'terms', 'ieee ethics', 
                           'facebook', 'twitter', 'linkedin', 'youtube', 'instagram', 'contact', 
                           'about us', 'login', 'register', 'copyright', 'all rights reserved']
            filtered_topics = []
            for t in topics:
                t_clean = clean_markdown(t)
                if len(t_clean) > 3 and not any(junk in t_clean.lower() for junk in junk_keywords):
                    filtered_topics.append(t_clean)
            
            data['topics'] = filtered_topics[:8]
        
        return data


def scrape_university_sync(url):
    """Run the async scraper"""
    scraper = ConferenceScraper()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(scraper.scrape_url(url))
        
        if result['status'] == 'success':
            data = scraper.extract_conference_info(result)
            return {
                'status': 'success',
                'data': data,
                'raw_markdown': result['markdown'][:2000]
            }
        else:
            return {
                'status': 'error',
                'message': result.get('message', 'Unknown error')
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
    finally:
        loop.close()
