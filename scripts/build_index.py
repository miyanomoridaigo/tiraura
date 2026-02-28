#!/usr/bin/env python3
"""
build_index.py
--------------
novels-config.json に列挙された各小説リポジトリから meta.json を取得し、
chapters の数を数えて novels-index.json を生成するスクリプト。

GitHub Actions から実行される。GITHUB_TOKEN 環境変数を使用する。
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests
except ImportError:
    print("requests がインストールされていません。pip install requests を実行してください。")
    sys.exit(1)

# ── 設定 ─────────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

CONFIG_PATH = Path(__file__).parent.parent / "novels-config.json"
OUTPUT_PATH = Path(__file__).parent.parent / "novels-index.json"


def normalize_repo(repo: str) -> str:
    """
    repo フィールドが URL 形式 (https://github.com/owner/name.git など) でも
    リポジトリ名だけを返す。すでに名前だけの場合はそのまま返す。
    """
    # https://github.com/owner/name.git や github.com/owner/name の形式に対応
    match = re.search(r'github\.com/[^/]+/([^/\s]+?)(?:\.git)?$', repo)
    if match:
        return match.group(1)
    return repo.rstrip('/')


def github_get(url: str, retries: int = 3) -> Optional[requests.Response]:
    """GitHub API または raw URL を GET する。レート制限時は待機してリトライ。"""
    for attempt in range(retries):
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r
        if r.status_code == 403 and "rate limit" in r.text.lower():
            wait = 60 * (attempt + 1)
            print(f"  ⚠ レート制限。{wait}秒待機します...")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return None
        print(f"  ⚠ HTTP {r.status_code}: {url}")
        return None
    return None


def fetch_meta(owner: str, repo: str, branch: str) -> Optional[dict]:
    """リポジトリから meta.json を取得する。"""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/meta.json"
    r = github_get(url)
    if r is None:
        print(f"  ⚠ meta.json が見つかりません: {owner}/{repo}")
        return None
    try:
        return r.json()
    except Exception as e:
        print(f"  ⚠ meta.json の JSON パースエラー: {e}")
        return None


def count_chapters(owner: str, repo: str, branch: str) -> Tuple[int, Optional[str]]:
    """
    リポジトリ直下の 1.txt, 2.txt ... を数えて (最大番号, 最終更新日時) を返す。
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/?ref={branch}"
    r = github_get(url)
    if r is None:
        return 0, None

    files = r.json()
    if not isinstance(files, list):
        return 0, None

    nums = []
    for f in files:
        name = f.get("name", "")
        stem = name[:-4] if name.lower().endswith(".txt") else None
        if stem and stem.isdigit():
            nums.append(int(stem))

    if not nums:
        return 0, None

    count = max(nums)
    return count, None


def fetch_last_commit_date(owner: str, repo: str, branch: str) -> Optional[str]:
    """リポジトリの最新コミット日時を取得する。"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{branch}"
    r = github_get(url)
    if r is None:
        return None
    try:
        data = r.json()
        return data["commit"]["committer"]["date"]
    except Exception:
        return None


def build_index():
    print(f"📖 novels-config.json を読み込み中: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    site_info = config.get("site", {"title": "Web小説サイト", "description": ""})
    repositories = config.get("repositories", [])

    if not repositories:
        print("⚠ novels-config.json にリポジトリが登録されていません。")

    novels = []
    for repo_info in repositories:
        owner = repo_info.get("owner", "").strip()
        repo = normalize_repo(repo_info.get("repo", "").strip())
        branch = repo_info.get("branch", "main").strip()

        if not owner or not repo:
            print(f"  ⚠ owner または repo が空です: {repo_info}")
            continue

        print(f"\n📚 処理中: {owner}/{repo} (branch: {branch})")

        # --- meta.json を取得 ---
        meta = fetch_meta(owner, repo, branch) or {}

        # --- 話数をカウント ---
        chapter_count, _ = count_chapters(owner, repo, branch)
        print(f"  ✅ {chapter_count} 話が見つかりました")

        # --- 最終コミット日時 ---
        updated_at = fetch_last_commit_date(owner, repo, branch)
        if not updated_at:
            updated_at = meta.get("updated_at", "")

        entry = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            # meta.json の値を優先、なければフォールバック
            "title": meta.get("title") or repo,
            "description": meta.get("description") or "",
            "author": meta.get("author") or owner,
            "tags": meta.get("tags") or [],
            "cover": meta.get("cover") or "",
            "status": meta.get("status") or "連載中",
            "created_at": meta.get("created_at") or "",
            "updated_at": updated_at,
            "chapter_count": chapter_count,
        }
        novels.append(entry)
        print(f"  📝 タイトル: {entry['title']} / 著者: {entry['author']}")

    # --- novels-index.json を出力 ---
    output = {
        "site": site_info,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "novels": novels,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(novels)} 作品を novels-index.json に書き込みました。")


if __name__ == "__main__":
    build_index()
