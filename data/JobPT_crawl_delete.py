# %%
import csv
import pandas as pd
import time
import os
from jobspy import scrape_jobs
from datetime import datetime, timedelta

def remove_old_jobs(csv_file, days_old=30):
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
        if os.path.exists(backup_file):
            print("백업에서 복구 중...")
            pd.read_csv(backup_file).to_csv(csv_file, index=False)
            print("복구 완료")
        return 0

def scrape_jobs_for_countries(positions, countries, total_pages=4):
    os.makedirs('jobs', exist_ok=True)

    for country in countries:
        for pos in positions:
            pos_jobs = []

            for j in range(total_pages):
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

                pos_jobs.append(jobs)
                print(f"Found {len(jobs)} jobs for '{pos}' in {country} on page {j+1}.")

                time.sleep(5)

            if pos_jobs:
                pos_jobs_df = pd.concat(pos_jobs, axis=0)
                output_file = f"jobs/{country}_{pos}_jobs_total.csv"

                if os.path.exists(output_file):
                    try:
                        existing_df = pd.read_csv(output_file)
                        combined_df = pd.concat([existing_df, pos_jobs_df], axis=0)
                        if 'job_id' in combined_df.columns:
                            combined_df = combined_df.drop_duplicates(subset=['job_id'], keep='last')
                        else:
                            combined_df = combined_df.drop_duplicates(subset=['url'], keep='last')

                        combined_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8')
                        print(f"기존 데이터와 합쳐서 {len(combined_df)}개의 채용공고가 {output_file}에 저장되었습니다.")
                    except Exception as e:
                        print(f"기존 파일 읽기 오류: {e}")
                        print(f"새 데이터만 {output_file}에 저장합니다.")
                        pos_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8')
                else:
                    pos_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8')
                    print(f"{len(pos_jobs_df)}개의 채용공고가 {output_file}에 저장되었습니다.")
            else:
                print(f"No job postings found for position '{pos}' in {country}.")

            time.sleep(10)

def filter_job_data(positions_list, countries_list):
    columns_to_drop = [
        'id', 
        'job_url_direct',
        'site', 
        'interval', 
        'listing_type', 
        'emails', 
        'job_level',
        'job_function',
        'salary_source',
        'min_amount',
        'max_amount',
        'currency',
        'company_industry', 
        'company_url', 
        'company_logo', 
        'company_addresses',
        'company_revenue', 
        'company_rating', 
        'company_reviews_count',
        'company_url_direct',
        'company_num_employees',
        'company_description',
        'vacancy_count', 
        'work_from_home_type',
        'skills',
        'experience_range',
    ]

    for current_country in countries_list:
        for current_position in positions_list:
            current_position_filename_part = current_position 
            
            input_file_name = f"{current_country}_{current_position_filename_part}_jobs_total.csv"
            output_file_name = f"{current_country}_{current_position_filename_part}_jobs_total_filtered.csv"
            
            input_file_path = os.path.join('jobs', input_file_name)
            output_file_path = os.path.join('jobs', output_file_name)

            print(f"--- 처리중인 파일: {input_file_path} ---")

            try:
                df = pd.read_csv(input_file_path, encoding='utf-8')
                print(f"성공적으로 읽음: {input_file_path}")
            except FileNotFoundError:
                print(f"파일을 찾을 수 없음: {input_file_path}. 건너뜀.")
                continue
            except Exception as e:
                print(f"오류 읽기 {input_file_path}: {e}. 건너뜀.")
                continue

            existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
            if existing_columns_to_drop:
                 df = df.drop(columns=existing_columns_to_drop)

            if 'location' in df.columns:
                df['location'] = df['location'].fillna(current_country)

            if 'date_posted' in df.columns:
                df['date_posted'] = df['date_posted'].bfill().ffill()

            if 'job_type' in df.columns:
                df['job_type'] = df['job_type'].fillna('fulltime')

            if 'is_remote' in df.columns:
                df['is_remote'] = df['is_remote'].fillna(False)

            if 'title' in df.columns:
                df['title'] = df['title'].fillna(current_position)

            company_col_exists = 'company' in df.columns
            description_col_exists = 'description' in df.columns

            if company_col_exists and description_col_exists:
                df.dropna(subset=['company', 'description'], how='any', inplace=True)
            elif company_col_exists:
                df.dropna(subset=['company'], inplace=True)
            elif description_col_exists:
                df.dropna(subset=['description'], inplace=True)
            
            try:
                df.to_csv(output_file_path, index=False, encoding='utf-8')
                print(f"성공적으로 저장됨: {output_file_path}")
            except Exception as e:
                print(f"오류 저장 {output_file_path}: {e}")
            
            print(f"--- 처리 완료: {input_file_path} ---\n")

    print("모든 파일 처리 완료.")

if __name__ == '__main__':
    """
    cron setting
    ```terminal
    crontab -e

    0 0 1 * * /home/사용자/miniconda3/envs/가상환경이름/bin/python /경로/내파일.py
    ```
    """
    positions = ['Machine Learning', 'Front-End', 'Back-End', 'mechanical engineer', 'marketing']
    countries = ['UK', 'Germany', 'USA']

    for country in countries:
        for position in positions:
            remove_old_jobs(f"jobs/{country}_{position}_jobs_total.csv", days_old=30)

    scrape_jobs_for_countries(positions, countries, total_pages=4)

    filter_job_data(positions, countries)


# %%
