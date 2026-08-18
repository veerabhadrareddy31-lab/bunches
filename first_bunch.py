import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==========================================
# 1. DYNAMIC FILE NAME & CONFIGURATION
# ==========================================
# ప్రతిరోజూ కొత్త ఫైల్ లో సేవ్ అవ్వడానికి డైనమిక్ నేమ్ (ఉదా: Leads_Backup_20260819.csv)
TODAY_DATE = datetime.now().strftime("%Y%m%d")
CSV_FILE = f"Leads_Backup_{TODAY_DATE}.csv"

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

def get_driver():
    return webdriver.Chrome(options=chrome_options)

# ==========================================
# 2. RESUME LOGIC (ఆగిపోయిన చోటు నుండి స్టార్ట్ చేయడానికి)
# ==========================================
processed_combos = set()

if os.path.exists(CSV_FILE):
    try:
        df_existing = pd.read_csv(CSV_FILE)
        if "City" in df_existing.columns and "Category" in df_existing.columns:
            counts = df_existing.groupby(["City", "Category"]).size()
            for (c, cat), count in counts.items():
                # 15 కంటే ఎక్కువ లీడ్స్ ఉంటేనే కంప్లీట్ అయినట్లుగా భావిస్తుంది
                if count >= 15:
                    processed_combos.add((str(c).strip().lower(), str(cat).strip().lower()))
        print(f"✅ ఫైల్ చెక్ చేయబడింది: ఇప్పటికే {len(processed_combos)} కేటగిరీలు సేవ్ అయి ఉన్నాయి.")
    except Exception as e:
        print(f"⚠️ CSV రీడ్ ప్రాబ్లమ్: {e}")

def save_data(data_list):
    if not data_list:
        return
    df_new = pd.DataFrame(data_list)
    if not os.path.isfile(CSV_FILE):
        df_new.to_csv(CSV_FILE, index=False)
    else:
        df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
    print(f"💾 {len(data_list)} కొత్త లీడ్స్ '{CSV_FILE}' లో సేవ్ అయ్యాయి!")

# ==========================================
# 3. SCRAPING FUNCTION WITH FULL SCROLL
# ==========================================
def scrape_leads(city, category):
    combo = (city.strip().lower(), category.strip().lower())
    if combo in processed_combos:
        print(f"⏩ Skipping {city} - {category} (Already Completed)")
        return

    print(f"\n🔍 Searching ALL Leads for: {category} in {city}...")
    driver = None
    
    try:
        driver = get_driver()
        search_query = f"{category} in {city}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        driver.get(url)
        time.sleep(4)

        try:
            scrollable_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Results for")]'))
            )
        except Exception:
            print("⚠️ రిజల్ట్స్ ప్యానెల్ లోడ్ అవ్వలేదు.")
            if driver: driver.quit()
            return

        # --- INFINITE SCROLL LOGIC ---
        print("📜 గూగుల్ మ్యాప్స్ లోని అన్ని షాప్స్ లోడ్ అయ్యే వరకు స్క్రోల్ చేస్తోంది...")
        last_height = 0
        no_change_count = 0
        max_scroll_limit = 80  # 200+ షాపులు లోడ్ అవ్వడానికి గరిష్ట స్క్రోల్స్

        for scroll_step in range(max_scroll_limit):
            try:
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                time.sleep(2.5)  # డేటా లోడ్ అవ్వడానికి టైమ్ ఇవ్వడం

                # "You've reached the end of the list." మెసేజ్ వచ్చిందో లేదో చెక్ చేయడం
                if "reached the end of the list" in driver.page_source.lower():
                    print("🛑 End of list వచ్చింది. స్క్రోలింగ్ పూర్తయింది.")
                    break

                new_height = driver.execute_script('return arguments[0].scrollHeight', scrollable_div)
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 3:  # 3 సార్లు కొత్త డేటా రాకపోతే ఆగిపోతుంది
                        print("🛑 ఇక కొత్త రిజల్ట్స్ ఏమీ లేవు.")
                        break
                else:
                    no_change_count = 0
                
                last_height = new_height
            except Exception as scroll_err:
                print(f"⚠️ స్క్రోల్ అవరోధం: {scroll_err}")
                break

        # --- DATA EXTRACTION ---
        items = driver.find_elements(By.XPATH, '//div[contains(@class, "Nv2PK")]')
        scraped_data = []

        print(f"📊 మొత్తం లోడ్ అయిన షాప్స్/బిజినెస్‌లు: {len(items)}")

        for item in items:
            try:
                name_elem = item.find_element(By.XPATH, './/div[contains(@class, "qBF1Pd")]')
                name = name_elem.text if name_elem else "N/A"

                link_elem = item.find_element(By.XPATH, './/a[contains(@href, "/maps/place/")]')
                link = link_elem.get_attribute("href") if link_elem else "N/A"

                if name and name != "N/A":
                    scraped_data.append({
                        "City": city,
                        "Category": category,
                        "Business Name": name,
                        "Google Maps Link": link
                    })
            except Exception:
                continue

        if scraped_data:
            save_data(scraped_data)
            print(f"🎉 SUCCESS: {city} - {category} నుండి మొత్తం {len(scraped_data)} లీడ్స్ తీసుకున్నాం!")
            processed_combos.add(combo)
        else:
            print("⚠️ ఏ లీడ్స్ దొరకలేదు.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == "__main__":
    CITIES = [
        "Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune",
        "Chennai", "Gurugram", "Noida", "Ahmedabad", "Kolkata",
        "Jaipur", "Kochi", "Chandigarh", "Indore", "Coimbatore",
        "Lucknow", "Surat", "Nagpur", "Vadodara", "Bhubaneswar",
        "Thiruvananthapuram", "Visakhapatnam", "Mysuru", "Mangaluru",
        "Nashik", "Bhopal", "Patna", "Vijayawada", "Tiruchirappalli", "Madurai"
    ]
    
    CATEGORIES = [
        "Restaurants", "Cafes", "Dental Clinics", "Salons", "Gyms / Fitness Centers",
        "Real Estate Agencies", "Hotels", "Clinics", "Interior Designers", "Digital Marketing Agencies",
        "Bakeries", "Hospitals", "Spas", "Photography Studios", "Car Repair Shops",
        "Car Dealerships", "Coaching Centers", "Schools", "Event Management Companies", "Furniture Stores",
        "Jewellery Stores", "Clothing Stores", "Mobile Phone Stores", "Diagnostic Centers", "Real Estate Developers",
        "Construction Companies", "Law Firms", "Chartered Accountants", "Travel Agencies", "Pet Clinics / Veterinary Clinics"
    ]

    print(f"🚀 Max Scraper Started ({len(CITIES)} Cities x {len(CATEGORIES)} Categories)...")
    print(f"📁 డేటా సేవ్ అయ్యే కొత్త ఫైల్: {CSV_FILE}")

    for city in CITIES:
        for category in CATEGORIES:
            scrape_leads(city, category)
