# %%
import csv
import pandas as pd
import time
import os
from jobspy import scrape_jobs
from datetime import datetime, timedelta

class JobScraper:
    def __init__(self, positions, countries, total_pages=4, days_old=30):
        """
        JobScraper 클래스 초기화 함수
        
        Args:
            positions (list): 스크래핑할 직무 목록
            countries (list): 스크래핑할 국가 목록
            total_pages (int): 각 직무별로 스크래핑할 페이지 수 (기본값: 4)
            days_old (int): 삭제할 오래된 채용공고 기준 일수 (기본값: 30일)
        """
        self.positions = positions 
        self.countries = countries 
        self.total_pages = total_pages 
        self.days_old = days_old 
        os.makedirs('jobs', exist_ok=True) 

    def remove_old_jobs(self, csv_file):
        """
        CSV 파일에서 지정된 일수보다 오래된 채용공고를 삭제하는 함수
        
        Args:
            csv_file (str): 처리할 CSV 파일 경로
        
        Returns:
            int: 삭제된 채용공고 개수
        """
        try:
            # 백업 파일 경로 설정 및 원본 파일 백업 생성
            backup_file = csv_file + '.backup'
            df = pd.read_csv(csv_file, encoding='utf-8')
            df.to_csv(backup_file, index=False, encoding='utf-8-sig')
            print(f"백업 파일 생성: {backup_file}")
            
            # 'date_posted' 컬럼이 존재하는지 확인
            if 'date_posted' not in df.columns:
                print(f"'date_posted' 열이 {csv_file}에 없습니다.")
                # 작업 완료 후 백업 파일 삭제
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                return 0
            
            # 현재 날짜와 기준 날짜(cutoff_date) 계산
            current_date = datetime.now()
            cutoff_date = current_date - timedelta(days=self.days_old)
            
            # 'date_posted' 컬럼을 datetime 형식으로 변환 (오류 발생시 NaT로 처리)
            df['date_posted'] = pd.to_datetime(df['date_posted'], format='%Y-%m-%d', errors='coerce')
            
            # 유효한 날짜 데이터를 가진 행들을 식별
            valid_dates = df['date_posted'].notna()
            
            # 기준 날짜 이후의 데이터만 필터링 (날짜가 없는 데이터는 보존)
            df_filtered = df[(df['date_posted'] >= cutoff_date) | (~valid_dates)]
            
            # 삭제된 행의 개수 계산
            removed_count = len(df) - len(df_filtered)
            
            # 유효한 날짜 데이터를 다시 문자열 형식으로 변환
            mask = df_filtered['date_posted'].notna()
            df_filtered.loc[mask, 'date_posted'] = df_filtered.loc[mask, 'date_posted'].dt.strftime('%Y-%m-%d')
            
            # 필터링된 데이터를 원본 파일에 저장
            df_filtered.to_csv(csv_file, index=False, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", encoding='utf-8-sig')
            print(f"{csv_file}에서 {removed_count}개의 오래된 잡 포스팅을 삭제했습니다.")

            # 작업 완료 후 백업 파일 삭제
            if os.path.exists(backup_file):
                os.remove(backup_file)
                print("백업 파일 삭제됨")

            return removed_count

        except FileNotFoundError:
            return 0
        except Exception as e:
            # 오류 발생시 백업 파일로부터 복구
            print(f"오류 발생: {e}")
            if 'backup_file' in locals() and os.path.exists(backup_file):
                print("백업에서 복구 중...")
                pd.read_csv(backup_file, encoding='utf-8-sig').to_csv(csv_file, index=False, encoding='utf-8-sig')
                print("복구 완료")
            return 0

    def scrape_jobs_for_countries(self):
        """
        여러 국가와 직무에 대해 채용공고를 스크래핑하는 함수
        """
        # 각 국가별로 반복
        for country in self.countries:
            # 각 직무별로 반복
            for pos in self.positions:
                pos_jobs = []  # 현재 직무의 모든 페이지 데이터를 저장할 리스트

                # 지정된 페이지 수만큼 반복하여 데이터 수집
                for j in range(self.total_pages):
                    sites = ["linkedin", "indeed"]  # 스크래핑할 사이트 목록
                    print(f"Scraping jobs for position '{pos}' in country '{country}', page {j+1}/{self.total_pages}...")
                    
                    # jobspy를 사용하여 채용공고 스크래핑
                    jobs = scrape_jobs(
                        site_name=sites,           # 검색할 사이트
                        search_term=pos,           # 검색 키워드 (직무명)
                        results_wanted=10,         # 페이지당 가져올 결과 수
                        hours_old=24*30,          # 최근 30일 이내 공고만
                        country_indeed=country,    # Indeed에서 검색할 국가
                        linkedin_fetch_description=True,  # LinkedIn 상세 설명 포함
                        offset=j*10               # 페이지 오프셋 (페이지네이션)
                    )

                    # 검색 결과가 없으면 다음 페이지로 넘어감
                    if jobs.empty:
                        print(f"No jobs found for {pos} in {country} on page {j+1}.")
                        continue

                    # 현재 페이지 결과를 리스트에 추가
                    pos_jobs.append(jobs)
                    print(f"Found {len(jobs)} jobs for '{pos}' in {country} on page {j+1}.")
                    
                    # API 호출 제한을 위한 대기 시간
                    time.sleep(5)

                # 수집된 데이터가 있으면 파일로 저장
                if pos_jobs:
                    # 모든 페이지의 데이터를 하나의 DataFrame으로 합치기
                    pos_jobs_df = pd.concat(pos_jobs, axis=0)
                    output_file = f"jobs/{country}_{pos}_jobs_total.csv"

                    # 기존 파일이 있으면 데이터 병합
                    if os.path.exists(output_file):
                        try:
                            # 기존 파일 읽기
                            existing_df = pd.read_csv(output_file, encoding='utf-8')
                            # 기존 데이터와 새 데이터 합치기
                            combined_df = pd.concat([existing_df, pos_jobs_df], axis=0)
                            
                            # 중복 제거 (job_id 또는 url 기준)
                            if 'job_id' in combined_df.columns:
                                combined_df = combined_df.drop_duplicates(subset=['job_id'], keep='last')
                            else:
                                combined_df = combined_df.drop_duplicates(subset=['url'], keep='last')

                            # 합쳐진 데이터를 파일에 저장
                            combined_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8-sig')
                            print(f"기존 데이터와 합쳐서 {len(combined_df)}개의 채용공고가 {output_file}에 저장되었습니다.")
                        except Exception as e:
                            # 기존 파일 읽기 실패시 새 데이터만 저장
                            print(f"기존 파일 읽기 오류: {e}")
                            print(f"새 데이터만 {output_file}에 저장합니다.")
                            pos_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8-sig')
                    else:
                        # 새 파일 생성
                        pos_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False, encoding='utf-8-sig')
                        print(f"{len(pos_jobs_df)}개의 채용공고가 {output_file}에 저장되었습니다.")
                else:
                    print(f"No job postings found for position '{pos}' in {country}.")

                # 다음 직무 처리 전 대기 시간
                time.sleep(10)

    def filter_job_data(self):
        """
        수집된 채용공고 데이터를 필터링하고 정제하는 함수
        불필요한 컬럼 제거, 결측값 처리, 데이터 정규화 수행
        """
        # 제거할 컬럼 목록 (분석에 불필요하거나 개인정보 관련 컬럼들)
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

        # 각 국가별로 처리
        for current_country in self.countries:
            # 각 직무별로 처리
            for current_position in self.positions:
                current_position_filename_part = current_position 
                
                # 입력 및 출력 파일 경로 설정
                input_file_name = f"{current_country}_{current_position_filename_part}_jobs_total.csv"
                output_file_name = f"{current_country}_{current_position_filename_part}_jobs_total_filtered.csv"
                input_file_path = os.path.join('jobs', input_file_name)
                output_file_path = os.path.join('jobs', output_file_name)

                print(f"--- 처리중인 파일: {input_file_path} ---")

                # CSV 파일 읽기 시도
                try:
                    df = pd.read_csv(input_file_path, encoding='utf-8')
                    print(f"성공적으로 읽음: {input_file_path}")
                except FileNotFoundError:
                    print(f"파일을 찾을 수 없음: {input_file_path}. 건너뜀.")
                    continue
                except Exception as e:
                    print(f"오류 읽기 {input_file_path}: {e}. 건너뜀.")
                    continue

                # 실제 존재하는 컬럼만 제거 (존재하지 않는 컬럼 제거 시 오류 방지)
                existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
                if existing_columns_to_drop:
                    df = df.drop(columns=existing_columns_to_drop)

                # 'location' 컬럼 결측값을 현재 국가명으로 채우기
                if 'location' in df.columns:
                    df['location'] = df['location'].fillna(current_country)

                # 'date_posted' 컬럼 결측값 처리 (뒤에서 앞으로, 앞에서 뒤로 채우기)
                if 'date_posted' in df.columns:
                    df['date_posted'] = df['date_posted'].bfill().ffill()

                # 'job_type' 컬럼 결측값을 'fulltime'으로 채우기
                if 'job_type' in df.columns:
                    df['job_type'] = df['job_type'].fillna('fulltime')

                # 'is_remote' 컬럼 결측값을 False로 채우기
                if 'is_remote' in df.columns:
                    df['is_remote'] = df['is_remote'].fillna(False)

                # 'title' 컬럼 결측값을 현재 직무명으로 채우기
                if 'title' in df.columns:
                    df['title'] = df['title'].fillna(current_position)

                # 필수 컬럼 존재 여부 확인
                company_col_exists = 'company' in df.columns
                description_col_exists = 'description' in df.columns

                # 회사명과 채용공고 설명이 모두 없는 행들 제거
                if company_col_exists and description_col_exists:
                    df.dropna(subset=['company', 'description'], how='any', inplace=True)
                elif company_col_exists:
                    df.dropna(subset=['company'], inplace=True)
                elif description_col_exists:
                    df.dropna(subset=['description'], inplace=True)
                
                # 정제된 데이터를 새 파일로 저장
                try:
                    df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
                    print(f"성공적으로 저장됨: {output_file_path}")
                except Exception as e:
                    print(f"오류 저장 {output_file_path}: {e}")
                
                print(f"--- 처리 완료: {input_file_path} ---\n")

        print("모든 파일 처리 완료.")

    def run(self):
        """
        전체 채용공고 처리 파이프라인 실행
        """
        # 1. 오래된 채용공고 삭제
        print("--- 1단계: 오래된 채용공고 삭제 시작 ---")
        for country in self.countries:
            for position in self.positions:
                csv_file = f"jobs/{country}_{position}_jobs_total.csv"
                removed_count = self.remove_old_jobs(csv_file)
                if removed_count > 0:
                    print(f"{csv_file}에서 {removed_count}개의 오래된 공고 삭제 완료.")
        print("--- 1단계: 오래된 채용공고 삭제 완료 ---\n")

        # 2. 새로운 채용공고 스크래핑
        print("--- 2단계: 새로운 채용공고 스크래핑 시작 ---")
        self.scrape_jobs_for_countries()
        print("--- 2단계: 새로운 채용공고 스크래핑 완료 ---\n")

        # 3. 채용공고 데이터 필터링
        print("--- 3단계: 채용공고 데이터 필터링 시작 ---")
        self.filter_job_data()
        print("--- 3단계: 채용공고 데이터 필터링 완료 ---\n")
        print("모든 작업이 완료되었습니다.")


if __name__ == '__main__':
    """
    추후 상용화 시 cron을 이용한 자동화 방식 세팅
    ```terminal
    crontab -e

    0 0 1 * * /home/사용자/miniconda3/envs/가상환경이름/bin/python /경로/내파일.py
    ```
    """

    # 예시 직무 목록
    #positions = ['Machine Learning', 'Front-End', 'Back-End', 'mechanical engineer', 'marketing']
    positions = ['machine learning']
    # 예시 국가 목록
    #countries = ['UK', 'Germany', 'USA']
    countries = ['USA']

    # JobScraper 인스턴스 생성 및 실행
    scraper = JobScraper(positions=positions, countries=countries, total_pages=4, days_old=30)
    scraper.run()


# %%
