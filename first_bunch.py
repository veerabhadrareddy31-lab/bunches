import time
import re
import urllib.request
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 250+ All Major & Minor Indian Cities
CITIES = [
    "Ahmedabad", "Agartala", "Agra", "Ajmer", "Alappuzha", "Aligarh", "Alwar", "Amritsar", "Anantnag", "Asansol",
    "Aizawl", "Aurangabad", "Bengaluru", "Berhampur", "Bhagalpur", "Bhilai", "Bhopal", "Bhubaneswar", "Bikaner", "Bilaspur",
    "Bokaro", "Chandigarh", "Chennai", "Churachandpur", "Cuttack", "Daman", "Davanagere", "Dehradun", "Deoghar", "Delhi",
    "Dhanbad", "Dharamshala", "Dharmanagar", "Dibrugarh", "Dimapur", "Durg", "Durgapur", "Erode", "Faridabad", "Gangtok",
    "Gaya", "Ghaziabad", "Gorakhpur", "Guntur", "Guwahati", "Gwalior", "Gyalshing", "Haldwani", "Haridwar", "Hisar",
    "Howrah", "Hubballi", "Hyderabad", "Imphal", "Indore", "Itanagar", "Jabalpur", "Jaipur", "Jalandhar", "Jalgaon",
    "Jammu", "Jamnagar", "Jamshedpur", "Jodhpur", "Jorhat", "Jowai", "Kakinada", "Kanchipuram", "Kannur", "Kanpur",
    "Kapurthala", "Karimnagar", "Kargil", "Karnal", "Kavaratti", "Kharagpur", "Khammam", "Kochi", "Kohima", "Kolhapur",
    "Kolkata", "Kollam", "Korba", "Kota", "Kozhikode", "Kurnool", "Latur", "Leh", "Lucknow", "Ludhiana",
    "Lunglei", "Madurai", "Mandi", "Mangaluru", "Margao", "Mapusa", "Meerut", "Mohali", "Mokokchung", "Muzaffarpur",
    "Mysuru", "Nadiad", "Nagpur", "Naharlagun", "Nalgonda", "Nashik", "Navi Mumbai", "Namchi", "Nellore", "New Delhi",
    "Nizamabad", "Noida", "Panaji", "Panipat", "Patiala", "Patna", "Pasighat", "Pondicherry", "Port Blair", "Prayagraj",
    "Puducherry", "Pune", "Raipur", "Rajahmundry", "Rajkot", "Ranchi", "Rishikesh", "Roorkee", "Rourkela", "Sagar",
    "Salem", "Sambalpur", "Shillong", "Shimla", "Siliguri", "Silchar", "Silvassa", "Solan", "Srinagar", "Surat",
    "Thane", "Thiruvananthapuram", "Thrissur", "Thoubal", "Tiruchirappalli", "Tirupati", "Tiruppur", "Tura", "Udaipur", "Ujjain",
    "Vadodara", "Varanasi", "Vasco da Gama", "Vellore", "Vijayawada", "Visakhapatnam", "Warangal", "Anantapur", "Kadapa",
    "Eluru", "Ongole", "Chittoor", "Srikakulam", "Machilipatnam", "Vizianagaram", "Tenali", "Proddatur", "Hindupur",
    "Bhimavaram", "Madanapalle", "Guntakal", "Dharmavaram", "Gudivada", "Narasaraopet", "Tadepalligudem", "Suryapet",
    "Miryalaguda", "Adilabad", "Jagtial", "Nirmal", "Kamareddy", "Kothagudem", "Mancherial", "Ramagundam", "Wanaparthy"
]

# 2. Complete List of 40+ Business Categories
CATEGORIES = [
    # Health & Medical
    "Dental Clinics", "Hospitals", "Clinics", "Pharmacies", "Diagnostic Centers", "Eye Hospitals", "Ayurvedic Clinics",
    # Food & Hospitality
    "Cafes", "Restaurants", "Bakeries", "Hotels", "Sweet Shops", "Catering Services", "Ice Cream Parlors",
    # Beauty & Wellness
    "Salons", "Spas", "Gyms", "Yoga Studios", "Beauty Parlours", "Dermatologists",
    # Services & Agencies
    "Real Estate Agencies", "Interior Designers", "Digital Marketing Agencies", "Software Companies", 
    "Web Development Companies", "Event Managers", "Travel Agencies", "CA Firms", "Law Firms",
    # Automobile
    "Car Repair Shops", "Car Washes", "Bike Service Centers", "Car Showrooms",
    # Creative & Education
    "Photography Studios", "Schools", "Coaching Centers", "Colleges", "Dance Academies", "Driving Schools",
    # Retail & Home Needs
    "Furniture Stores", "Boutiques", "Jewelry Stores", "Electronics Stores"
]

# Headless Setup (బ్యాక్‌గ్రౌండ్ సైలెంట్ రన్నింగ్)
options = Options()
options.add_argument("--headless=new")
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--lang=en-US")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

all_leads = []

# Email Extractor (Main Page + Contact Pages)
def scrape_email_from_website(website_url):
    if not website_url or website_url == "N/A":
        return "N/A"
    
    urls_to_check = [website_url]
    if not website_url.endswith('/'):
        urls_to_check.extend([website_url + "/contact", website_url + "/contact-us", website_url + "/about"])
    
    found_emails = set()
    for url in urls_to_check:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            html = urllib.request.urlopen(req, timeout=3).read().decode('utf-8', errors='ignore')
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
            for e in emails:
                if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js')):
                    found_emails.add(e)
            if found_emails:
                break
        except:
            continue
            
    return list(found_emails)[0] if found_emails else "N/A"

