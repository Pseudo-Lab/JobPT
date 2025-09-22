import json
import base64
import requests
from typing import List, Dict, Any, Optional

class GitHubToolAgent:
    def __init__(self, github_token:str, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.github_base_url = "https://api.github.com"
        self.primary_model = "gpt-5-mini"
        self.github_token = github_token
        self.fallback_models = ["gpt-5-nano", "gpt-4.1", "gpt-4o-mini"]
        self.tools = [
            {"type":"function","function":{"name":"get_user_info","description":"Get GitHub user profile information","parameters":{"type":"object","properties":{"username":{"type":"string","description":"GitHub username"}},"required":["username"]}}},
            {"type":"function","function":{"name":"list_user_repos","description":"List repositories for a GitHub user","parameters":{"type":"object","properties":{"username":{"type":"string","description":"GitHub username"},"limit":{"type":"integer","description":"Maximum number of repos to return","default":30},"sort":{"type":"string","description":"Sort by: updated, created, pushed, full_name","default":"updated"}},"required":["username"]}}},
            {"type":"function","function":{"name":"get_repo_details","description":"Get detailed information about a specific repository","parameters":{"type":"object","properties":{"owner":{"type":"string","description":"Repository owner username"},"repo":{"type":"string","description":"Repository name"}},"required":["owner","repo"]}}},
            {"type":"function","function":{"name":"get_repo_readme","description":"Get README content of a repository","parameters":{"type":"object","properties":{"owner":{"type":"string","description":"Repository owner username"},"repo":{"type":"string","description":"Repository name"}},"required":["owner","repo"]}}},
            {"type":"function","function":{"name":"get_repo_commits","description":"Get recent commits from a repository","parameters":{"type":"object","properties":{"owner":{"type":"string","description":"Repository owner username"},"repo":{"type":"string","description":"Repository name"},"limit":{"type":"integer","description":"Number of commits to return","default":5}},"required":["owner","repo"]}}},
            {"type":"function","function":{"name":"get_repo_languages","description":"Get programming languages used in a repository","parameters":{"type":"object","properties":{"owner":{"type":"string","description":"Repository owner username"},"repo":{"type":"string","description":"Repository name"}},"required":["owner","repo"]}}},
            {"type":"function","function":{"name":"get_repo_contributors","description":"Get contributors of a repository","parameters":{"type":"object","properties":{"owner":{"type":"string","description":"Repository owner username"},"repo":{"type":"string","description":"Repository name"},"limit":{"type":"integer","description":"Number of contributors to return","default":10}},"required":["owner","repo"]}}}
        ]
        self._probe_cache: Dict[str, Optional[Dict[str,str]]] = {}
        self._block_models = set()

    def _build_github_headers(self, extra: dict = None) -> dict:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        if extra:
            headers.update(extra)
        return headers

    def _github_api_call(self, endpoint: str, params: Optional[Dict] = None, etag: Optional[str] = None) -> Any:
        headers = self._build_github_headers()
        if etag:
            headers["If-None-Match"] = etag 
        try:
            r = requests.get(f"{self.github_base_url}{endpoint}", headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                return {"status":200, "data": r.json(), "etag": r.headers.get("ETag")}
            if r.status_code == 304:
                return {"status":304, "data": None, "etag": etag}
            try:
                err_json = r.json()
            except Exception:
                err_json = {"message": r.text}
            return {"error": f"GitHub API {r.status_code}", "detail": err_json, "endpoint": endpoint, "params": params, "status_code": r.status_code}
        except Exception as e:
            return {"error": str(e), "endpoint": endpoint, "params": params}

    def _probe_model(self, model: str) -> bool:
        if model in self._probe_cache:
            ok = self._probe_cache[model] is None
            if ok:
                print(f"[OpenAI][Probe] {model} OK (cached)")
            else:
                e = self._probe_cache[model]
                print(f"[OpenAI][Probe] {model} unavailable (cached): {e.get('status')} {e.get('type') or ''} {e.get('code') or ''} {e.get('message')[:160] if e.get('message') else ''}")
            return ok
        try:
            r = requests.get(f"https://api.openai.com/v1/models/{model}", headers={"Authorization": f"Bearer {self.openai_api_key}"}, timeout=20)
            if r.status_code == 200:
                self._probe_cache[model] = None
                print(f"[OpenAI][Probe] {model} OK")
                return True
            try:
                err = r.json().get("error", {})
            except Exception:
                err = {"message": r.text}
            self._probe_cache[model] = {"status": r.status_code, "type": err.get("type"), "code": err.get("code"), "message": err.get("message")}
            print(f"[OpenAI][Probe] {model} unavailable: {r.status_code} {err.get('type') or ''} {err.get('code') or ''} {err.get('message')[:160] if err.get('message') else ''}")
            return False
        except Exception as e:
            self._probe_cache[model] = {"status": "EXC", "type": None, "code": None, "message": str(e)}
            print(f"[OpenAI][Probe] {model} exception: {e}")
            return False

    def _chat_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], model: str):
        payload = {"model": model, "messages": messages, "tools": tools, "tool_choice": "auto",}
        print(f"[OpenAI] Trying model: {model}")
        return requests.post("https://api.openai.com/v1/chat/completions",
                             headers={"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"},
                             json=payload, timeout=60)

    def _print_fail(self, model: str, resp):
        try:
            j = resp.json()
            err = j.get("error", {})
            print(f"[OpenAI][Fail] {model} -> {resp.status_code} {err.get('type') or ''} {err.get('code') or ''} {err.get('message')[:200] if err.get('message') else resp.text[:200]}")
            if err.get("code") in {"model_not_found","insufficient_quota"} or resp.status_code in {401,403,404}:
                self._block_models.add(model)
        except Exception:
            print(f"[OpenAI][Fail] {model} -> {resp.status_code} {resp.text[:200]}")

    def _chat_with_fallbacks(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]):
        order = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        for m in order:
            if m in self._block_models:
                print(f"[OpenAI][Skip] {m} blocked in this session")
                continue
            if not self._probe_model(m):
                self._block_models.add(m)
                continue
            resp = self._chat_with_tools(messages, tools, m)
            if resp.status_code == 200:
                data = resp.json()
                actual = data.get("model", m)
                print(f"[OpenAI] Using model: {actual}")
                return resp, actual, None
            self._print_fail(m, resp)
        return None, None, "All models failed or unavailable"

    def execute_function(self, function_name: str, arguments: Dict) -> Any:
        if function_name == "get_user_info":
            return self._github_api_call(f"/users/{arguments['username']}")
        elif function_name == "list_user_repos":
            username = arguments["username"]; limit = arguments.get("limit", 30); sort = arguments.get("sort", "updated")
            repos = []; page = 1
            while len(repos) < limit:
                data = self._github_api_call(f"/users/{username}/repos", {"per_page": min(50, limit - len(repos)), "page": page, "sort": sort})
                if isinstance(data, dict) and "error" in data: return data
                if not data: break
                repos.extend(data)
                if len(data) < 30: break
                page += 1
                if page > 5: break
            return repos[:limit]
        elif function_name == "get_repo_details":
            return self._github_api_call(f"/repos/{arguments['owner']}/{arguments['repo']}")
        elif function_name == "get_repo_readme":
            data = self._github_api_call(f"/repos/{arguments['owner']}/{arguments['repo']}/readme")
            if isinstance(data, dict) and data.get("content"):
                try:
                    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                    return {"content": content[:5000]}
                except Exception as e:
                    return {"error": f"Failed to decode README: {e}"}
            return data
        elif function_name == "get_repo_commits":
            limit = arguments.get("limit", 5)
            return self._github_api_call(f"/repos/{arguments['owner']}/{arguments['repo']}/commits", {"per_page": limit})
        elif function_name == "get_repo_languages":
            return self._github_api_call(f"/repos/{arguments['owner']}/{arguments['repo']}/languages")
        elif function_name == "get_repo_contributors":
            limit = arguments.get("limit", 10)
            return self._github_api_call(f"/repos/{arguments['owner']}/{arguments['repo']}/contributors", {"per_page": limit})
        else:
            return {"error": f"Unknown function: {function_name}"}

    def analyze(self, github_url: str, query: str) -> str:
        username = github_url.rstrip("/").split("/")[-1] if "github.com/" in github_url else github_url
        messages: List[Dict[str, Any]] = [
            {"role":"system","content":"You are a GitHub repository analyst with access to GitHub API tools.\nAnalyze the given GitHub profile/repositories based on the user's query.\nUse the provided tools as many times as needed to gather sufficient information.\nAlways respond in Korean.\n\nAvailable information from GitHub API:\n- User profile information\n- Repository lists and details\n- README files\n- Commit history\n- Programming languages used\n- Contributors\n\nUse tools strategically to answer the user's query comprehensively."},
            {"role":"user","content":f"GitHub 사용자: {username}\n\n질문: {query}"}
        ]
        max_iterations = 10
        for i in range(max_iterations):
            try:
                print(f"[Loop] Iteration: {i+1}")
                resp, used_model, err = self._chat_with_fallbacks(messages, self.tools)
                if resp is None:
                    print(f"[OpenAI] Error: {err}")
                    return f"API Error: {err}"
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
                            try: fn_args = json.loads(raw_args) if raw_args else {}
                            except Exception: fn_args = {}
                        elif isinstance(raw_args, dict):
                            fn_args = raw_args
                        else:
                            fn_args = {}
                        print(f"[ToolCall] name={fn_name} args={json.dumps(fn_args, ensure_ascii=False)}")
                        result = self.execute_function(fn_name, fn_args)
                        print(f"[ToolResult] name={fn_name} type={'error' if isinstance(result, dict) and 'error' in result else 'ok'}")
                        messages.append({"role":"tool","tool_call_id":tc["id"],"content":json.dumps(result, ensure_ascii=False)})
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
        print("[Loop] Max iterations reached]")
        return "분석을 완료할 수 없습니다 (최대 반복 횟수 초과)"

if __name__ == "__main__":
    OPENAI_API_KEY = ""
    GITHUB_TOKEN = ""
    GITHUB_URL = "https://github.com/Pseudo-Lab"
    QUERY = "JobPT 레포에서 최신 커밋에 대해 요약 설명해줘"
    
    agent = GitHubToolAgent(GITHUB_TOKEN, OPENAI_API_KEY)
    result = agent.analyze(GITHUB_URL, QUERY)
    
    print("=" * 60)
    print("분석 결과:")
    print("=" * 60)
    print(result)