print("DEBUG: Script starting...", flush=True)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import gspread
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime
import random
import os
import pickle
import urllib.parse
import json
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium_stealth import stealth

print("DEBUG: All imports completed successfully", flush=True)

class ResonanceRemainTracker:
    def __init__(self):
        print("DEBUG: Initializing tracker...", flush=True)
        self.credentials_file = "credentials_oauth.json"
        self.token_file = "token.pickle"
        self.spreadsheet_name = "Test resonance"
        self.guild_name = "Resonance Remain"
        self.driver = None

    def setup_cloud_credentials(self):
        print("DEBUG: Setting up cloud credentials...", flush=True)
        if 'GOOGLE_CREDENTIALS' in os.environ:
            try:
                credentials_data = json.loads(os.environ['GOOGLE_CREDENTIALS'])
                with open(self.credentials_file, 'w') as f:
                    json.dump(credentials_data, f)
                print("✅ Cloud credentials setup successful")
                return True
            except Exception as e:
                print(f"❌ Error setting up cloud credentials: {e}")
                return False
        
        if os.path.exists(self.credentials_file):
            print("✅ Local credentials file found")
            return True
        
        print("❌ No credentials found")
        return False

    def get_google_credentials(self):
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                  'https://www.googleapis.com/auth/drive']
        
        if not os.path.exists(self.credentials_file):
            print(f"❌ OAuth credentials file not found: {self.credentials_file}")
            raise FileNotFoundError(f"OAuth credentials file not found: {self.credentials_file}")
        
        creds = None
        
        if os.path.exists(self.token_file):
            print("🔍 Loading stored credentials...")
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                print("✅ Loaded existing authentication token")
                
                if creds.expired and creds.refresh_token:
                    print("🔄 Refreshing expired credentials...")
                    try:
                        creds.refresh(Request())
                        print("✅ Successfully refreshed credentials")
                        
                        with open(self.token_file, 'wb') as token:
                            pickle.dump(creds, token)
                        print("💾 Saved refreshed credentials")
                        
                    except Exception as e:
                        print(f"❌ Failed to refresh credentials: {e}")
                        creds = None
                
                if creds and creds.valid:
                    print("✅ Using existing valid credentials")
                    return creds
                    
            except Exception as e:
                print(f"⚠️  Could not load stored token: {e}")
                creds = None
        
        if not os.environ.get('GITHUB_ACTIONS'):
            print("🔐 Starting OAuth authentication...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=8080, open_browser=True)
                print("✅ Authentication successful!")
                
                print("💾 Saving credentials for future use...")
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                print("✅ Credentials saved successfully")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                raise
        else:
            print("❌ No valid token found in GitHub Actions environment")
            print("💡 Please run the script locally first to generate token.pickle")
            raise Exception("Pre-authorized token required for GitHub Actions")
        
        return creds

    def validate_setup(self):
        print("🔍 Validating setup...")
        
        issues = []
        
        if not os.path.exists(self.credentials_file):
            issues.append(f"❌ OAuth credentials file missing: {self.credentials_file}")
        else:
            print("✅ OAuth credentials file found")
        
        try:
            import google_auth_oauthlib
            print("✅ google-auth-oauthlib package installed")
        except ImportError:
            issues.append("❌ Missing package: google-auth-oauthlib")
        
        try:
            import gspread
            print("✅ gspread package available")
        except ImportError:
            issues.append("❌ Missing package: gspread")
        
        if issues:
            print("\n🚨 Setup Issues Found:")
            for issue in issues:
                print(issue)
            return False
        else:
            print("✅ Setup validation passed!")
            return True

    def setup_driver(self):
        """Setup undetected Chrome driver with maximum stealth"""
        print("DEBUG: Setting up undetected Chrome driver...", flush=True)
        
        try:
            # Use undetected Chrome (specifically designed to bypass Cloudflare)
            options = uc.ChromeOptions()
            
            # Basic options for GitHub Actions
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Create undetected Chrome instance
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Apply additional stealth
            stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
            
            print("✅ Undetected Chrome driver setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up undetected Chrome driver: {e}")
            print("🔄 Falling back to regular Chrome...")
            
            # Fallback to regular Chrome if undetected fails
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                print("✅ Fallback Chrome driver setup successful")
                return True
                
            except Exception as fallback_error:
                print(f"❌ Fallback Chrome driver also failed: {fallback_error}")
                return False

    def scrape_with_requests(self):
        print("DEBUG: Starting requests-based scraping...", flush=True)
        guild_name_encoded = urllib.parse.quote_plus(self.guild_name)
        url = f"https://rubinot.com.br/?subtopic=guilds&page=view&GuildName={guild_name_encoded}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
        try:
            print(f"🌐 Requesting {self.guild_name} guild page with requests...")
            print(f"🔗 URL: {url}")
            
            time.sleep(2)
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                print("✅ Successfully fetched page with requests")
                
                if "cloudflare" in response.text.lower() or "attention required" in response.text.lower():
                    print("❌ Cloudflare challenge detected in requests response")
                    return []
                
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.find_all('table')
                print(f"🔍 Found {len(tables)} tables in the page")
                
                # For now, let's just return a test member to see if the flow works
                test_data = [{
                    'Rank': 'Leader',
                    'Name': 'Test Member',
                    'Title': '',
                    'Vocation': 'Elite Knight',
                    'Level': '100',
                    'Joining Date': 'Jan 01 2025'
                }]
                print(f"✅ Returning test data with {len(test_data)} members")
                return test_data
                
            else:
                print(f"❌ HTTP {response.status_code}: {response.reason}")
                return []
                
        except Exception as e:
            print(f"❌ Error with requests method: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_with_selenium(self):
        """Enhanced Selenium-based scraping with undetected Chrome"""
        print("DEBUG: Starting undetected selenium-based scraping...", flush=True)
        
        if not self.setup_driver():
            return []
        
        try:
            guild_name_encoded = urllib.parse.quote_plus(self.guild_name)
            url = f"https://rubinot.com.br/?subtopic=guilds&page=view&GuildName={guild_name_encoded}"
            
            print(f"🌐 Navigating to {self.guild_name} guild page with Undetected Chrome...")
            print(f"🔗 URL: {url}")
            
            # Human-like delay before navigation
            time.sleep(random.uniform(2, 5))
            
            self.driver.get(url)
            
            # Extended wait for Cloudflare with better detection
            max_wait = 90  # Wait up to 90 seconds
            start_time = time.time()
            cloudflare_detected = False
            
            while time.time() - start_time < max_wait:
                try:
                    page_title = self.driver.title.lower()
                    page_source = self.driver.page_source.lower()
                    
                    print(f"📄 Current page title: {self.driver.title}")
                    
                    # Check for Cloudflare indicators
                    cloudflare_indicators = [
                        "cloudflare", "attention required", "checking your browser",
                        "ray id", "please wait", "verifying you are human"
                    ]
                    
                    is_cloudflare = any(indicator in page_title or indicator in page_source 
                                      for indicator in cloudflare_indicators)
                    
                    if is_cloudflare:
                        if not cloudflare_detected:
                            print("🔄 Cloudflare challenge detected, waiting for bypass...")
                            cloudflare_detected = True
                        
                        elapsed = int(time.time() - start_time)
                        print(f"⏳ Waiting for Cloudflare bypass... ({elapsed}s)")
                        time.sleep(5)
                        continue
                    
                    # Check for successful access
                    if any(keyword in page_source for keyword in ["tibia", "guild", "members", "level"]):
                        print("✅ Successfully bypassed Cloudflare and accessed guild page!")
                        break
                    
                    # If we're not on Cloudflare but also don't see expected content
                    elapsed = int(time.time() - start_time)
                    if elapsed > 30:  # Give it at least 30 seconds
                        print("⚠️  Page loaded but content unclear, proceeding...")
                        break
                        
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"⚠️  Error checking page status: {e}")
                    time.sleep(5)
            
            # Final status check
            final_title = self.driver.title
            final_source = self.driver.page_source.lower()
            
            print(f"📄 Final page title: {final_title}")
            
            # Check if we're still blocked
            if any(indicator in final_source for indicator in ["cloudflare", "attention required"]):
                print("❌ Still blocked by Cloudflare after 90 seconds")
                return []
            
            if "blocked" in final_source or "forbidden" in final_source:
                print("❌ Access blocked by website")
                return []
            
            if "guild not found" in final_source:
                print("❌ Guild not found")
                return []
            
            print("✅ Successfully accessed guild page with Undetected Chrome")
            
            # For now, return test data to confirm it works
            test_data = [{
                'Rank': 'Leader',
                'Name': 'Undetected Chrome Success',
                'Title': '',
                'Vocation': 'Elite Knight',
                'Level': '500',
                'Joining Date': 'Jan 01 2025'
            }]
            print(f"✅ Returning test data with {len(test_data)} members")
            return test_data
            
        except Exception as e:
            print(f"❌ Error with undetected selenium method: {e}")
            import traceback
            traceback.print_exc()
            return []
        
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def update_spreadsheet(self, guild_data):
        print(f"📊 Connecting to Google Sheets for {self.guild_name}...")
        
        try:
            creds = self.get_google_credentials()
            client = gspread.authorize(creds)
            
            try:
                spreadsheet = client.open(self.spreadsheet_name)
                print(f"✅ Opened existing spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(self.spreadsheet_name)
                print(f"✅ Created new spreadsheet: {self.spreadsheet_name}")
            
            sheet_name = "Resonance_Remain"
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"✅ Found existing {sheet_name} worksheet")
            except gspread.WorksheetNotFound:
                print(f"🆕 Creating new {sheet_name} worksheet")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=30)
            
            # Simple update for testing
            current_datetime = datetime.now()
            headers = ['Rank', 'Name', 'Title', 'Vocation', 'Level', 'Joining Date', f'Level_{current_datetime.strftime("%d/%m/%Y_%H:%M:%S")}']
            
            # Convert guild data to rows
            rows = [headers]
            for member in guild_data:
                row = [
                    member.get('Rank', ''),
                    member.get('Name', ''),
                    member.get('Title', ''),
                    member.get('Vocation', ''),
                    member.get('Level', ''),
                    member.get('Joining Date', ''),
                    member.get('Level', '')  # Same level in timestamp column
                ]
                rows.append(row)
            
            worksheet.clear()
            worksheet.update(values=rows, range_name='A1')
            
            print(f"✅ Successfully updated {self.guild_name}")
            print(f"📊 Spreadsheet URL: {spreadsheet.url}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating {self.guild_name} spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            return False

    def check_google_permissions(self):
        try:
            creds = self.get_google_credentials()
            client = gspread.authorize(creds)
            
            files = client.list_spreadsheet_files()
            print(f"✅ Can access Drive - found {len(files)} spreadsheets")
            return True
                
        except Exception as e:
            print(f"❌ OAuth check failed: {e}")
            return False

    def run(self):
        print("DEBUG: Starting run method...", flush=True)
        print("🚀 Resonance Remain Guild Tracker Starting...")
        print("🎯 Target: Resonance Remain Guild")
        print("=" * 50)
        
        print("🔐 Step 0: Setting up cloud credentials...")
        if not self.setup_cloud_credentials():
            print("❌ Failed to setup credentials")
            return
        
        print("\n🔧 Step 1: Validating setup...")
        if not self.validate_setup():
            print("\n❌ Please fix the setup issues above")
            return
        
        print("\n🔍 Step 2: Checking Google OAuth authentication...")
        try:
            if not self.check_google_permissions():
                print("❌ Google OAuth has issues")
                return
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return
        
        print("\n🎯 Step 3: Starting guild data collection...")
        
        # Try requests first, then Selenium
        approaches = [
            ("Requests", self.scrape_with_requests),
            ("Undetected Selenium", self.scrape_with_selenium)
        ]
        
        for approach_name, approach_method in approaches:
            print(f"\n🎯 Trying approach: {approach_name}")
            
            try:
                guild_data = approach_method()
                
                if guild_data:
                    print(f"✅ {approach_name} succeeded!")
                    if self.update_spreadsheet(guild_data):
                        print(f"📊 Successfully updated spreadsheet with {len(guild_data)} members")
                        print(f"\n🎉 RESONANCE REMAIN GUILD TRACKER COMPLETED SUCCESSFULLY!")
                        return
                    else:
                        print("❌ Spreadsheet update failed")
                else:
                    print(f"❌ {approach_name} failed - no data retrieved")
                    
            except Exception as e:
                print(f"❌ {approach_name} failed with error: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(3)  # Small delay between approaches
        
        print(f"\n❌ ALL APPROACHES FAILED")

print("DEBUG: Class definition complete, starting main block...", flush=True)

if __name__ == "__main__":
    print("DEBUG: Reached main block", flush=True)
    
    print("🔥 STARTING RESONANCE REMAIN GUILD TRACKER...", flush=True)
    print("📅 Date:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), flush=True)
    print("🌍 Environment:", "GitHub Actions" if os.environ.get('GITHUB_ACTIONS') else "Local", flush=True)
    print("-" * 50, flush=True)
    
    try:
        print("DEBUG: Creating tracker instance...", flush=True)
        tracker = ResonanceRemainTracker()
        print("✅ Resonance Remain tracker initialized successfully", flush=True)
        
        print("DEBUG: Starting tracker.run()...", flush=True)
        tracker.run()
        print("DEBUG: tracker.run() completed", flush=True)
        
    except Exception as e:
        print(f"❌ Critical error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        exit(1)
    
    print("\n🏁 Resonance Remain tracker execution completed", flush=True)
    
    if not os.environ.get('GITHUB_ACTIONS'):
        input("Press Enter to exit...")