# Opportunity Intelligence Engine
def calculate_opportunity(website, rating, reviews_count):
    score = 50
    opp_list = []
    
    if website == "N/A" or not website:
        score += 30
        opp_list.append("No Website (High Potential for Web Dev)")
    else:
        score -= 10

    try:
        r_val = float(rating)
        c_val = int(re.sub(r'[^\d]', '', str(reviews_count)))
        if r_val < 4.0:
            score += 15
            opp_list.append("Low Rating (Reputation Management Needed)")
        if c_val < 20:
            score += 15
            opp_list.append("Low Review Count (GMB SEO Needed)")
    except:
        pass

    score = min(max(score, 10), 100)
    
    if "No Website" in str(opp_list):
        angle = "Pitch Website & Local SEO Package"
    elif "Low Rating" in str(opp_list) or "Low Review Count" in str(opp_list):
        angle = "Pitch GMB Optimization & Review Automation"
    else:
        angle = "Pitch Content Engine AI Social Media Management"
        
    opp_str = " | ".join(opp_list) if opp_list else "Standard Marketing Outreach"
    return score, opp_str, angle


print("🔥 EXTREME FULL-DEPTH SCRAPING STARTED...")

for city in CITIES:
    for cat in CATEGORIES:
        search_query = f"{cat} in {city}"
        print(f"\n==========================================")
        print(f"🚀 Scraping Started: {search_query}")
        print(f"==========================================")
        
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        driver.get(url)
        time.sleep(3)

        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        except Exception:
            continue

        # 60 SCROLLS - లోతుగా ఉన్న ప్రతీ ఒక్క బిజినెస్‌ని లోడ్ చేస్తుంది
        last_height = driver.execute_script('return arguments[0].scrollHeight', scrollable_div)
        for scroll_step in range(60):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            time.sleep(1.8)
            new_height = driver.execute_script('return arguments[0].scrollHeight', scrollable_div)
            
            # రిజల్ట్స్ ఇక పెరగవు అని నిర్ధారణ అయితేనే నెక్స్ట్ స్టెప్‌కి వెళ్తుంది
            if new_height == last_height and scroll_step > 25:
                break
            last_height = new_height

        results = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc')
        print(f"Total Shops Found for {search_query}: {len(results)}")

        # ఆ కేటగిరీలో దొరికిన ప్రతీ ఒక్క రిజల్ట్‌ని స్క్రేప్ చేస్తుంది
        for index, result in enumerate(results):
            try:
                map_url = result.get_attribute("href")
                
                coords = "N/A"
                if map_url and "!3d" in map_url:
                    try:
                        lat_long = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', map_url)
                        if lat_long:
                            coords = f"{lat_long.group(1)}, {lat_long.group(2)}"
                    except:
                        coords = "N/A"

                driver.execute_script("arguments[0].scrollIntoView(true);", result)
                driver.execute_script("arguments[0].click();", result)
                time.sleep(1.8)

                # 1. Business Name
                try: name = driver.find_element(By.CSS_SELECTOR, 'h1.DUwfe, h1.DUwDvf, h1').text
                except: name = "N/A"

                # 2. Website
                try: website = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute("href")
                except: website = "N/A"

                # 3. Phone
                try: phone = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id*="phone"]').text.replace('\n', ' ')
                except: phone = "N/A"

                # 4. Address
                try: address = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]').text.replace('\n', ' ')
                except: address = "N/A"

                # 5. Rating
                try: rating = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span[aria-hidden="true"]').text
                except: rating = "N/A"

                # 6. Reviews
                try: reviews = driver.find_element(By.CSS_SELECTOR, 'div.F7nice span:nth-child(2)').text.replace('(', '').replace(')', '')
                except: reviews = "0"

                # 7. Deep Email Extraction
                email = scrape_email_from_website(website)

                # 8. Opportunity Intelligence
                opp_score, opp_type, outreach_angle = calculate_opportunity(website, rating, reviews)

                print(f"[{city} | {cat}] #{index+1} {name} | Phone: {phone} | Email: {email}")

                all_leads.append({
                    "City": city,
                    "Category": cat,
                    "Business Name": name,
                    "Address": address,
                    "Phone": phone,
                    "Website": website,
                    "Email": email,
                    "Rating": rating,
                    "Reviews": reviews,
                    "Coordinates": coords,
                    "Google Maps URL": map_url,
                    "Opportunity Score": opp_score,
                    "Opportunity": opp_type,
                    "Outreach Angle": outreach_angle
                })

            except Exception:
                continue

    # ప్రతి సిటీ కంప్లీట్ అవ్వగానే బ్యాకప్ ఫైల్ సేవ్ అవుతుంది
    df_temp = pd.DataFrame(all_leads)
    df_temp.drop_duplicates(subset=["Business Name", "Phone"], keep="first", inplace=True)
    df_temp.to_csv("All_India_Master_Leads_Backup.csv", index=False)
    print(f" Backup Progress Saved: Finished {city} | Total Leads Collected So Far: {len(df_temp)}")

# ఫైనల్ సేవ్
df_final = pd.DataFrame(all_leads)
df_final.drop_duplicates(subset=["Business Name", "Phone"], keep="first", inplace=True)
df_final.to_csv("All_India_Master_Leads_Final.csv", index=False)

print("\n🎉 MISSION ACCOMPLISHED! All India Lead Generation Finished!")
driver.quit()