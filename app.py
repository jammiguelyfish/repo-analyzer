import os

import streamlit as st

from github_fetcher import fetch_github_repo_data
from summarizer import generate_repo_summary

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="AI GitHub Repo Summarizer",
    page_icon="🔍",
    layout="centered",
)

# ------------------------------------------------------------------
# Sidebar – API key
# ------------------------------------------------------------------
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Paste your GEMINI_API_KEY here",
        help="Your key is stored only for this session and never transmitted anywhere except the Gemini API.",
    )
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        st.success("API key set for this session.", icon="✅")
    else:
        st.info("Enter your Gemini API key to enable summarization.", icon="ℹ️")

    st.divider()
    st.caption(
        "Uses [Google Gemini](https://ai.google.dev/) via `gemini-2.5-flash` "
        "and the public [GitHub API](https://docs.github.com/en/rest)."
    )

# ------------------------------------------------------------------
# Main area – title
# ------------------------------------------------------------------
st.title("🔍 AI GitHub Repository Summarizer")
st.subheader("Paste any public GitHub repo link and get an instant Developer Onboarding Guide.")
st.divider()

# ------------------------------------------------------------------
# Input
# ------------------------------------------------------------------
repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/owner/repo",
    label_visibility="collapsed",
)

summarize_btn = st.button("Summarize Repository", type="primary", use_container_width=True)

# ------------------------------------------------------------------
# Processing
# ------------------------------------------------------------------
if summarize_btn:
    if not os.environ.get("GEMINI_API_KEY"):
        st.error("Please enter your Gemini API key in the sidebar before proceeding.")
    elif not repo_url.strip():
        st.warning("Please enter a GitHub repository URL.")
    else:
        with st.spinner("Analyzing repository structure and code..."):
            try:
                # Step 1 – fetch files from GitHub
                repo_data = fetch_github_repo_data(repo_url)

                if not repo_data["file_contents"]:
                    st.warning(
                        "No recognizable source files were found in that repository. "
                        "Make sure the repo is public and contains .py / .js / .ts files "
                        "or a README / package.json / requirements.txt."
                    )
                else:
                    # Step 2 – format files into a single text block for the LLM
                    repo_text_parts = [
                        f"Repository: {repo_data['owner']}/{repo_data['repo']} "
                        f"(branch: {repo_data['branch']})\n"
                    ]
                    for path, content in repo_data["file_contents"].items():
                        repo_text_parts.append(f"### {path}\n```\n{content}\n```")

                    repo_text = "\n\n".join(repo_text_parts)

                    # Step 3 – generate summary with Gemini
                    summary = generate_repo_summary(repo_text)

                    # Step 4 – display results
                    st.success(
                        f"Analyzed **{len(repo_data['files_found'])}** file(s) from "
                        f"`{repo_data['owner']}/{repo_data['repo']}`.",
                        icon="✅",
                    )
                    st.divider()
                    st.markdown(summary)

                    with st.expander("Files analyzed"):
                        for f in repo_data["files_found"]:
                            st.code(f, language=None)

            except ValueError as exc:
                st.error(f"Invalid repository URL: {exc}")
            except Exception as exc:
                err_msg = str(exc)
                if "rate limit" in err_msg.lower() or "403" in err_msg:
                    st.error(
                        "GitHub API rate limit reached or access was denied. "
                        "Wait a few minutes and try again, or authenticate with a GitHub token."
                    )
                elif "api_key" in err_msg.lower() or "401" in err_msg or "403" in err_msg:
                    st.error("Gemini API key is invalid or missing. Check the key in the sidebar.")
                else:
                    st.error(f"An unexpected error occurred: {exc}")
