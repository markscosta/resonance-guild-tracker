print("DEBUG: Script starting...", flush=True)

try:
    from selenium import webdriver
    print("DEBUG: Selenium imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Selenium import failed: {e}", flush=True)

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    print("DEBUG: Selenium components imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Selenium components import failed: {e}", flush=True)

try:
    import time
    import gspread
    import pandas as pd
    print("DEBUG: Basic packages imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Basic packages import failed: {e}", flush=True)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    print("DEBUG: Google auth packages imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Google auth packages import failed: {e}", flush=True)

try:
    from datetime import datetime
    import random
    import os
    import pickle
    import urllib.parse
    import json
    print("DEBUG: Standard library packages imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Standard library packages import failed: {e}", flush=True)

try:
    import requests
    from bs4 import BeautifulSoup
    print("DEBUG: Requests and BeautifulSoup imported successfully", flush=True)
except Exception as e:
    print(f"DEBUG: Requests/BeautifulSoup import failed: {e}", flush=True)

print("DEBUG: All imports completed, defining class...", flush=True)

class ResonanceRemainTracker:
    def __init__(self):
        print("DEBUG: Initializing ResonanceRemainTracker...", flush=True)
        # Use relative paths for cloud deployment
        self.credentials_file = "credentials_oauth.json"
        self.token_file = "token.pickle"
        self.spreadsheet_name = "Test resonance"
        self.guild_name = "Resonance Remain"
        self.driver = None
        print("DEBUG: ResonanceRemainTracker initialization complete", flush=True)

    def setup_cloud_credentials(self):
        """Setup credentials for cloud deployment"""
        print("DEBUG: Setting up cloud credentials...", flush=True)
        # Check if credentials are provided as environment variable (GitHub Actions)
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
        
        # If running locally, check if file exists
        if os.path.exists(self.credentials_file):
            print("✅ Local credentials file found")
            return True
        
        print("❌ No credentials found (neither environment variable nor local file)")
        return False

    def get_google_credentials(self):
        """Get Google credentials using OAuth flow - Cloud compatible with enhanced token handling"""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
                  'https://www.googleapis.com/auth/drive']
        
        if not os.path.exists(self.credentials_file):
            print(f"❌ OAuth credentials file not found: {self.credentials_file}")
            raise FileNotFoundError(f"OAuth credentials file not found: {self.credentials_file}")
        
        creds = None
        
        # Try to load existing token FIRST (for GitHub Actions)
        if os.path.exists(self.token_file):
            print("🔍 Loading stored credentials...")
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                print("✅ Loaded existing authentication token")
                
                # If credentials are expired but have refresh token, try to refresh
                if creds.expired and creds.refresh_token:
                    print("🔄 Refreshing expired credentials...")
                    try:
                        creds.refresh(Request())
                        print("✅ Successfully refreshed credentials")
                        
                        # Save refreshed credentials
                        with open(self.token_file, 'wb') as token:
                            pickle.dump(creds, token)
                        print("💾 Saved refreshed credentials")
                        
                    except Exception as e:
                        print(f"❌ Failed to refresh credentials: {e}")
                        creds = None
                
                # If we have valid credentials, return them
                if creds and creds.valid:
                    print("✅ Using existing valid credentials")
                    return creds
                    
            except Exception as e:
                print(f"⚠️  Could not load stored token: {e}")
                creds = None
        
        # Only try interactive OAuth if not in GitHub Actions
        if not os.environ.get('GITHUB_ACTIONS'):
            print("🔐 Starting OAuth authentication...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=8080, open_browser=True)
                print("✅ Authentication successful!")
                
                # Save credentials for future use
                print("💾 Saving credentials for future use...")
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                print("✅ Credentials saved successfully")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                raise
        else:
            # In GitHub Actions, we MUST have a pre-existing token
            print("❌ No valid token found in GitHub Actions environment")
            print("💡 Please run the script locally first to generate token.pickle")
            raise Exception("Pre-authorized token required for GitHub Actions")
        
        return creds

    def validate_setup(self):
        """Validate that all required files and dependencies are in place"""
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
        """Setup Chrome driver with optimized stealth"""
        print("DEBUG: Setting up Chrome driver...", flush=True)
        chrome_options = Options()
        
        # Basic headless setup
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1366,768")
        
        # Essential stealth options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Performance optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        
        # Language settings
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en-US,en;q=0.9',
            'profile.managed_default_content_settings.images': 2  # Disable images for speed
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Essential stealth scripts only
            essential_scripts = [
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
            ]
            
            for script in essential_scripts:
                try:
                    self.driver.execute_script(script)
                except:
                    pass
            
            print("✅ Chrome driver setup successful (optimized stealth mode)")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Chrome driver: {e}")
            return False

    def wait_for_cloudflare(self, max_wait=30):
        """Faster Cloudflare detection"""
        print("⏳ Waiting for Cloudflare challenge to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                page_title = self.driver.title.lower()
                page_source = self.driver.page_source.lower()
                
                # Quick Cloudflare detection
                cloudflare_indicators = [
                    "attention required",
                    "cloudflare", 
                    "checking your browser",
                    "ray id"
                ]
                
                is_cloudflare = any(indicator in page_source or indicator in page_title for indicator in cloudflare_indicators)
                
                if is_cloudflare:
                    elapsed = int(time.time() - start_time)
                    print(f"🔄 Cloudflare active... ({elapsed}s)")
                    time.sleep(2)
                else:
                    print("✅ Cloudflare challenge completed!")
                    print(f"📄 Page title: {self.driver.title}")
                    return True
                    
            except Exception as e:
                print(f"⚠️  Error: {e}")
                time.sleep(2)
        
        print(f"❌ Cloudflare timeout after {max_wait}s")
        print(f"📄 Final page title: {self.driver.title}")
        return False

    def scrape_with_requests(self):
        """Alternative scraping using requests instead of Selenium"""
        print("DEBUG: Starting requests-based scraping...", flush=True)
        guild_name_encoded = urllib.parse.quote_plus(self.guild_name)
        url = f"https://rubinot.com.br/?subtopic=guilds&page=view&GuildName={guild_name_encoded}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        try:
            print(f"🌐 Requesting {self.guild_name} guild page with requests...")
            print(f"🔗 URL: {url}")
            
            # Add random delay
            time.sleep(random.uniform(1, 3))
            
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                print("✅ Successfully fetched page with requests")
                
                # Check if we got Cloudflare challenge
                if "cloudflare" in response.text.lower() or "attention required" in response.text.lower():
                    print("❌ Cloudflare challenge detected in requests response")
                    return []
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for tables
                tables = soup.find_all('table')
                print(f"🔍 Found {len(tables)} tables in the page")
                
                for i, table in enumerate(tables):
                    # Check if this looks like a guild members table
                    headers = [th.get_text().strip() for th in table.find_all('th')]
                    if not headers:
                        first_row = table.find('tr')
                        if first_row:
                            headers = [td.get_text().strip() for td in first_row.find_all('td')]
                    
                    header_text = ' '.join(headers).lower()
                    print(f"Table {i+1} headers: {headers}")
                    
                    if any(keyword in header_text for keyword in ['rank', 'name', 'level', 'vocation']):
                        print(f"✅ Found members table in table {i+1}")
                        
                        # Extract table text
                        table_text = table.get_text('\n', strip=True)
                        members_data = self.parse_guild_data(table_text)
                        print(f"✅ Parsed {len(members_data)} members with requests method")
                        return members_data
                
                print("❌ No members table found in requests response")
                return []
                
            else:
                print(f"❌ HTTP {response.status_code}: {response.reason}")
                return []
                
        except Exception as e:
            print(f"❌ Error with requests method: {e}")
            import traceback
            traceback.print_exc()
            return []

    def scrape_guild_data(self):
        """Faster scraping with minimal delays"""
        guild_name_encoded = urllib.parse.quote_plus(self.guild_name)
        url = f"https://rubinot.com.br/?subtopic=guilds&page=view&GuildName={guild_name_encoded}"
        
        try:
            print(f"🌐 Navigating to {self.guild_name} guild page...")
            print(f"🔗 URL: {url}")
            
            # Minimal delay
            time.sleep(1)
            
            self.driver.get(url)
            
            # Shorter Cloudflare wait
            if not self.wait_for_cloudflare(max_wait=30):
                print("❌ Cloudflare challenge failed")
                return []
            
            # Shorter wait after Cloudflare
            time.sleep(2)
            
            page_title = self.driver.title
            print(f"📄 Page title: {page_title}")
            
            page_source = self.driver.page_source.lower()
            if "blocked" in page_source or "sorry" in page_source:
                print(f"❌ BLOCKED while accessing {self.guild_name}!")
                return []
            
            if "guild not found" in page_source or "no guild" in page_source:
                print(f"❌ Guild '{self.guild_name}' not found!")
                return []
            
            print(f"✅ Successfully accessed {self.guild_name} page")
            
            # Check for guild name variations
            guild_variations = [
                self.guild_name.lower(),
                self.guild_name.lower().replace(" ", ""),
                "resonance remain",
                "resonanceremain"
            ]
            
            found_guild = False
            for variation in guild_variations:
                if variation in page_source:
                    print(f"✅ Confirmed we're on {self.guild_name} guild page (found: {variation})")
                    found_guild = True
                    break
            
            if not found_guild:
                print(f"⚠️  Guild name variations not found in page content - proceeding anyway")
            
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"🔍 Found {len(tables)} tables on the page")
            
            for i, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    if len(rows) < 2:
                        continue
                    
                    header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                    
                    headers = [cell.text.strip() for cell in header_cells]
                    header_text = ' '.join(headers).lower()
                    
                    print(f"Table {i+1} headers: {headers}")
                    
                    if any(keyword in header_text for keyword in ['rank', 'name', 'level', 'vocation']):
                        print(f"✅ Found members table for {self.guild_name} in table {i+1}")
                        raw_text = table.text
                        
                        members_data = self.parse_guild_data(raw_text)
                        print(f"✅ Parsed {len(members_data)} members from {self.guild_name}")
                        return members_data
                        
                except Exception as e:
                    print(f"Error processing table {i+1}: {e}")
                    continue
            
            print(f"❌ No members table found for {self.guild_name}")
            return []
            
        except Exception as e:
            print(f"❌ Error during scraping {self.guild_name}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def parse_guild_data(self, raw_text):
        """Parse guild data from table text - ENHANCED RANK DETECTION"""
        lines = raw_text.strip().split('\n')
        members_data = []
        
        ranks = ['Leader', 'Vice Leader', 'Officer', 'High Member', 'Member']
        vocations = ['Elite Knight', 'Master Sorcerer', 'Elder Druid', 'Royal Paladin', 'Exalted Monk']
        
        print(f"🔍 PARSING GUILD DATA - {len(lines)} total lines")
        
        current_rank = ""
        member_lines = []
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean or i == 0:
                continue
            
            if line_clean in ranks:
                current_rank = line_clean
                print(f"         >>> RANK SECTION: {current_rank}")
                continue
            
            line_rank = None
            for rank in ranks:
                if line_clean.startswith(rank + ' '):
                    line_rank = rank
                    current_rank = rank
                    print(f"         >>> INLINE RANK: {rank}")
                    break
            
            has_vocation = any(voc in line_clean for voc in vocations)
            has_level = any(part.isdigit() and len(part) >= 2 for part in line_clean.split())
            
            if has_vocation or has_level:
                assigned_rank = line_rank or current_rank
                if not assigned_rank:
                    member_count = len(member_lines)
                    if member_count < 2:
                        assigned_rank = "Leader"
                    elif member_count < 8:
                        assigned_rank = "Vice Leader"
                    elif member_count < 15:
                        assigned_rank = "Officer"
                    elif member_count < 30:
                        assigned_rank = "High Member"
                    else:
                        assigned_rank = "Member"
                
                member_lines.append((i, line_clean, assigned_rank))
        
        print(f"\n📊 Found {len(member_lines)} potential member lines")
        
        for line_idx, line_content, member_rank in member_lines:
            if not member_rank:
                continue
                
            member_data = self.extract_member_data(line_content, member_rank)
            if member_data:
                members_data.append(member_data)
        
        rank_counts = {}
        for member in members_data:
            rank = member['Rank']
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        print(f"\n📊 FINAL RANK DISTRIBUTION:")
        for rank in ranks:
            count = rank_counts.get(rank, 0)
            print(f"   {rank}: {count} members")
        
        return members_data

    def extract_member_data(self, line_content, member_rank):
        """Extract member data from a single line"""
        vocations = ['Elite Knight', 'Master Sorcerer', 'Elder Druid', 'Royal Paladin', 'Exalted Monk']
        
        clean_line = line_content
        if clean_line.startswith(member_rank + ' '):
            clean_line = clean_line[len(member_rank):].strip()
        
        parts = clean_line.split()
        if len(parts) < 4:
            return None
        
        vocation = ""
        vocation_index = -1
        
        for i, part in enumerate(parts):
            for v in vocations:
                vocation_parts = v.split()
                if i + len(vocation_parts) <= len(parts):
                    potential_vocation = ' '.join(parts[i:i+len(vocation_parts)])
                    if potential_vocation == v:
                        vocation = v
                        vocation_index = i
                        break
            if vocation:
                break
        
        if not vocation:
            return None
        
        name = ' '.join(parts[:vocation_index]).strip()
        if not name:
            return None
        
        remaining_parts = parts[vocation_index + len(vocation.split()):]
        
        level = ""
        for part in remaining_parts:
            if part.isdigit():
                level = part
                break
        
        joining_date = ""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i, part in enumerate(remaining_parts):
            if part in months and i + 2 < len(remaining_parts):
                joining_date = f"{part} {remaining_parts[i+1]} {remaining_parts[i+2]}"
                break
        
        return {
            'Rank': member_rank,
            'Name': name,
            'Title': "",
            'Vocation': vocation,
            'Level': level,
            'Joining Date': joining_date
        }

    def get_or_create_sairam_worksheet(self, spreadsheet):
        """Get or create the sairam worksheet for ex-members"""
        sheet_name = "sairam"
        
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            print(f"✅ Found existing {sheet_name} worksheet")
            return worksheet
        except gspread.WorksheetNotFound:
            print(f"🆕 Creating new {sheet_name} worksheet")
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=30)
            
            # Set up headers for sairam tab
            headers = ['Rank', 'Name', 'Title', 'Vocation', 'Level', 'Joining Date', 'Left Date', 'Reason']
            worksheet.update(values=[headers], range_name='A1')
            print(f"✅ Set up headers for {sheet_name} worksheet")
            return worksheet

    def move_left_members_to_sairam(self, spreadsheet, left_members):
        """Move members who left the guild to the sairam tab"""
        if not left_members:
            print("📊 No members left the guild this time")
            return True
        
        try:
            sairam_worksheet = self.get_or_create_sairam_worksheet(spreadsheet)
            
            # Get existing sairam data to avoid duplicates
            existing_sairam_data = sairam_worksheet.get_all_values()
            existing_sairam_names = set()
            
            if len(existing_sairam_data) > 1:  # Skip header row
                for row in existing_sairam_data[1:]:
                    if len(row) > 1 and row[1]:  # Check if Name column has value
                        existing_sairam_names.add(row[1].strip())
            
            # Prepare new rows for sairam tab
            new_sairam_rows = []
            current_date = datetime.now().strftime("%d/%m/%Y")
            
            for member_data in left_members:
                member_name = member_data[1]  # Name is in column B (index 1)
                
                # Skip if already in sairam tab
                if member_name in existing_sairam_names:
                    print(f"   ⚠️  {member_name} already in sairam tab, skipping")
                    continue
                
                # Create new row for sairam tab
                sairam_row = member_data[:6]  # First 6 columns (Rank, Name, Title, Vocation, Level, Joining Date)
                sairam_row.append(current_date)  # Left Date
                sairam_row.append("Left Guild")   # Reason
                
                new_sairam_rows.append(sairam_row)
                print(f"   ➡️  Moving {member_name} to sairam tab")
            
            # Add new rows to sairam tab
            if new_sairam_rows:
                # Find the next empty row in sairam tab
                next_row = len(existing_sairam_data) + 1
                
                # Update sairam worksheet with new data
                for i, row in enumerate(new_sairam_rows):
                    row_range = f'A{next_row + i}:H{next_row + i}'
                    sairam_worksheet.update(values=[row], range_name=row_range)
                
                print(f"✅ Moved {len(new_sairam_rows)} members to sairam tab")
            
            return True
            
        except Exception as e:
            print(f"❌ Error moving members to sairam tab: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_spreadsheet(self, guild_data):
        """Update Resonance Remain tab in spreadsheet with level tracking and timestamp"""
        try:
            print(f"📊 Connecting to Google Sheets for {self.guild_name}...")
            
            creds = self.get_google_credentials()
            client = gspread.authorize(creds)
            
            try:
                spreadsheet = client.open(self.spreadsheet_name)
                print(f"✅ Opened existing spreadsheet: {self.spreadsheet_name}")
            except gspread.SpreadsheetNotFound:
                spreadsheet = client.create(self.spreadsheet_name)
                print(f"✅ Created new spreadsheet: {self.spreadsheet_name}")
            
            # Use a sheet-safe name (Google Sheets has character limits)
            sheet_name = "Resonance_Remain"
            
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                print(f"✅ Found existing {sheet_name} worksheet")
                existing_sheet = True
            except gspread.WorksheetNotFound:
                print(f"🆕 Creating new {sheet_name} worksheet")
                worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=500, cols=30)
                existing_sheet = False
            
            # Create timestamp for new level column
            current_datetime = datetime.now()
            current_date = current_datetime.strftime("%d/%m/%Y")
            current_time = current_datetime.strftime("%H:%M:%S")
            level_column_name = f"Level_{current_date}_{current_time}"
            
            print(f"📅 New level column: {level_column_name}")
            
            # Get existing data if sheet exists
            existing_data = {}
            existing_headers = []
            
            if existing_sheet:
                try:
                    all_values = worksheet.get_all_values()
                    if all_values:
                        existing_headers = all_values[0]
                        print(f"📋 Found existing headers: {existing_headers}")
                        
                        # Create lookup for existing members
                        for row in all_values[1:]:  # Skip header row
                            if len(row) > 1 and row[1]:  # Check if Name column (B) has value
                                name = row[1].strip()
                                existing_data[name] = row
                        
                        print(f"📊 Found {len(existing_data)} existing members in sheet")
                except Exception as e:
                    print(f"⚠️  Could not read existing data: {e}")
                    existing_data = {}
                    existing_headers = []
            
            # Build new data structure
            print(f"📋 Processing {len(guild_data)} scraped members...")
            
            # Define base headers (fixed columns A-F)
            base_headers = ['Rank', 'Name', 'Title', 'Vocation', 'Level', 'Joining Date']
            
            # Determine all headers (base + existing level columns + new level column)
            all_headers = base_headers.copy()
            
            # Add existing level columns (skip base headers)
            for header in existing_headers:
                if header.startswith('Level_') and header not in all_headers:
                    all_headers.append(header)
            
            # Add new level column
            if level_column_name not in all_headers:
                all_headers.append(level_column_name)
            
            print(f"📊 Final headers: {all_headers}")
            
            # Build member rows and identify members who left
            final_rows = []
            new_members_count = 0
            updated_members_count = 0
            current_member_names = set()
            left_members = []
            
            # Process current guild members
            for member in guild_data:
                name = member['Name'].strip()
                current_level = member.get('Level', '')
