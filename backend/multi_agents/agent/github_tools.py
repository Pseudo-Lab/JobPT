"""
GitHub API 기반 LangChain Tools
GitHub 사용자 및 레포지토리 정보를 조회하는 도구 모음
"""

import json
import base64
import requests
from typing import Dict, List, Optional, Any
from langchain_core.tools import tool
import os


def _build_github_headers() -> dict:
    """GitHub API 헤더 생성"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _github_api_call(endpoint: str, params: Optional[Dict] = None) -> Any:
    """GitHub API 호출 헬퍼 함수"""
    headers = _build_github_headers()
    try:
        r = requests.get(
            f"https://api.github.com{endpoint}",
            headers=headers,
            params=params,
            timeout=10
        )
        if r.status_code == 200:
            return r.json()
        try:
            err_json = r.json()
        except Exception:
            err_json = {"message": r.text}
        return {"error": f"GitHub API {r.status_code}", "detail": err_json}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_github_user_info(username: str) -> Dict[str, Any]:
    """
    Get GitHub user profile information using GitHub API
    
    Args:
        username: GitHub username or organization name
    
    Returns:
        사용자 프로필 정보 딕셔너리 (이름, bio, 팔로워 수, 레포지토리 수 등)
    """
    result = _github_api_call(f"/users/{username}")
    if isinstance(result, dict) and "error" not in result:
        return {
            "login": result.get("login"),
            "name": result.get("name"),
            "bio": result.get("bio"),
            "company": result.get("company"),
            "location": result.get("location"),
            "email": result.get("email"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "public_repos": result.get("public_repos"),
            "created_at": result.get("created_at"),
        }
    return result


@tool
def list_github_user_repos(username: str, limit: int = 10, sort: str = "updated") -> List[Dict[str, Any]]:
    """
    List repositories for a GitHub user or organization using GitHub API
    
    Args:
        username: GitHub username or organization name
        limit: Maximum number of repos to return (default: 10)
        sort: Sort by updated, created, pushed, or full_name (default: updated)
    
    Returns:
        레포지토리 리스트 (이름, 설명, 언어, 스타 수 등)
    """
    repos = []
    page = 1
    
    while len(repos) < limit:
        data = _github_api_call(
            f"/users/{username}/repos",
            {"per_page": min(100, limit - len(repos)), "page": page, "sort": sort}
        )
        if isinstance(data, dict) and "error" in data:
            return data
        if not data:
            break
        
        for repo in data:
            repos.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "language": repo.get("language"),
                "stargazers_count": repo.get("stargazers_count"),
                "forks_count": repo.get("forks_count"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
            })
        
        if len(data) < 100:
            break
        page += 1
        if page > 5:
            break
    
    return repos[:limit]


@tool
def get_github_repo_details(owner: str, repo: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific repository using GitHub API
    
    Args:
        owner: Repository owner username or organization name
        repo: Repository name
    
    Returns:
        레포지토리 상세 정보 딕셔너리 (설명, 스타 수, 포크 수, 라이센스 등)
    """
    result = _github_api_call(f"/repos/{owner}/{repo}")
    if isinstance(result, dict) and "error" not in result:
        return {
            "name": result.get("name"),
            "full_name": result.get("full_name"),
            "description": result.get("description"),
            "html_url": result.get("html_url"),
            "language": result.get("language"),
            "stargazers_count": result.get("stargazers_count"),
            "forks_count": result.get("forks_count"),
            "watchers_count": result.get("watchers_count"),
            "open_issues_count": result.get("open_issues_count"),
            "topics": result.get("topics", []),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "pushed_at": result.get("pushed_at"),
            "license": result.get("license", {}).get("name") if result.get("license") else None,
        }
    return result


@tool
def get_github_repo_readme(owner: str, repo: str) -> Dict[str, Any]:
    """
    Get README content of a repository using GitHub API
    
    Args:
        owner: Repository owner username or organization name
        repo: Repository name
    
    Returns:
        README 내용 (최대 5000자, 프로젝트 설명 및 사용법 포함)
    """
    data = _github_api_call(f"/repos/{owner}/{repo}/readme")
    if isinstance(data, dict) and data.get("content"):
        try:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            return {
                "content": content[:5000],
                "name": data.get("name"),
                "path": data.get("path")
            }
        except Exception as e:
            return {"error": f"Failed to decode README: {e}"}
    return data


@tool
def get_github_repo_commits(owner: str, repo: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent commits from a repository using GitHub API
    
    Args:
        owner: Repository owner username or organization name
        repo: Repository name
        limit: Number of commits to return (default: 5)
    
    Returns:
        최근 커밋 리스트 (커밋 메시지, 작성자, 날짜 등)
    """
    data = _github_api_call(f"/repos/{owner}/{repo}/commits", {"per_page": limit})
    if isinstance(data, list):
        commits = []
        for commit in data:
            commits.append({
                "sha": commit.get("sha"),
                "message": commit.get("commit", {}).get("message"),
                "author": commit.get("commit", {}).get("author", {}).get("name"),
                "date": commit.get("commit", {}).get("author", {}).get("date"),
                "html_url": commit.get("html_url"),
            })
        return commits
    return data


@tool
def get_github_repo_languages(owner: str, repo: str) -> Dict[str, int]:
    """
    Get programming languages used in a repository using GitHub API
    
    Args:
        owner: Repository owner username or organization name
        repo: Repository name
    
    Returns:
        사용된 프로그래밍 언어와 바이트 수 딕셔너리 (언어별 코드 비중)
    """
    return _github_api_call(f"/repos/{owner}/{repo}/languages")


@tool
def get_github_repo_contributors(owner: str, repo: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get contributors of a repository using GitHub API
    
    Args:
        owner: Repository owner username or organization name
        repo: Repository name
        limit: Number of contributors to return (default: 10)
    
    Returns:
        기여자 리스트 (사용자명, 기여 횟수 등)
    """
    data = _github_api_call(f"/repos/{owner}/{repo}/contributors", {"per_page": limit})
    if isinstance(data, list):
        contributors = []
        for contributor in data:
            contributors.append({
                "login": contributor.get("login"),
                "contributions": contributor.get("contributions"),
                "html_url": contributor.get("html_url"),
                "type": contributor.get("type"),
            })
        return contributors
    return data


# 모든 GitHub 도구를 리스트로 export
GITHUB_TOOLS = [
    get_github_user_info,
    list_github_user_repos,
    get_github_repo_details,
    get_github_repo_readme,
    get_github_repo_commits,
    get_github_repo_languages,
    get_github_repo_contributors,
]

