import csv
import pandas as pd
import time
import os
import datetime
import json
import requests
from jobspy import scrape_jobs
from urllib.parse import urlparse

file_path = '../../API_keys/keys.json'
with open(file_path, 'r') as file:
    api = json.load(file)
NEWS_API_KEY = {0: api['news_api'], 1:api['news_jaekang_api'], 2:api['news_minah_api'], 'credits':[True, True, True]}
NEWSDATA_API_KEY = {0: api['newsdata_api'], 1:api['newsdata_jaekang_api'], 2:api['newsdata_minah_api'], 'credits':[True, True, True]}

def api_changer(news):
    if news == 'news':
        for i in range(3):
            if NEWS_API_KEY['credits'][i]:
                return NEWS_API_KEY[i]
    else:
        for i in range(3):
            if NEWSDATA_API_KEY['credits'][i]:
                return NEWSDATA_API_KEY[i]
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
                time.sleep(5)  # Sleep between position searches
            time.sleep(10)  # Sleep between pages to avoid being blocked
        # Concatenate all job dataframes for the country
        if all_jobs:
            all_jobs_df = pd.concat(all_jobs, axis=0)
            # Save to CSV
            output_file = f"jobs/{country}_jobs_total.csv"
            all_jobs_df.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            print(f"Job postings for {country} saved to {output_file}")
        else:
            print(f"No job postings found for {country}.")

def get_company_names(jobs_csv_file):
    """
    Extract unique company names from the jobs CSV file.
    """
    jobs_df = pd.read_csv(jobs_csv_file)
    company_names = jobs_df['company'].dropna().unique()
    return company_names

