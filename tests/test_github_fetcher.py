from unittest.mock import MagicMock, patch

import pytest
import requests

from github_fetcher import fetch_github_repo_data


def _resp(status=200, json_data=None, content=b""):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = json_data or {}
    r.content = content
    r.text = content.decode()
    r.raise_for_status.side_effect = (
        requests.HTTPError(response=r) if status >= 400 else None
    )
    return r


def _session(routes):
    """Fake requests.Session whose get() answers by URL substring."""
    session = MagicMock()

    def get(url, **_):
        for needle, response in routes.items():
            if needle in url:
                return response
        return _resp(404)

    session.get.side_effect = get
    return session


TREE = {
    "tree": [
        {"type": "blob", "path": "README.md"},
        {"type": "blob", "path": "src/app.py"},
        {"type": "blob", "path": "logo.png"},
        {"type": "tree", "path": "src"},
    ]
}


@pytest.mark.parametrize(
    "url",
    ["https://gitlab.com/o/r", "https://github.com/only-owner", "not a url"],
)
def test_rejects_urls_that_are_not_github_repos(url):
    with pytest.raises(ValueError):
        fetch_github_repo_data(url)


def test_fetches_only_important_files_and_strips_dot_git():
    routes = {
        "git/trees/main": _resp(json_data=TREE),
        "/main/README.md": _resp(content=b"# hi"),
        "/main/src/app.py": _resp(content=b"print(1)"),
    }
    with patch("github_fetcher.requests.Session", return_value=_session(routes)):
        data = fetch_github_repo_data("https://github.com/octo/demo.git")
    assert (data["owner"], data["repo"], data["branch"]) == ("octo", "demo", "main")
    assert sorted(data["files_found"]) == ["README.md", "src/app.py"]  # no png, no tree
    assert data["file_contents"]["src/app.py"] == "print(1)"


def test_falls_back_to_master_when_main_is_missing():
    routes = {
        "git/trees/master": _resp(json_data=TREE),
        "/master/README.md": _resp(content=b"x"),
        "/master/src/app.py": _resp(content=b"y"),
    }
    with patch("github_fetcher.requests.Session", return_value=_session(routes)):
        data = fetch_github_repo_data("https://github.com/octo/demo")
    assert data["branch"] == "master"


def test_raises_when_neither_branch_exists():
    with patch("github_fetcher.requests.Session", return_value=_session({})):
        with pytest.raises(ValueError):
            fetch_github_repo_data("https://github.com/octo/demo")


def test_rate_limit_surfaces_as_http_error():
    routes = {"git/trees/main": _resp(status=403, content=b"rate limited")}
    with patch("github_fetcher.requests.Session", return_value=_session(routes)):
        with pytest.raises(requests.HTTPError):
            fetch_github_repo_data("https://github.com/octo/demo")
