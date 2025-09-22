import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

class GitHubScraperAgent:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.primary_model = "gpt-5-mini"
        self.fallback_models = ["gpt-5-nano", "gpt-4.1", "gpt-4o-mini"]

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "scrape_user_profile",
                    "description": "Scrape GitHub user profile information from their main page",
                    "parameters": {
                        "type": "object",
                        "properties": {"username": {"type": "string", "description": "GitHub username"}},
                        "required": ["username"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_user_repos",
                    "description": "Scrape list of repositories from user's repositories tab",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "username": {"type": "string", "description": "GitHub username"},
                            "page": {"type": "integer", "description": "Page number for pagination", "default": 1}
                        },
                        "required": ["username"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_repo_main_page",
                    "description": "Scrape repository main page for basic info and README",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "Repository owner username"},
                            "repo": {"type": "string", "description": "Repository name"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_repo_commits",
                    "description": "Scrape recent commits from repository",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "Repository owner username"},
                            "repo": {"type": "string", "description": "Repository name"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrape_repo_files",
                    "description": "Scrape repository file structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "Repository owner username"},
                            "repo": {"type": "string", "description": "Repository name"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            }
        ]

    def _scrape_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return BeautifulSoup(r.text, 'html.parser')
            return None
        except:
            return None

    def execute_function(self, function_name: str, arguments: Dict) -> Any:
        if function_name == "scrape_user_profile":
            username = arguments['username']
            soup = self._scrape_page(f"https://github.com/{username}")
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

        elif function_name == "scrape_user_repos":
            username = arguments['username']
            page = arguments.get('page', 1)
            url = f"https://github.com/{username}?tab=repositories"
            if page > 1: url += f"&page={page}"
            soup = self._scrape_page(url)
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

        elif function_name == "scrape_repo_main_page":
            owner = arguments['owner']; repo = arguments['repo']
            soup = self._scrape_page(f"https://github.com/{owner}/{repo}")
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

        elif function_name == "scrape_repo_commits":
            owner = arguments['owner']; repo = arguments['repo']
            soup = self._scrape_page(f"https://github.com/{owner}/{repo}/commits")
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

        elif function_name == "scrape_repo_files":
            owner = arguments['owner']; repo = arguments['repo']
            soup = self._scrape_page(f"https://github.com/{owner}/{repo}")
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

        else:
            return {"error": f"Unknown function: {function_name}"}

    def _chat_with_tools(self, messages: List[Dict[str, Any]], model: str):
        payload = {
            "model": model,
            "messages": messages,
            "tools": self.tools,
            "tool_choice": "auto"
        }
        print(f"[OpenAI] Trying model: {model}")
        return requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )

    def _chat_with_fallbacks(self, messages: List[Dict[str, Any]]):
        order = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        for m in order:
            resp = self._chat_with_tools(messages, m)
            if resp.status_code == 200:
                data = resp.json()
                actual = data.get("model", m)
                print(f"[OpenAI] Using model: {actual}")
                return resp, actual
            else:
                try:
                    err = resp.json().get("error", {})
                    print(f"[OpenAI][Fail] {m} -> {resp.status_code} {err.get('type') or ''} {err.get('code') or ''} {err.get('message') or resp.text[:200]}")
                except Exception:
                    print(f"[OpenAI][Fail] {m} -> {resp.status_code} {resp.text[:200]}")
        return None, None

    def analyze(self, github_url: str, query: str) -> str:
        username = github_url.rstrip('/').split('/')[-1] if 'github.com/' in github_url else github_url
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a GitHub repository analyst with web scraping tools.\n"
                    "Analyze GitHub profiles and repositories by scraping public web pages.\n"
                    "Use the provided tools as many times as needed to gather information.\n"
                    "Always respond in Korean.\n\n"
                    "Available scraping tools:\n"
                    "- scrape_user_profile: Get user profile information\n"
                    "- scrape_user_repos: Get list of repositories\n"
                    "- scrape_repo_main_page: Get repository details and README\n"
                    "- scrape_repo_commits: Get recent commits\n"
                    "- scrape_repo_files: Get file structure\n\n"
                    "Use tools strategically to answer the user's query comprehensively."
                )
            },
            {"role": "user", "content": f"GitHub 사용자: {username}\n\n질문: {query}"}
        ]

        max_iterations = 10
        for i in range(max_iterations):
            try:
                print(f"[Loop] Iteration: {i+1}")
                resp, used_model = self._chat_with_fallbacks(messages)
                if resp is None:
                    return "API Error: All models failed"

                data = resp.json()
                if not data.get("choices"):
                    print("[OpenAI] Error: No choices")
                    return f"API Error: No choices in response ({used_model})"

                choice = data["choices"][0]
                message = choice.get("message", {})
                tool_calls = message.get("tool_calls")

                if tool_calls:
                    messages.append(message)
                    for tc in tool_calls:
                        fn_name = tc["function"]["name"]
                        raw_args = tc["function"].get("arguments", "{}")
                        if isinstance(raw_args, str):
                            try:
                                fn_args = json.loads(raw_args) if raw_args else {}
                            except Exception:
                                fn_args = {}
                        elif isinstance(raw_args, dict):
                            fn_args = raw_args
                        else:
                            fn_args = {}
                        print(f"[ToolCall] name={fn_name} args={json.dumps(fn_args, ensure_ascii=False)}")
                        result = self.execute_function(fn_name, fn_args)
                        print(f"[ToolResult] name={fn_name} type={'error' if isinstance(result, dict) and 'error' in result else 'ok'}")
                        messages.append({"role":"tool","tool_call_id": tc["id"], "content": json.dumps(result, ensure_ascii=False)})
                    print("[Reason] Tool results added → follow-up call to model")
                    continue

                content = message.get("content")
                if content:
                    print("[OpenAI] Final answer produced without further tool use")
                    return content

                print("[OpenAI] Empty content")
                return "분석 결과가 비어 있습니다."

            except Exception as e:
                print(f"[Runtime] Exception: {e}")
                return f"Error: {str(e)}"

        print("[Loop] Max iterations reached")
        return "분석을 완료할 수 없습니다 (최대 반복 횟수 초과)"

if __name__ == "__main__":
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("필요한 패키지를 설치하세요:")
        print("pip install beautifulsoup4 requests")
        exit(1)
    
    OPENAI_API_KEY = ""
    GITHUB_URL = "https://github.com/Pseudo-Lab"
    QUERY = "JobPT 레포에서 cv를 위해서 정보 요약하고 주요 코드 요약해서 알려줘"
    
    agent = GitHubScraperAgent(OPENAI_API_KEY)
    result = agent.analyze(GITHUB_URL, QUERY)
    
    print("\n" + "=" * 60)
    print("분석 결과:")
    print("=" * 60)
    print(result)