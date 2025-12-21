#!/usr/bin/env python3
"""
PDF에서 URL을 추출하는 유틸리티 모듈
PyMuPDF를 사용하여 PDF의 하이퍼링크를 추출하고, 정규표현식으로 텍스트에서 URL 패턴을 찾습니다.

.com이 포함되는 url만 추출
```python 
result = get_urls_from_pdf(
    pdf_path,
    include_domains=['.com']
)
```
"""

import os
import re
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def extract_urls_from_pdf(pdf_path: str):
    """
    PDF에서 모든 하이퍼링크 URL을 추출합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        list: 추출된 URL 리스트 (dict 형태: {'page': int, 'url': str, 'type': str})
        
    Raises:
        ImportError: PyMuPDF가 설치되지 않은 경우
        FileNotFoundError: PDF 파일이 존재하지 않는 경우
    """
    if fitz is None:
        raise ImportError("PyMuPDF가 설치되지 않았습니다. 'pip install PyMuPDF'로 설치하세요.")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    urls = []
    
    try:
        # PDF 열기
        doc = fitz.open(pdf_path)
        
        # 각 페이지 순회
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 페이지의 모든 링크 가져오기
            links = page.get_links()
            
            for link in links:
                # 'uri' 키가 있으면 외부 URL
                if 'uri' in link and link['uri']:
                    url = link['uri']
                    urls.append({
                        'page': page_num + 1,
                        'url': url,
                        'type': 'hyperlink'
                    })
        
        doc.close()
        
        # 중복 URL 제거 (순서 유지)
        seen_urls = set()
        unique_urls = []
        for item in urls:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_urls.append(item)
        
        return unique_urls
        
    except Exception as e:
        raise Exception(f"URL 추출 중 오류 발생: {e}")


def extract_urls_from_text(text: str):
    """
    텍스트에서 URL 패턴을 추출합니다.
    (하이퍼링크가 아닌 일반 텍스트로 작성된 URL 추출용)
    
    Args:
        text: 검색할 텍스트
        
    Returns:
        list: 추출된 URL 리스트 (string 형태)
    """
    # URL 패턴 정규표현식
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    urls = url_pattern.findall(text)
    return list(set(urls))  # 중복 제거


def filter_valid_urls(urls, include_domains=None, exclude_patterns=None):
    """
    URL 리스트를 필터링합니다.
    
    Args:
        urls: URL 리스트 (dict 또는 string)
        include_domains: 포함할 도메인 확장자 리스트 (예: ['.com', '.net', '.org'])
                        None이면 .com만 포함
        exclude_patterns: 제외할 패턴 리스트 (예: ['mailto:', 'tel:'])
                         None이면 ['mailto:']만 제외
        
    Returns:
        list: 필터링된 URL 리스트 (원본 형태 유지)
    """
    if include_domains is None:
        include_domains = ['.com']
    
    if exclude_patterns is None:
        exclude_patterns = ['mailto:']
    
    filtered_urls = []
    
    for item in urls:
        # dict 형태면 url 키에서 추출, string이면 그대로 사용
        url = item['url'] if isinstance(item, dict) else item
        
        # 제외 패턴 확인
        should_exclude = False
        for pattern in exclude_patterns:
            if url.startswith(pattern):
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # 포함 도메인 확인
        has_valid_domain = False
        for domain in include_domains:
            if domain in url:
                has_valid_domain = True
                break
        
        if not has_valid_domain:
            continue
        
        filtered_urls.append(item)
    
    return filtered_urls


def get_urls_from_pdf(pdf_path: str, text_content: str = None, 
                     include_domains=None, exclude_patterns=None):
    """
    PDF에서 최종 필터링된 URL 리스트를 반환합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        text_content: 추출된 텍스트 내용 (선택사항, 제공되면 텍스트에서도 URL 추출)
        include_domains: 포함할 도메인 확장자 리스트 (기본값: ['.com'])
        exclude_patterns: 제외할 패턴 리스트 (기본값: ['mailto:'])
        
    Returns:
        list: 필터링된 고유 URL 리스트 (string 형태)
        
    Examples:
        >>> urls = get_urls_from_pdf("resume.pdf")
        >>> print(urls)
        ['https://github.com/username', 'https://linkedin.com/in/username']
        
        >>> # 여러 도메인 포함
        >>> urls = get_urls_from_pdf("resume.pdf", include_domains=['.com', '.org', '.io'])
        
        >>> # 텍스트 내용도 함께 검색
        >>> urls = get_urls_from_pdf("resume.pdf", text_content=extracted_text)
    """
    if fitz is None:
        raise ImportError("PyMuPDF가 설치되지 않았습니다. 'pip install PyMuPDF'로 설치하세요.")
    
    # PDF에서 하이퍼링크 추출
    urls_from_links = extract_urls_from_pdf(pdf_path)
    
    # 텍스트에서 URL 패턴 추출 (선택사항)
    urls_from_text = []
    if text_content:
        urls_from_text = extract_urls_from_text(text_content)
    
    # 필터링 적용
    filtered_links = filter_valid_urls(urls_from_links, include_domains, exclude_patterns)
    filtered_text_urls = filter_valid_urls(urls_from_text, include_domains, exclude_patterns)
    
    # 최종 고유 URL 목록 (string 형태로 반환)
    all_filtered_urls = set(
        [item['url'] for item in filtered_links] + 
        [url for url in filtered_text_urls]
    )
    
    return sorted(list(all_filtered_urls))
