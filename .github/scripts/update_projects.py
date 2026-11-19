#!/usr/bin/env python3
"""Refresh the profile README with the latest public repositories."""

import base64
import json
import os
import urllib.request

OWNER = "2N3ll"
PROFILE_REPO = "2N3ll"
README_PATH = "README.md"
API = "https://api.github.com"


def api_request(url, token, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        return json.loads(body) if body else {}


def make_project_list(repositories):
    public_repos = [
        repo for repo in repositories
        if not repo.get("private", True)
        and not repo.get("fork", False)
        and not repo.get("archived", False)
        and repo.get("name", "").lower() != PROFILE_REPO.lower()
    ]
    public_repos.sort(
        key=lambda repo: repo.get("pushed_at") or repo.get("updated_at") or "",
        reverse=True,
    )
    selected = public_repos[:6]
    if not selected:
        return "_New public projects will appear here as they are published._"

    rows = [
        "| Project | Description | Language | Stars |",
        "|:--|:--|:--:|--:|",
    ]
    for repo in selected:
        name = repo["name"]
        url = repo["html_url"]
        description = (repo.get("description") or "No description provided.")
        description = description.replace("|", "\\|").replace("\n", " ")
        if len(description) > 100:
            description = description[:97].rstrip() + "..."
        language = repo.get("language") or "—"
        stars = repo.get("stargazers_count", 0)
        rows.append(f"| [**{name}**]({url}) | {description} | {language} | ⭐ {stars} |")
    return "\n".join(rows)


def main():
    token = os.environ["GITHUB_TOKEN"]
    owner = os.environ.get("GITHUB_OWNER", OWNER)
    repo = os.environ.get("GITHUB_REPOSITORY", f"{owner}/{PROFILE_REPO}")
    api_root = f"{API}/repos/{repo}/contents/{README_PATH}"

    repositories = api_request(
        f"{API}/users/{owner}/repos?type=owner&sort=updated&per_page=100",
        token,
    )
    readme = api_request(api_root, token)
    current = base64.b64decode(readme["content"]).decode("utf-8")
    start = "<!-- PROJECTS:START -->"
    end = "<!-- PROJECTS:END -->"
    if start not in current or end not in current:
        raise RuntimeError("README project markers are missing; refusing to overwrite it.")

    generated = make_project_list(repositories)
    before, remainder = current.split(start, 1)
    _, after = remainder.split(end, 1)
    updated = f"{before}{start}\n\n{generated}\n\n{end}{after}"
    if updated == current:
        print("README is already up to date.")
        return

    api_request(
        api_root,
        token,
        method="PUT",
        payload={
            "message": "chore: refresh public projects in profile README",
            "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
            "sha": readme["sha"],
        },
    )
    print("Successfully refreshed the public projects section.")


if __name__ == "__main__":
    main()
