"""
Blog Scraping 기반 LangChain Tools
블로그 내용을 스크래핑하여 분석하는 도구 모음
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
from urllib.parse import urljoin, urlparse
import re


def _get_page_content(url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
    """웹 페이지 내용을 가져와서 BeautifulSoup 객체로 반환"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        return None


def _extract_text_safe(element, max_length: int = 5000) -> str:
    """요소에서 텍스트를 안전하게 추출"""
    if element is None:
        return ""
    text = element.get_text(strip=True, separator=' ')
    return text[:max_length] if text else ""


@tool
def fetch_homepage_overview(url: str) -> Dict[str, Any]:
    """
    Fetch blog homepage overview including title, description, and basic metadata
    
    Args:
        url: Blog homepage URL (e.g., https://example.tistory.com/ or https://blog.example.com/)
    
    Returns:
        블로그 기본 정보 (제목, 설명, 카테고리 등)
    """
    soup = _get_page_content(url)
    if not soup:
        return {"error": f"Failed to fetch {url}"}
    
    # 블로그 제목
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.get_text(strip=True)
    
    # 블로그 설명 (meta description)
    description = ""
    meta_desc = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if meta_desc:
        description = meta_desc.get('content', '')
    
    # 카테고리 찾기 (일반적인 패턴)
    categories = []
    category_links = soup.find_all('a', href=re.compile(r'/category/'))
    for link in category_links[:20]:  # 최대 20개
        cat_name = link.get_text(strip=True)
        cat_url = urljoin(url, link.get('href', ''))
        if cat_name:
            categories.append({
                "name": cat_name,
                "url": cat_url
            })
    
    # 블로그 주인 정보 (있다면)
    author = ""
    author_tag = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'article:author'})
    if author_tag:
        author = author_tag.get('content', '')
    
    return {
        "url": url,
        "title": title,
        "description": description,
        "author": author,
        "categories": categories,
        "category_count": len(categories)
    }


@tool
def list_recent_posts(url: str, max_posts: int = 10) -> List[Dict[str, Any]]:
    """
    List recent blog posts from homepage or category page
    
    Args:
        url: Blog homepage or category page URL
        max_posts: Maximum number of posts to return (default: 10)
    
    Returns:
        최근 게시물 리스트 (제목, URL, 날짜, 요약 등)
    """
    soup = _get_page_content(url)
    if not soup:
        return [{"error": f"Failed to fetch {url}"}]
    
    posts = []
    
    # 티스토리 패턴
    post_items = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'post|article|entry'))
    
    for item in post_items[:max_posts]:
        # 제목과 링크
        title_tag = item.find('h2') or item.find('h3') or item.find('a', class_=re.compile(r'title|headline'))
        if not title_tag:
            continue
        
        link_tag = title_tag.find('a') if title_tag.name != 'a' else title_tag
        if not link_tag:
            continue
        
        post_url = urljoin(url, link_tag.get('href', ''))
        title = link_tag.get_text(strip=True)
        
        # 날짜
        date = ""
        date_tag = item.find('time') or item.find(class_=re.compile(r'date|time'))
        if date_tag:
            date = date_tag.get('datetime', '') or date_tag.get_text(strip=True)
        
        # 요약
        summary = ""
        summary_tag = item.find('p') or item.find(class_=re.compile(r'summary|excerpt|description'))
        if summary_tag:
            summary = _extract_text_safe(summary_tag, 300)
        
        posts.append({
            "title": title,
            "url": post_url,
            "date": date,
            "summary": summary
        })
    
    return posts


@tool
def fetch_post_content(url: str, include_metadata: bool = True) -> Dict[str, Any]:
    """
    Fetch full content of a specific blog post
    
    Args:
        url: Blog post URL
        include_metadata: Whether to include metadata (title, date, tags) (default: True)
    
    Returns:
        게시물 전체 내용 (제목, 본문, 날짜, 태그 등, 최대 10000자)
    """
    soup = _get_page_content(url)
    if not soup:
        return {"error": f"Failed to fetch {url}"}
    
    result = {"url": url}
    
    if include_metadata:
        # 제목
        title = ""
        title_tag = soup.find('h1') or soup.find('h2', class_=re.compile(r'title|headline'))
        if not title_tag:
            title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        result["title"] = title
        
        # 날짜
        date = ""
        date_tag = soup.find('time') or soup.find(class_=re.compile(r'date|published'))
        if date_tag:
            date = date_tag.get('datetime', '') or date_tag.get_text(strip=True)
        result["date"] = date
        
        # 태그
        tags = []
        tag_links = soup.find_all('a', href=re.compile(r'/tag/'))
        for tag_link in tag_links[:10]:
            tag_name = tag_link.get_text(strip=True)
            if tag_name:
                tags.append(tag_name)
        result["tags"] = tags
    
    # 본문 내용
    content = ""
    # 일반적인 본문 패턴 찾기
    content_div = (
        soup.find('div', class_=re.compile(r'post-content|entry-content|article-content|contents_style')) or
        soup.find('article') or
        soup.find('div', id=re.compile(r'content|post|article'))
    )
    
    if content_div:
        # 불필요한 요소 제거
        for unwanted in content_div.find_all(['script', 'style', 'nav', 'aside', 'footer', 'header']):
            unwanted.decompose()
        
        content = _extract_text_safe(content_div, 10000)
    
    result["content"] = content
    result["content_length"] = len(content)
    
    return result