def fetch_news_about_company(company_name, news_csv_file, days_back=15):
    """
    Fetch news articles about a company in the last 'days_back' days.
    Use NewsAPI.org by default, and switch to Newsdata.io if a 429 status code is received.
    """
    # Check if news_csv_file exists
    if os.path.exists(news_csv_file):
        existing_news_df = pd.read_csv(news_csv_file)
    else:
        existing_news_df = pd.DataFrame(columns=['company_name', 'published_date', 'title', 'description', 'url'])

    # Get list of existing titles for this company
    existing_titles = existing_news_df[existing_news_df['company_name'] == company_name]['title'].tolist()

    # Fetch news articles using NewsAPI.org
    base_url = "https://newsapi.org/v2/everything"
    all_articles = []
    today = datetime.datetime.now()
    from_date = (today - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
    to_date = today.strftime('%Y-%m-%d')

    status = "use_news_api" if sum(NEWS_API_KEY['credits']) > 0 else "use_newsdata_api"

    while True:
        if status == "use_news_api":
            for page in range(1, 4): # Fetch up to 2 pages to reduce requests
                params = {
                    'q': f'{company_name}',
                    'from': from_date,
                    'to': to_date,
                    'searchIn': "description",
                    'sortBy': 'publishedAt',
                    'apiKey': api_changer('news'),
                    'language': 'en',
                    'pageSize': 5,
                    'page': page,
                }
                response = requests.get(base_url, params=params)

                if response.status_code == 200:
                    news_data = response.json()
                    articles = news_data.get('articles', [])
                    if not articles:
                        break  # No more articles
                    for article in articles:
                        title = article.get('title')
                        description = article.get('description')
                        if title in existing_titles:
                            continue  # Skip duplicate
                        url = article.get('url')
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc

                        if title:
                            try:
                                title = title
                            except UnicodeDecodeError:
                                title = title # Handle or log error

                        if description:
                            try:
                                description = description
                            except UnicodeDecodeError:
                                description = description # Handle or log error

                        if title in existing_titles:
                            continue  # Skip duplicate

                        published_date = article.get('publishedAt', '')[0:10]
                        all_articles.append({
                            'company_name': company_name,
                            'published_date': published_date,
                            'title': title,
                            'description': description,
                            'url': url,
                            'origin': 'NewsAPI'
                        })
                    time.sleep(2)  # Sleep to respect rate limits

                elif response.status_code == 429:
                    if sum(NEWS_API_KEY['credits']) == 3:
                        NEWS_API_KEY['credits'][0] = False
                        print('Change news api to jaekang')
                        break
                    elif sum(NEWS_API_KEY['credits']) == 2:
                        NEWS_API_KEY['credits'][1] = False
                        print('Change news api to minah')
                        break
                    else:
                        NEWS_API_KEY['credits'][2] = False
                        status = "use_newsdata_api"
                        print(f"Received 429 status code from NewsAPI.org for {company_name} and use all credits in api keys. Switching to Newsdata.io API.")
                        break
                else:
                    print(f"Failed to fetch news articles for {company_name} from NewsAPI.org. Status code: {response.status_code}")
                    break

            if status == "use_newsdata_api":
                continue
            elif response.status_code != 429:
                break

        if status == "use_newsdata_api":
            newsdata_endpoint = 'https://newsdata.io/api/1/news'
            keyword = company_name  
            
            params = {
                'apikey': api_changer('newsdata'),
                'q': keyword,
                'language': 'en',
                'country': 'us',
                'category': 'business'
            }

            response = requests.get(newsdata_endpoint, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('results', [])

                for article in articles:
                    title = article.get('title')
                    description = article.get('description')
                    if title in existing_titles:
                        continue  # Skip duplicate

                    if title:
                        try:
                            title = title
                        except UnicodeDecodeError:
                            title = title  # Handle or log error

                    if description:
                        try:
                            description = description
                        except UnicodeDecodeError:
                            description = description  # Handle or log error
                    url = article.get('link')

                    if title in existing_titles:
                        continue  # Skip duplicate
                    
                    published_date = article.get('pubDate', '')[0:10]

                    all_articles.append({
                        'company_name': company_name,
                        'published_date': published_date,
                        'title': title,
                        'description': description,
                        'url': url,
                        'origin': 'Newsdata.io'
                    })

                time.sleep(2)
                break
            elif response.status_code == 429:
                if sum(NEWSDATA_API_KEY['credits']) == 3:
                    NEWSDATA_API_KEY['credits'][0] = False
                    print('Change newsdata api to jaekang')
                elif sum(NEWSDATA_API_KEY['credits']) == 2:
                    NEWSDATA_API_KEY['credits'][1] = False
                    print('Change newsdata api to minah')
                else:
                    NEWSDATA_API_KEY['credits'][2] = False
                    print(f"Received 429 status code from Newsdata.io for {company_name}. finish")
                    break
            else:
                print(f"Failed to fetch news articles for {company_name} from Newsdata.io. Status code: {response.status_code}")
                break

    if all_articles:
        # Convert to DataFrame
        new_news_df = pd.DataFrame(all_articles)
        # Append to existing_news_df
        combined_news_df = pd.concat([existing_news_df, new_news_df], ignore_index=True)
        # Remove duplicates based on 'company_name' and 'title'
        combined_news_df.drop_duplicates(subset=['company_name', 'title'], inplace=True)
        # Save to CSV
        os.makedirs('news', exist_ok=True)
        combined_news_df.to_csv(news_csv_file, index=False, encoding='utf-8-sig')
        print(f"News articles for {company_name} saved to {news_csv_file}")
    else:
        print(f"No new articles found for {company_name}")



if __name__ == '__main__':
    positions = ['machine learning']
    countries = ['USA'] 

    # Scrape jobs and save to CSV for each country
    scrape_jobs_for_countries(positions, countries, total_pages=2)

    # For each country, get company names and fetch news
    news_csv_file = 'news/news_data.csv'
    for country in countries:
        jobs_csv_file = f"jobs/{country}_jobs_total.csv"
        if not os.path.exists(jobs_csv_file):
            print(f"No job postings file found for {country}. Skipping news fetching.")
            continue
        company_names = get_company_names(jobs_csv_file)
        for company_name in company_names:
            print(f"Fetching news for company: {company_name}")
            fetch_news_about_company(company_name, news_csv_file, days_back=15)
            time.sleep(2)  # Sleep between companies to avoid rate limiting