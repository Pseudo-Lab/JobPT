import csv
import pandas as pd
import time
import os
from jobspy import scrape_jobs
from datetime import datetime, timedelta

def remove_old_jobs(csv_file, days_old=30):
    """
    30일 이상 된 잡 포스팅을 안전하게 삭제합니다.
    날짜 형식: YYYY-MM-DD
    """
    try:
        backup_file = csv_file + '.backup'
        
        df = pd.read_csv(csv_file)

        df.to_csv(backup_file, index=False)
        print(f"백업 파일 생성: {backup_file}")

        if 'date_posted' not in df.columns:
            print(f"'date_posted' 열이 {csv_file}에 없습니다.")
            return 0

        current_date = datetime.now()

        cutoff_date = current_date - timedelta(days=days_old)

        df['date_posted'] = pd.to_datetime(df['date_posted'], format='%Y-%m-%d', errors='coerce')

        valid_dates = df['date_posted'].notna()

        df_filtered = df[(df['date_posted'] >= cutoff_date) | (~valid_dates)]

        removed_count = len(df) - len(df_filtered)

        mask = df_filtered['date_posted'].notna()
        df_filtered.loc[mask, 'date_posted'] = df_filtered.loc[mask, 'date_posted'].dt.strftime('%Y-%m-%d')

        df_filtered.to_csv(csv_file, index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\")
        
        print(f"{csv_file}에서 {removed_count}개의 오래된 잡 포스팅을 삭제했습니다.")

        if os.path.exists(backup_file):
            os.remove(backup_file)
            print("백업 파일 삭제됨")
            
        return removed_count
        
    except Exception as e:
        print(f"오류 발생: {e}")
        # 백업에서 복구
        if os.path.exists(backup_file):
            print("백업에서 복구 중...")
            pd.read_csv(backup_file).to_csv(csv_file, index=False)
            print("복구 완료")
        return 0

def scrape_jobs_for_countries(positions, countries, total_pages=4):
    """
    Scrape job postings for given positions and countries, and save to CSV files.
    This function handles multiple countries within itself.
    """
    os.makedirs('jobs', exist_ok=True)
    
    for country in countries:
        all_jobs = []
        
        for j in range(total_pages):
            for pos in positions:
                if country == 'USA':
                    sites = ["linkedin", "indeed", "zip_recruiter"]
                else:
                    sites = ["linkedin", "indeed"]
                
                print(f"Scraping jobs for position '{pos}' in country '{country}', page {j+1}/{total_pages}...")
                
                jobs = scrape_jobs(
                    site_name=sites,
                    search_term=pos,
                    results_wanted=10,
                    hours_old=24*30,  # last 30 days
                    country_indeed=country,
                    linkedin_fetch_description=True,
                    offset=j*10
                )
                
                if jobs.empty:
                    print(f"No jobs found for {pos} in {country} on page {j+1}.")
                    continue
                
                all_jobs.append(jobs)
                print(f"Found {len(jobs)} jobs for '{pos}' in {country} on page {j+1}.")
                
                time.sleep(5)
            
            time.sleep(10)
        
        if all_jobs:
            all_jobs_df = pd.concat(all_jobs, axis=0)
            output_file = f"jobs/{country}_{pos}jobs_total.csv"
            all_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            print(f"Job postings for {country} saved to {output_file}")
            
        else:
            print(f"No job postings found for {country}.")

if __name__ == '__main__':
    """
    cron setting
    ```terminal
    crontab -e
    
    0 0 1 * * /home/사용자/miniconda3/envs/가상환경이름/bin/python /경로/내파일.py
    ```
    """
    positions = ['machine learning']
    countries = ['USA']
    
    for country in countries:
        for position in positions:
            remove_old_jobs(f"jobs/{country}_{position}jobs_total.csv", days_old=30)
            
    scrape_jobs_for_countries(positions, countries, total_pages=1)
