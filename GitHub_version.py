# Add these methods to your existing ResonanceRemainTracker class:

def setup_driver(self):
    """Setup Chrome driver"""
    print("DEBUG: Setting up Chrome driver...", flush=True)
    chrome_options = Options()
    
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1366,768")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Basic stealth
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver setup successful")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Chrome driver: {e}")
        return False

def scrape_with_selenium(self):
    """Selenium-based scraping"""
    print("DEBUG: Starting selenium-based scraping...", flush=True)
    
    if not self.setup_driver():
        return []
    
    try:
        guild_name_encoded = urllib.parse.quote_plus(self.guild_name)
        url = f"https://rubinot.com.br/?subtopic=guilds&page=view&GuildName={guild_name_encoded}"
        
        print(f"🌐 Navigating to {self.guild_name} guild page with Selenium...")
        print(f"🔗 URL: {url}")
        
        time.sleep(2)
        self.driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        page_title = self.driver.title
        print(f"📄 Page title: {page_title}")
        
        # Check for Cloudflare
        page_source = self.driver.page_source.lower()
        if "cloudflare" in page_source or "attention required" in page_source:
            print("❌ Cloudflare challenge detected")
            return []
        
        if "blocked" in page_source or "forbidden" in page_source:
            print("❌ Access blocked by website")
            return []
        
        if "guild not found" in page_source:
            print("❌ Guild not found")
            return []
        
        print("✅ Successfully accessed guild page")
        
        # For now, return test data to confirm Selenium works
        test_data = [{
            'Rank': 'Leader',
            'Name': 'Selenium Test Member',
            'Title': '',
            'Vocation': 'Elite Knight',
            'Level': '200',
            'Joining Date': 'Jan 01 2025'
        }]
        print(f"✅ Returning test data with {len(test_data)} members")
        return test_data
        
    except Exception as e:
        print(f"❌ Error with selenium method: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if self.driver:
            self.driver.quit()
            self.driver = None

# Update your run method to try both approaches:

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
        ("Selenium", self.scrape_with_selenium)
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
