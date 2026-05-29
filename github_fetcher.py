import re
import requests
from urllib.parse import urlparse


# Files considered "important" regardless of extension
_IMPORTANT_FILENAMES = {"readme.md", "package.json", "requirements.txt"}

# Source-code extensions to include
_IMPORTANT_EXTENSIONS = (".py", ".js", ".ts")


def fetch_github_repo_data(repo_url: str) -> dict:
    """Fetch key source files from a public GitHub repository.

    Parses *repo_url* (e.g. ``'https://github.com/owner/repo'``), queries the
    GitHub API for the full recursive file tree, filters for important files
    (README.md, package.json, requirements.txt, and *.py / *.js / *.ts), then
    downloads each file's raw content.

    Returns a dict::

        {
            "owner": str,
            "repo": str,
            "branch": str,            # whichever of 'main'/'master' was found
            "files_found": [str, ...], # list of relative file paths
            "file_contents": {
                "<path>": "<raw text>",
                ...
            },
        }

    Raises:
        ValueError: URL cannot be parsed or neither branch was found.
        requests.HTTPError: GitHub API returned 4xx/5xx (including rate limits).
        requests.RequestException: Network-level error.
    """

    # ------------------------------------------------------------------
    # 1. Parse the URL and extract owner / repo name
    # ------------------------------------------------------------------
    try:
        parsed = urlparse(repo_url.strip())
        if parsed.netloc not in ("github.com", "www.github.com"):
            raise ValueError(f"Not a GitHub URL: {repo_url!r}")

        # Strip leading slash, drop any trailing '.git'
        path_parts = re.sub(r"\.git$", "", parsed.path.strip("/")).split("/")
        if len(path_parts) < 2 or not all(path_parts[:2]):
            raise ValueError(
                f"Could not extract owner/repo from path: {parsed.path!r}"
            )

        owner, repo = path_parts[0], path_parts[1]
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Invalid GitHub URL {repo_url!r}: {exc}") from exc

    # Shared session with Accept / API-version headers
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    # ------------------------------------------------------------------
    # 2. Fetch the recursive file tree (try 'main', fall back to 'master')
    # ------------------------------------------------------------------
    tree_items = None
    branch_used = None

    for branch in ("main", "master"):
        tree_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/git/trees/{branch}?recursive=1"
        )
        try:
            resp = session.get(tree_url, timeout=15)

            if resp.status_code == 404:
                continue  # try the other branch

            if resp.status_code == 403:
                raise requests.HTTPError(
                    "GitHub API rate limit exceeded or access forbidden. "
                    f"Response: {resp.text}",
                    response=resp,
                )

            resp.raise_for_status()
            tree_items = resp.json().get("tree", [])
            branch_used = branch
            break

        except requests.HTTPError:
            raise
        except requests.RequestException as exc:
            raise requests.RequestException(
                f"Network error fetching tree for '{owner}/{repo}': {exc}"
            ) from exc

    if tree_items is None:
        raise ValueError(
            f"Could not locate the repository tree for '{owner}/{repo}'. "
            "Neither 'main' nor 'master' branch was accessible."
        )

    # ------------------------------------------------------------------
    # 3. Filter the tree for important files
    # ------------------------------------------------------------------
    key_paths: list[str] = []
    for item in tree_items:
        if item.get("type") != "blob":
            continue  # skip subtrees / other objects

        file_path: str = item.get("path", "")
        filename = file_path.split("/")[-1].lower()

        if filename in _IMPORTANT_FILENAMES or filename.endswith(
            _IMPORTANT_EXTENSIONS
        ):
            key_paths.append(file_path)

    # ------------------------------------------------------------------
    # 4. Download raw content for each key file
    # ------------------------------------------------------------------
    raw_base = (
        f"https://raw.githubusercontent.com/{owner}/{repo}/{branch_used}"
    )
    file_contents: dict[str, str] = {}

    for file_path in key_paths:
        raw_url = f"{raw_base}/{file_path}"
        try:
            raw_resp = session.get(raw_url, timeout=15)

            if raw_resp.status_code == 403:
                raise requests.HTTPError(
                    "GitHub API rate limit exceeded or access forbidden.",
                    response=raw_resp,
                )

            if raw_resp.status_code == 404:
                # File disappeared between tree fetch and download – skip it
                continue

            raw_resp.raise_for_status()

            # Decode with replacement so binary blobs don't crash us
            file_contents[file_path] = raw_resp.content.decode(
                "utf-8", errors="replace"
            )

        except requests.HTTPError:
            raise  # propagate rate-limit / auth errors immediately
        except requests.RequestException as exc:
            # Record the error but keep going for remaining files
            file_contents[file_path] = f"[Error fetching file: {exc}]"

    # ------------------------------------------------------------------
    # 5. Return structured result
    # ------------------------------------------------------------------
    return {
        "owner": owner,
        "repo": repo,
        "branch": branch_used,
        "files_found": list(file_contents.keys()),
        "file_contents": file_contents,
    }
