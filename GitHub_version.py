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

class ResonanceRemainTracker:
    def __init__(self):
        # Use relative paths for cloud deployment
        self.credentials_file = "credentials_oauth.json"
        self.token_file = "token.pickle"
        self.spreadsheet_name = "Test resonance"
        self.guild_name = "Resonance Remain"
        self.driver = None

    def setup_cloud_credentials(self):
        """Setup credentials for cloud deployment"""
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
                current_member_names.add(name)
                
                # Check if member exists
                if name in existing_data:
                    # Existing member - preserve existing data and add new level
                    existing_row = existing_data[name]
                    updated_members_count += 1
                    
                    # Build new row with existing data
                    new_row = [''] * len(all_headers)
                    
                    # Copy existing data up to the length we have
                    for i, value in enumerate(existing_row):
                        if i < len(all_headers):
                            new_row[i] = value
                    
                    # Update basic info (might have changed)
                    new_row[0] = member.get('Rank', '')      # A: Rank
                    new_row[1] = name                         # B: Name
                    new_row[2] = member.get('Title', '')      # C: Title
                    new_row[3] = member.get('Vocation', '')   # D: Vocation
                    # Column E (Level) is preserved from existing data
                    new_row[5] = member.get('Joining Date', '') # F: Joining Date
                    
                    # Add current level to new timestamp column
                    new_level_col_index = all_headers.index(level_column_name)
                    new_row[new_level_col_index] = current_level
                    
                    print(f"   ✅ Updated existing member: {name} (Level: {current_level})")
                    
                else:
                    # New member - set starting level in column E and new column
                    new_members_count += 1
                    
                    new_row = [''] * len(all_headers)
                    new_row[0] = member.get('Rank', '')       # A: Rank
                    new_row[1] = name                         # B: Name
                    new_row[2] = member.get('Title', '')      # C: Title
                    new_row[3] = member.get('Vocation', '')   # D: Vocation
                    new_row[4] = current_level                # E: Level (starting level)
                    new_row[5] = member.get('Joining Date', '') # F: Joining Date
                    
                    # Add current level to new timestamp column as well
                    new_level_col_index = all_headers.index(level_column_name)
                    new_row[new_level_col_index] = current_level
                    
                    print(f"   🆕 New member: {name} (Starting Level: {current_level})")
                
                final_rows.append(new_row)
            
            # Identify members who left (were in existing data but not in current scrape)
            for existing_name, existing_row in existing_data.items():
                if existing_name not in current_member_names:
                    # This member left the guild - add to left_members list
                    left_members.append(existing_row)
                    print(f"   ⬅️  Member left guild: {existing_name}")
            
            # Move left members to sairam tab
            if left_members:
                print(f"\n📤 Moving {len(left_members)} left members to sairam tab...")
                self.move_left_members_to_sairam(spreadsheet, left_members)
            
            # Prepare final data for upload (only current guild members)
            all_values = [all_headers] + final_rows
            
            print(f"📊 Summary:")
            print(f"   🆕 New members: {new_members_count}")
            print(f"   ✅ Updated members: {updated_members_count}")
            print(f"   ⬅️  Left members (moved to sairam): {len(left_members)}")
            print(f"   📊 Active guild members: {len(final_rows)}")
            print(f"   📋 Total columns: {len(all_headers)}")
            
            # Clear and upload
            print(f"📤 Uploading data to {sheet_name} tab...")
            worksheet.clear()
            
            # Upload in chunks if needed
            try:
                worksheet.update(values=all_values, range_name='A1')
                print("✅ Successfully uploaded data")
            except Exception as upload_error:
                print(f"⚠️  Direct upload failed: {upload_error}")
                print("🔄 Trying chunked upload...")
                
                # Upload headers first
                worksheet.update(values=[all_headers], range_name='A1')
                
                # Upload data in chunks of 100 rows
                chunk_size = 100
                for i in range(0, len(final_rows), chunk_size):
                    chunk = final_rows[i:i + chunk_size]
                    start_row = i + 2  # +2 because row 1 is headers and sheets are 1-indexed
                    end_row = start_row + len(chunk) - 1
                    range_name = f'A{start_row}:{chr(ord("A") + len(all_headers) - 1)}{end_row}'
                    
                    worksheet.update(values=chunk, range_name=range_name)
                    print(f"📤 Uploaded chunk {i//chunk_size + 1}: rows {start_row}-{end_row}")
                
                print("✅ Successfully uploaded all data in chunks")
            
            # Add timestamp in a separate area
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            try:
                # Put timestamp in the row below the last column
                timestamp_col = chr(ord('A') + len(all_headers) + 1) if len(all_headers) < 25 else "Z"
                worksheet.update(values=[[f'Last Updated: {timestamp}']], range_name=f'{timestamp_col}1')
                print("🕒 Added timestamp")
            except:
                print("⚠️  Could not add timestamp (non-critical)")
            
            print(f"✅ Successfully updated {self.guild_name}")
            print(f"📊 Spreadsheet URL: {spreadsheet.url}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating {self.guild_name} spreadsheet: {e}")
            import traceback
            traceback.print_exc()
            
            # Save locally as backup
            print(f"\n💾 Saving data locally as backup...")
            return self.save_data_locally(guild_data)

    def save_data_locally(self, guild_data):
        """Save data locally as CSV backup"""
        try:
            import csv
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            # Use safe filename
            safe_guild_name = self.guild_name.replace(" ", "_")
            filename = f"{safe_guild_name}_backup_{timestamp}.csv"
            filepath = os.path.join(backup_dir, filename)
            
            if guild_data:
                fieldnames = ['Rank', 'Name', 'Title', 'Vocation', 'Level', 'Joining Date']
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(guild_data)
                
                print(f"✅ {self.guild_name} data saved locally: {filepath}")
                return True
            return False
                
        except Exception as e:
            print(f"❌ Error saving {self.guild_name} local backup: {e}")
            return False

    def check_google_permissions(self):
        """Check Google OAuth permissions"""
        try:
            creds = self.get_google_credentials()
            client = gspread.authorize(creds)
            
            files = client.list_spreadsheet_files()
            print(f"✅ Can access Drive - found {len(files)} spreadsheets")
            return True
                
        except Exception as e:
            print(f"❌ OAuth check failed: {e}")
            return False

    def run_with_retries(self):
        """Faster retry logic - only 2 attempts"""
        max_attempts = 2
        
        for attempt in range(1, max_attempts + 1):
            print(f"🎯 Attempt {attempt}/{max_attempts}")
            
            try:
                if not self.setup_driver():
                    print("❌ Browser setup failed")
                    continue
                
                guild_data = self.scrape_guild_data()
                
                if guild_data:
                    if self.update_spreadsheet(guild_data):
                        print(f"\n✅ SUCCESS on attempt {attempt}!")
                        print(f"📊 Updated with {len(guild_data)} members")
                        return True
                    else:
                        print(f"❌ Spreadsheet update failed on attempt {attempt}")
                else:
                    print(f"❌ No data scraped on attempt {attempt}")
                
            except Exception as e:
                print(f"❌ Error on attempt {attempt}: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                if self.driver:
                    self.driver.quit()
                    self.driver = None
            
            # Shorter retry wait
            if attempt < max_attempts:
                wait_time = 20
                print(f"⏳ Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        print(f"❌ All {max_attempts} attempts failed")
        return False

    def run(self):
        """Main execution function for Resonance Remain guild"""
        print("🚀 Resonance Remain Guild Tracker Starting...")
        print("🎯 Target: Resonance Remain Guild")
        print("=" * 50)
        
        # Setup cloud credentials first
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
        
        print("\n🎯 Step 3: Starting guild data collection with retry logic...")
        
        # Use retry logic for better Cloudflare handling
        success = self.run_with_retries()
        
        if success:
            print(f"\n🎉 RESONANCE REMAIN GUILD TRACKER COMPLETED SUCCESSFULLY!")
        else:
            print(f"\n❌ RESONANCE REMAIN GUILD TRACKER FAILED AFTER ALL RETRIES")

if __name__ == "__main__":
    print("🔥 STARTING RESONANCE REMAIN GUILD TRACKER...")
    print("📅 Date:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("🌍 Environment:", "GitHub Actions" if os.environ.get('GITHUB_ACTIONS') else "Local")
    print("-" * 50)
    
    try:
        tracker = ResonanceRemainTracker()
        print("✅ Resonance Remain tracker initialized successfully")
        tracker.run()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        # Exit with error code for GitHub Actions
        exit(1)
    
    print("\n🏁 Resonance Remain tracker execution completed")
    
    # Only wait for input if running locally (not in GitHub Actions)
    if not os.environ.get('GITHUB_ACTIONS'):
        input("Press Enter to exit...")%
