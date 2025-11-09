import requests
from bs4 import BeautifulSoup
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage
from multi_agents.states.states import State
from typing import Dict, List, cast, Optional, Any
from configs import *
from langchain_core.tools import tool
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

# 세션 초기화 (스크래핑용)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

def _scrape_page(url: str) -> Optional[BeautifulSoup]:
    """웹 페이지 스크래핑 헬퍼 함수"""
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
        return None
    except:
        return None

@tool
def scrape_user_profile(username: str) -> Dict[str, Any]:
    """
    Scrape GitHub user profile information from their main page
    
    Args:
        username: GitHub username
    
    Returns:
        사용자 프로필 정보 딕셔너리
    """
    soup = _scrape_page(f"https://github.com/{username}")
    if not soup:
        return {"error": "Failed to scrape profile"}

    result = {
        "username": username, "name": None, "bio": None, "location": None,
        "company": None, "followers": None, "following": None, "repositories": None
    }

    name_elem = soup.select_one('.vcard-fullname')
    if name_elem: result["name"] = name_elem.text.strip()

    bio_elem = soup.select_one('.user-profile-bio > div')
    if bio_elem: result["bio"] = bio_elem.text.strip()

    for item in soup.select('.vcard-detail'):
        text = item.text.strip()
        if 'location' in str(item):
            result["location"] = text
        elif 'organization' in str(item):
            result["company"] = text

    for link in soup.select('a.Link--secondary'):
        href = link.get('href', '')
        text = link.text.strip()
        if 'followers' in href:
            result["followers"] = text.split()[0]
        elif 'following' in href:
            result["following"] = text.split()[0]

    repo_count = soup.select_one('span.Counter')
    if repo_count:
        result["repositories"] = repo_count.text.strip()

    return result

@tool
def scrape_user_repos(username: str, page: int = 1) -> Dict[str, Any]:
    """
    Scrape list of repositories from user's repositories tab
    
    Args:
        username: GitHub username
        page: Page number for pagination
    
    Returns:
        Dictionary containing list of repositories and count
    """
    url = f"https://github.com/{username}?tab=repositories"
    if page > 1: url += f"&page={page}"
    soup = _scrape_page(url)
    if not soup:
        return {"error": "Failed to scrape repositories"}

    repos = []
    for repo_elem in soup.select('#user-repositories-list > ul > li'):
        repo_data = {}
        name_elem = repo_elem.select_one('a[itemprop="name codeRepository"]')
        if name_elem:
            repo_data["name"] = name_elem.text.strip()
            repo_data["url"] = f"https://github.com{name_elem.get('href','')}"
        desc_elem = repo_elem.select_one('p[itemprop="description"]')
        if desc_elem: repo_data["description"] = desc_elem.text.strip()
        lang_elem = repo_elem.select_one('[itemprop="programmingLanguage"]')
        if lang_elem: repo_data["language"] = lang_elem.text.strip()
        star_elem = repo_elem.select_one('a[href*="stargazers"]')
        if star_elem: repo_data["stars"] = star_elem.text.strip()
        fork_elem = repo_elem.select_one('a[href*="forks"]')
        if fork_elem: repo_data["forks"] = fork_elem.text.strip()
        time_elem = repo_elem.select_one('relative-time')
        if time_elem: repo_data["updated"] = time_elem.get('datetime', '')
        if repo_data.get("name"): repos.append(repo_data)
    return {"repositories": repos, "count": len(repos)}

@tool
def scrape_repo_main_page(owner: str, repo: str) -> Dict[str, Any]:
    """
    Scrape repository main page for basic info and README
    
    Args:
        owner: Repository owner username
        repo: Repository name
    
    Returns:
        Dictionary containing repository info, README, etc.
    """
    soup = _scrape_page(f"https://github.com/{owner}/{repo}")
    if not soup:
        return {"error": "Failed to scrape repository"}

    result = {
        "name": repo, "owner": owner, "description": None, "stars": None,
        "forks": None, "watching": None, "readme": None, "languages": {}, "about": {}
    }

    desc_elem = soup.select_one('p.f4')
    if desc_elem: result["description"] = desc_elem.text.strip()

    for elem in soup.select('#repo-content-pjax-container a.Link--muted'):
        href = elem.get('href',''); text = elem.text.strip()
        if '/stargazers' in href: result["stars"] = text.split()[0]
        elif '/forks' in href: result["forks"] = text.split()[0]
        elif '/watchers' in href: result["watching"] = text.split()[0]

    readme_elem = soup.select_one('article.markdown-body')
    if readme_elem:
        readme_text = readme_elem.get_text(separator='\n', strip=True)
        result["readme"] = readme_text[:3000]

    for lang_elem in soup.select('.BorderGrid-cell span[itemprop="programmingLanguage"]'):
        lang = lang_elem.text.strip()
        percent_elem = lang_elem.find_next('span', class_='ml-1')
        if percent_elem:
            result["languages"][lang] = percent_elem.text.strip()

    about_elem = soup.select_one('.BorderGrid')
    if about_elem:
        for link in about_elem.select('a'):
            text = link.text.strip()
            if 'release' in link.get('href',''):
                result["about"]["releases"] = text
            elif 'commit' in link.get('href',''):
                result["about"]["commits"] = text
            elif 'contributor' in link.get('href',''):
                result["about"]["contributors"] = text

    return result

