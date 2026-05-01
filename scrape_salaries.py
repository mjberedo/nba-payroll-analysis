import pandas as pd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_hoopshype_salaries():
    print("Launching browser...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=options)
    all_data = []

    try:
        driver.get("https://hoopshype.com/salaries/players/")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.o6j80t__o6j80t tbody tr"))
        )

        page = 1
        while True:
            print(f"Scraping page {page}...")
            time.sleep(1.5)

            rows = driver.find_elements(By.CSS_SELECTOR, "table.o6j80t__o6j80t tbody tr")
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) < 3:
                    continue
                all_data.append({
                    "rank": cols[0].text.strip(),
                    "player": cols[1].text.strip(),
                    "salary_raw": cols[2].text.strip()
                })

            # Click the next button (second hd3Vfp button)
            btns = driver.find_elements(By.CSS_SELECTOR, "button.hd3Vfp__hd3Vfp")
            if len(btns) >= 2:
                next_btn = btns[1]
                if next_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", next_btn)
                    page += 1
                else:
                    print("Reached last page.")
                    break
            else:
                print("Pagination buttons not found, stopping.")
                break

    finally:
        driver.quit()

    df = pd.DataFrame(all_data)
    df["salary"] = (
        df["salary_raw"]
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
    df = df.drop(columns=["salary_raw"]).dropna(subset=["salary"])
    df["salary"] = df["salary"].astype(int)

    print(f"\nScraped {len(df)} players successfully.")
    print(df.head(10))

    return df


def save_salaries(df):
    os.makedirs("data/raw", exist_ok=True)
    
    # Deduplicate by player name
    before = len(df)
    df = df.drop_duplicates(subset=["player"])
    after = len(df)
    print(f"Removed {before - after} duplicate rows. {after} unique players.")
    
    output_path = "data/raw/salaries_raw.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    
    return df


if __name__ == "__main__":
    df = scrape_hoopshype_salaries()
    if df is not None:
        save_salaries(df)