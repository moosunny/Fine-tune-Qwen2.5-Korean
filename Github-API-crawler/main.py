from fastapi import FastAPI, HTTPException, Query, Header
from typing import Optional
from datetime import datetime, time
import requests
from zoneinfo import ZoneInfo
from collections import defaultdict
import re

KST = ZoneInfo("Asia/Seoul")

app = FastAPI()

markdown_filter = re.compile(r"(!\[.*?\]\(.*?\)|http[s]?://)")
code_start_pattern = re.compile(
    r"^\s*(import |from |def |class |if |for |while |try|#include|public |private |let |const |function )"
)

def remove_markdown_links(text: str) -> str:
    lines = text.splitlines()
    return "\n".join([line for line in lines if not markdown_filter.search(line)])

def extract_meaningful_code(code: str) -> str:
    lines = code.splitlines()
    code_lines = []
    keep = False

    for line in lines:
        if code_start_pattern.search(line):
            keep = True
        if keep:
            code_lines.append(line)

    return "\n".join(code_lines).strip()

# 제외할 경로 키워드 리스트
EXCLUDE_PATH_KEYWORDS = [
    "__pycache__", "tests/", "docs/", ".github/", "node_modules/",
    "venv/", "build/", "dist/", "assets/", "images/"
]

def is_excluded_path(filepath: str) -> bool:
    return any(keyword in filepath for keyword in EXCLUDE_PATH_KEYWORDS)

@app.get("/commit_data")
async def get_commit_data(
    owner: str = Query(..., description="GitHub 사용자 이름"),
    repo: str = Query(..., description="레포 이름"),
    branch: str = Query(..., description= "브랜치 이름"),
    since: Optional[str] = Query(None, description="시작 날짜 (ISO 8601 형식)"),
    until: Optional[str] = Query(None, description="종료 날짜 (ISO 8601 형식)"),
    token: str = Header(...)
):
    """
    레포의 커밋 데이터, 파일 경로, 코드, 커밋 메시지, diff 호출
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    params = {"sha": branch, "until": until, "per_page": 100}
    if since:
        since_date = datetime.strptime(since, "%Y-%m-%d").date()
        since_dt = datetime.combine(since_date, time.min, tzinfo=KST)
        params['since'] = since_dt.isoformat()
    if until:
        until_date = datetime.strptime(until, "%Y-%m-%d").date()
        until_dt = datetime.combine(until_date, time.max, tzinfo=KST)
        params['until'] = until_dt.isoformat()

    commits_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    commits_res = requests.get(commits_url, headers=headers, params= params)

    if commits_res.status_code != 200:
        raise HTTPException(status_code=commits_res.status_code, detail=commits_res.json())

    commits = commits_res.json()
    file_data = defaultdict(lambda: {"filepath": "", "latest_code": "", "patches": []})

    for commit in commits:
        sha = commit.get("sha")
        commit_message = commit.get("commit", {}).get("message", "")

        detail_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
        detail_res = requests.get(detail_url, headers=headers, params= params)
        if detail_res.status_code != 200:
            continue

        commit_detail = detail_res.json()

        for file in commit_detail.get("files", []):
            filepath = file.get("filename", "")
            if is_excluded_path(filepath):
                continue  # 제외 경로일 경우 skip

            patch = file.get("patch", "")
            raw_url = file.get("raw_url", "")

            if not file_data[filepath]["latest_code"] and raw_url:
                latest_code_res = requests.get(raw_url, headers=headers)
                if latest_code_res.status_code == 200:
                    raw_code = latest_code_res.text
                    no_md = remove_markdown_links(raw_code)
                    meaningful_code = extract_meaningful_code(no_md)
                    file_data[filepath]["latest_code"] = meaningful_code

            filtered_patch = remove_markdown_links(patch) if patch else ""
            file_data[filepath]["filepath"] = filepath
            file_data[filepath]["patches"].append({
                "commit_message": commit_message,
                "patch": filtered_patch
            })

    return {
        "username": owner,
        "date": until,
        "repo": repo,
        "files": list(file_data.values())
    }