@tool
def scrape_repo_commits(owner: str, repo: str) -> Dict[str, Any]:
    """
    Scrape recent commits from repository
    
    Args:
        owner: Repository owner username
        repo: Repository name
    
    Returns:
        Dictionary containing list of commits and count
    """
    soup = _scrape_page(f"https://github.com/{owner}/{repo}/commits")
    if not soup:
        return {"error": "Failed to scrape commits"}

    commits = []
    for commit_elem in soup.select('.Box-row')[:10]:
        commit_data = {}
        msg_elem = commit_elem.select_one('a.Link--primary')
        if msg_elem: commit_data["message"] = msg_elem.text.strip()
        author_elem = commit_elem.select_one('a.commit-author')
        if author_elem: commit_data["author"] = author_elem.text.strip()
        time_elem = commit_elem.select_one('relative-time')
        if time_elem: commit_data["date"] = time_elem.get('datetime','')
        hash_elem = commit_elem.select_one('a.text-mono')
        if hash_elem: commit_data["sha"] = hash_elem.text.strip()
        if commit_data: commits.append(commit_data)
    return {"commits": commits, "count": len(commits)}

@tool
def scrape_repo_files(owner: str, repo: str) -> Dict[str, Any]:
    """
    Scrape repository file structure
    
    Args:
        owner: Repository owner username
        repo: Repository name
    
    Returns:
        Dictionary containing list of files and count
    """
    soup = _scrape_page(f"https://github.com/{owner}/{repo}")
    if not soup:
        return {"error": "Failed to scrape files"}
    files = []
    for row in soup.select('div[role="row"]'):
        name_elem = row.select_one('a.Link--primary')
        if name_elem:
            name = name_elem.text.strip()
            icon = row.select_one('svg')
            file_type = "file"
            if icon and 'directory' in str(icon):
                file_type = "directory"
            files.append({"name": name, "type": file_type})
    return {"files": files, "count": len(files)}

async def github_agent(state: State) -> Dict[str, List[AIMessage]]:
    """
    Analyze GitHub profile and repository information
    """

    model = ChatOpenAI(model=AGENT_MODEL, temperature=0, api_key=OPENAI_API_KEY)

    username = state.github_url.rstrip('/').split('/')[-1] if 'github.com/' in state.github_url else state.github_url
    # LangChain tool 데코레이터로 정의된 도구들을 사용
    tools = [
        scrape_user_profile,
        scrape_user_repos,
        scrape_repo_main_page,
        scrape_repo_commits,
        scrape_repo_files
    ]

    system_message = f"""당신은 GitHub 저장소 분석 전문가입니다.
    웹 스크래핑 도구를 사용하여 GitHub 프로필과 저장소를 분석합니다.
    
    username: {username}

    You are a GitHub repository analyst with web scraping tools.
    Analyze GitHub profiles and repositories by scraping public web pages.
    Always respond in Korean.
    
    Available scraping tools:
    - scrape_user_profile: Get user profile information
    - scrape_user_repos: Get list of repositories
    - scrape_repo_main_page: Get repository details and README
    - scrape_repo_commits: Get recent commits
    - scrape_repo_files: Get file structure
    
    IMPORTANT INSTRUCTIONS:
    1. Use tools strategically to gather information (maximum 3-4 tool calls)
    2. After collecting sufficient information, provide a comprehensive Korean summary
    3. Do NOT continue using tools indefinitely - stop when you have enough information
    4. Your final response should be a complete analysis in Korean, not a request for more tools
    
    Process:
    1. Start with scrape_user_profile or scrape_repo_main_page for basic info
    2. Use 1-2 additional tools if needed for specific details
    3. Provide final comprehensive summary in Korean and STOP
    """

    prompt = PromptTemplate.from_template(system_message)
    agent = create_react_agent(model, tools, prompt=prompt)

    # recursion_limit 설정으로 무한 루프 방지
    config = {"recursion_limit": 10, "max_iterations": 5}
    response = await agent.ainvoke({"messages": state.messages}, config=config)
    print("response: ", response)

    # messages = [SystemMessage(content=system_message), *state.messages]
    # response = await agent.ainvoke({"messages": messages})
    
    
    return {
        "messages": [response["messages"][-1]],
        "agent_name": "github_agent",
        "company_summary": response["messages"][-1].content,
    }
