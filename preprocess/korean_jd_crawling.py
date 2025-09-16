import json
from re import T
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class TestCrawlingWanted:
    """
    원티드 사이트 테스트용 크롤링 (5개 항목만)
    """
    
    def __init__(self):
        self.endpoint = "https://www.wanted.co.kr"
        self.job_parent_category = 518
        self.job_category_id = 10110  # 소프트웨어 엔지니어
        self.job_category_name = "소프트웨어 엔지니어"
        # self.job_category_id2name = {
            # 10110: "소프트웨어 엔지니어",
            # 873: "웹 개발자",
            # 872: "서버 개발자",
            # 669: "프론트엔드 개발자",
            # 660: "자바 개발자",
            # 900: "C,C++ 개발자",
            # 899: "파이썬 개발자",
            # 1634: "머신러닝 엔지니어",
            # 674: "DevOps / 시스템 관리자",
            # 665: "시스템,네트워크 관리자",
            # 655: "데이터 엔지니어",
            # 895: "Node.js 개발자",
            # 677: "안드로이드 개발자",
            # 678: "iOS 개발자",
            # 658: "임베디드 개발자",
            # 877: "개발 매니저",
            # 1024: "데이터 사이언티스트",
            # 1026: "기술지원",
            # 676: "QA,테스트 엔지니어",
            # 672: "하드웨어 엔지니어",
            # 1025: "빅데이터 엔지니어",
            # 671: "보안 엔지니어",
            # 876: "프로덕트 매니저",
            # 10111: "크로스플랫폼 앱 개발자",
            # 1027: "블록체인 플랫폼 엔지니어",
            # 10231: "DBA",
            # 893: "PHP 개발자",
            # 661: ".NET 개발자",
            # 896: "영상,음성 엔지니어",
            # 10230: "ERP전문가",
            # 939: "웹 퍼블리셔",
            # 898: "그래픽스 엔지니어",
            # 795: "CTO,Chief Technology Officer",
            # 10112: "VR 엔지니어",
            # 1022: "BI 엔지니어",
            # 894: "루비온레일즈 개발자",
            # 793: "CIO,Chief Information Officer"
        # }
        
        self.tag2field_map = {
            "포지션 상세": "description",
            "주요업무": "main_work", 
            "자격요건": "qualification",
            "우대사항": "preferences",
            "혜택 및 복지": "welfare",
            "기술스택 ・ 툴": "tech_list"
        }
        
        # Chrome 드라이버 설정
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # 브라우저 창 안 띄우기
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--disable-notifications")  # 알림 차단
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        
        try:
            # chromedriver 경로 확인
            chromedriver_path = "/Users/minahkim/Desktop/work space/git_project/JobPT/chromedriver"
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # 시스템 PATH에서 chromedriver 찾기
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Chrome 드라이버 초기화 실패: {e}")
            print("Chrome과 chromedriver가 설치되어 있는지 확인해주세요.")
            raise
    
    def get_test_job_urls(self, limit=5):
        """테스트용으로 5개의 채용공고 URL만 가져오기"""
        print(f"채용공고 URL 수집 중... (최대 {limit}개)")
        
        url = f"{self.endpoint}/wdlist/{self.job_parent_category}/{self.job_category_id}"
        print(f"접속 URL: {url}")
        
        self.driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기
        
        # 페이지 스크롤 (일부만)
        self.driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(2)
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        ul_element = soup.find('ul', {'data-cy': 'job-list'})
        
        if not ul_element:
            print("채용공고 목록을 찾을 수 없습니다.")
            return []
        
        position_list = [
            a_tag['href'] for a_tag in ul_element.find_all('a') 
            if a_tag.get('href', '').startswith('/wd/')
        ][:limit]  # 제한된 개수만 가져오기
        
        print(f"수집된 URL 개수: {len(position_list)}")
        return position_list
    
    def crawl_job_detail(self, position_url):
        """개별 채용공고 상세 정보 크롤링"""
        full_url = f"{self.endpoint}{position_url}"
        print(f"크롤링 중: {full_url}")
        
        self.driver.get(full_url)
        time.sleep(2)
        
        try:
            # "상세 정보 더 보기" 버튼이 나타날 때까지 대기
            more_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[span[text()="상세 정보 더 보기"]]'))
            )
            self.driver.execute_script("arguments[0].click();", more_button)  # 버튼 클릭
            time.sleep(1)  # 로딩 대기
            print("✅ 상세 정보 더 보기 클릭 완료")
        except Exception as e:
            print("상세보기 버튼을 찾지 못했습니다.", e)

        result = {
            "url": full_url,
            "job_category": self.job_category_id,
            "job_name": self.job_category_name
        }
        
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        # 제목과 회사 정보
        job_header = soup.find("header", class_="JobHeader_JobHeader__TZkW3")
    
        if not job_header:
            print("채용공고 헤더를 찾을 수 없습니다.")
            return None
            
        try:
            result['title'] = job_header.find("h1").text.strip()
        except AttributeError:
            print("채용공고 제목을 찾을 수 없습니다.")
            return None
        
        # 회사 정보
        company_info = job_header.find("div", class_="JobHeader_JobHeader__Tools__lyxqQ")
        if company_info:
            result['company_name'] = company_info.text.strip()
            company_link = company_info.find("a")
            if company_link:
                result['company_id'] = company_link.get("href", "")
        
        # 태그 정보
        tags_div = job_header.find("div", class_="Tags_tagsClass__mvehZ")
        if tags_div:
            tag_list = tags_div.find_all("span")
            result['tag_name'] = [tag.text.lstrip("#").strip() for tag in tag_list]
            result['tag_id'] = [tag.get("href", "") for tag in tag_list]
        else:
            result['tag_name'] = []
            result['tag_id'] = []
        
        # 상세 내용
        job_body = soup.find("section", class_="JobContent_descriptionWrapper__RMlfm")
        if job_body:
            current_field = None
            h3_text = ""
            for elem in job_body.find_all(["h3", "h2", "p", "li", "div"]):
                if elem.name in ["h2", "h3"]:
                    title = elem.text.strip()
                    if title in self.tag2field_map:
                        current_field = self.tag2field_map[title]
                        result[current_field] = ""
                    else:
                        current_field = None
                elif current_field:
                    text = elem.get_text(" ", strip=True)
                    if text and len(h3_text) > 0:
                        result[current_field] = h3_text
                        h3_text = text
                    elif text:
                        result[current_field] = text
                        current_field = None
                elif current_field is None:
                    text = elem.get_text(" ", strip=True)
                    h3_text += text
        
        # 기술 스택 정제
        if "tech_list" in result and result["tech_list"]:
            result["tech_list"] = [t.strip() for t in result["tech_list"].split("・") if t.strip()]
        else:
            result["tech_list"] = []
        
        return result
    
    def run_test_crawling(self, limit=5):
        """테스트 크롤링 실행"""
        print("=== 원티드 테스트 크롤링 시작 ===")
        
        try:
            # 1. URL 수집
            position_urls = self.get_test_job_urls(limit)
            if not position_urls:
                print("수집할 URL이 없습니다.")
                return
            
            # 2. 상세 정보 크롤링
            results = []
            for i, url in enumerate(position_urls, 1):
                print(f"\n[{i}/{len(position_urls)}] 처리 중...")
                result = self.crawl_job_detail(url)
                if result:
                    results.append(result)
                    print(f"✅ 성공: {result.get('title', 'Unknown')}")
                else:
                    print("❌ 실패")
                
                # 요청 간격 (서버 부하 방지)
                time.sleep(1)
            
            # 3. 결과 저장
            output_file = "test_crawling_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"\n=== 크롤링 완료 ===")
            print(f"총 {len(results)}개 항목 수집")
            print(f"결과 파일: {output_file}")
            
            # 간단한 결과 미리보기
            print("\n=== 결과 미리보기 ===")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('company_name', 'Unknown')} - {result.get('title', 'Unknown')}")
                print(f"   URL: {result.get('url', '')}")
                print(f"   태그: {', '.join(result.get('tag_name', []))}")
                print()
            
            return results
            
        finally:
            self.driver.quit()
            print("브라우저 종료")

if __name__ == "__main__":
    crawler = TestCrawlingWanted()
    results = crawler.run_test_crawling(limit=5)
    
    # # view_files.py로 결과 확인하기
    # if results:
    #     print("\n결과를 HTML로 보려면:")
    #     print("python view_files.py test_crawling_results.json")