@tool
def extract_blog_categories(url: str) -> List[Dict[str, Any]]:
    """
    Extract all categories from a blog
    
    Args:
        url: Blog homepage URL
    
    Returns:
        카테고리 리스트 (이름, URL, 게시물 수 등)
    """
    soup = _get_page_content(url)
    if not soup:
        return [{"error": f"Failed to fetch {url}"}]
    
    categories = []
    
    # 카테고리 링크 찾기
    category_section = soup.find('nav') or soup.find('div', class_=re.compile(r'categor|menu|sidebar'))
    
    if category_section:
        category_links = category_section.find_all('a', href=re.compile(r'/category/|/tag/'))
    else:
        category_links = soup.find_all('a', href=re.compile(r'/category/|/tag/'))
    
    seen_urls = set()
    for link in category_links:
        cat_url = urljoin(url, link.get('href', ''))
        if cat_url in seen_urls:
            continue
        seen_urls.add(cat_url)
        
        cat_name = link.get_text(strip=True)
        
        # 게시물 수 (있다면)
        post_count = ""
        count_span = link.find('span', class_=re.compile(r'count|num'))
        if count_span:
            post_count = count_span.get_text(strip=True)
        
        if cat_name:
            categories.append({
                "name": cat_name,
                "url": cat_url,
                "post_count": post_count
            })
    
    return categories[:30]  # 최대 30개


@tool
def inspect_page_structure(url: str, max_elements: int = 20) -> Dict[str, Any]:
    """
    Inspect HTML structure of a blog page to understand its layout
    
    Args:
        url: Page URL to inspect
        max_elements: Maximum number of structural elements to analyze (default: 20)
    
    Returns:
        페이지 구조 정보 (주요 HTML 요소, 클래스, ID 등)
    """
    soup = _get_page_content(url)
    if not soup:
        return {"error": f"Failed to fetch {url}"}
    
    # 주요 구조 요소
    structure = {
        "url": url,
        "main_sections": [],
        "common_classes": [],
        "ids": []
    }
    
    # 주요 섹션 태그
    main_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
    for tag in main_tags:
        elements = soup.find_all(tag, limit=5)
        for elem in elements:
            classes = elem.get('class', [])
            elem_id = elem.get('id', '')
            structure["main_sections"].append({
                "tag": tag,
                "classes": classes,
                "id": elem_id
            })
    
    # 자주 사용되는 클래스
    all_classes = []
    for elem in soup.find_all(class_=True, limit=max_elements * 2):
        all_classes.extend(elem.get('class', []))
    
    # 클래스 빈도 계산
    from collections import Counter
    class_counts = Counter(all_classes)
    structure["common_classes"] = [
        {"class": cls, "count": count}
        for cls, count in class_counts.most_common(10)
    ]
    
    # ID 목록
    for elem in soup.find_all(id=True, limit=max_elements):
        elem_id = elem.get('id')
        if elem_id:
            structure["ids"].append({
                "id": elem_id,
                "tag": elem.name
            })
    
    return structure


@tool
def analyze_blog_author(url: str) -> Dict[str, Any]:
    """
    Analyze blog author information and writing style by examining multiple posts
    
    Args:
        url: Blog homepage URL
    
    Returns:
        작성자 정보 및 블로그 분석 (이름, 주요 주제, 작성 스타일 등)
    """
    # 홈페이지 정보
    overview = fetch_homepage_overview.invoke({"url": url})
    if isinstance(overview, dict) and "error" in overview:
        return overview
    
    # 최근 게시물 가져오기
    posts = list_recent_posts.invoke({"url": url, "max_posts": 5})
    if not posts or (isinstance(posts, list) and posts and "error" in posts[0]):
        return {"error": "Failed to fetch posts"}
    
    # 분석 결과 구성
    analysis = {
        "blog_url": url,
        "blog_title": overview.get("title", ""),
        "blog_description": overview.get("description", ""),
        "author": overview.get("author", ""),
        "category_count": overview.get("category_count", 0),
        "categories": [cat["name"] for cat in overview.get("categories", [])[:10]],
        "recent_posts_count": len(posts),
        "recent_post_titles": [post.get("title", "") for post in posts],
        "topics": [],
        "style_notes": []
    }
    
    # 주제 추출 (카테고리와 게시물 제목에서)
    topics = set()
    for cat in overview.get("categories", []):
        topics.add(cat["name"])
    
    for post in posts:
        title = post.get("title", "")
        # 기술 키워드 추출
        tech_keywords = ["LLM", "AI", "ML", "Python", "SQL", "Agent", "프로젝트", "논문", "리뷰"]
        for keyword in tech_keywords:
            if keyword in title:
                topics.add(keyword)
    
    analysis["topics"] = list(topics)[:15]
    
    # 스타일 노트
    if len(posts) >= 3:
        analysis["style_notes"].append(f"최근 {len(posts)}개 게시물 활동 확인됨")
    
    if overview.get("categories"):
        analysis["style_notes"].append(f"{len(overview['categories'])}개 카테고리로 체계적 분류")
    
    return analysis


# 모든 Blog 도구를 리스트로 export
BLOG_TOOLS = [
    fetch_homepage_overview,
    list_recent_posts,
    fetch_post_content,
    extract_blog_categories,
    inspect_page_structure,
    analyze_blog_author,
]

