# Remove these two lines from the imports at the top of your file:
# import requests
# from bs4 import BeautifulSoup

# And replace the run_with_multiple_approaches method with this:

def run_with_multiple_approaches(self):
    """Try multiple selenium approaches"""
    approaches = [
        ("Standard Selenium", self.scrape_with_standard_selenium),
        ("Retry Standard Selenium", self.scrape_with_standard_selenium)
    ]
    
    for approach_name, approach_method in approaches:
        print(f"\n🎯 Trying approach: {approach_name}")
        
        try:
            guild_data = approach_method()
            
            if guild_data:
                print(f"✅ {approach_name} succeeded!")
                if self.update_spreadsheet(guild_data):
                    print(f"📊 Successfully updated spreadsheet with {len(guild_data)} members")
                    return True
                else:
                    print("❌ Spreadsheet update failed")
            else:
                print(f"❌ {approach_name} failed - no data retrieved")
                
        except Exception as e:
            print(f"❌ {approach_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        # Small delay between approaches
        time.sleep(10)
    
    print("❌ All approaches failed")
    return False

# Also remove the scrape_with_requests method entirely
