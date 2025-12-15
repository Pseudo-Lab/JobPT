"""
JD URL 크롤러
채용 공고 URL에서 텍스트를 추출하는 모듈
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urlparse
import re


class JDCrawler:
    """채용 공고 URL 크롤링 클래스"""

    SUPPORTED_DOMAINS = {
        "saramin.co.kr": "사람인",
        "jobkorea.co.kr": "잡코리아",
        "wanted.co.kr": "원티드",
        "linkedin.com": "LinkedIn",
        "incruit.com": "인크루트",
        "jobplanet.co.kr": "잡플래닛",
    }

    TIMEOUT = 10  # 요청 타임아웃 (초)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """URL 유효성 검사"""
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False

    @staticmethod
    def get_domain(url: str) -> Optional[str]:
        """URL에서 도메인 추출"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # www. 제거
            if domain.startswith('www.'):
                domain = domain[4:]
            # 빈 도메인이면 None 반환
            return domain if domain else None
        except Exception:
            return None

    @staticmethod
    def is_supported_domain(url: str) -> tuple[bool, Optional[str]]:
        """
        지원하는 도메인인지 확인
        Returns: (지원 여부, 사이트명)
        """
        domain = JDCrawler.get_domain(url)
        if not domain:
            return False, None

        for supported_domain, site_name in JDCrawler.SUPPORTED_DOMAINS.items():
            if supported_domain in domain:
                return True, site_name

        return False, None

    @staticmethod
    def crawl_url(url: str) -> Dict[str, any]:
        """
        URL에서 채용 공고 텍스트 크롤링

        Args:
            url: 채용 공고 URL

        Returns:
            {
                "success": bool,
                "text": str,  # 추출된 텍스트
                "site": str,  # 사이트명
                "error": str  # 에러 메시지 (실패시)
            }
        """
        # URL 유효성 검사
        if not JDCrawler.is_valid_url(url):
            return {
                "success": False,
                "text": "",
                "site": "",
                "error": "유효하지 않은 URL 형식입니다."
            }

        # 도메인 확인
        domain = JDCrawler.get_domain(url)
        is_supported, site_name = JDCrawler.is_supported_domain(url)

        try:
            # HTTP 요청
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=JDCrawler.TIMEOUT)
            response.raise_for_status()

            # 인코딩 설정
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding

            html_content = response.text

            # HTML에서 텍스트 추출 (BeautifulSoup 사용)
            soup = BeautifulSoup(html_content, 'html.parser')

            # script, style 태그 제거
            for script_or_style in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav']):
                script_or_style.decompose()

            # 텍스트 추출
            text = soup.get_text(separator=' ', strip=True)

            # 여러 공백을 하나로
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()

            if not text:
                return {
                    "success": False,
                    "text": "",
                    "site": site_name or domain,
                    "error": "페이지에서 텍스트를 추출할 수 없습니다."
                }

            return {
                "success": True,
                "text": text,
                "site": site_name or domain,
                "error": ""
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "text": "",
                "site": site_name or domain or "",
                "error": f"요청 시간이 초과되었습니다 (타임아웃: {JDCrawler.TIMEOUT}초)."
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "text": "",
                "site": site_name or domain or "",
                "error": f"페이지를 가져오는 중 오류가 발생했습니다: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "site": site_name or domain or "",
                "error": f"예상치 못한 오류가 발생했습니다: {str(e)}"
            }


def crawl_jd_from_url(url: str) -> Dict[str, any]:
    """
    JD URL 크롤링 헬퍼 함수

    Args:
        url: 채용 공고 URL

    Returns:
        크롤링 결과 딕셔너리
    """
    return JDCrawler.crawl_url(url)
