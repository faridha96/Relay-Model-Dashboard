# Health-Risk Failure Dashboard

This repository contains a Streamlit dashboard for analyzing health-risk failure data from CSV or Excel files.

## Files

- `dashboard_V2.py` - Streamlit dashboard implementation.
- `streamlit_app.py` - Streamlit entrypoint used for deployment.
- `requirements.txt` - Python dependencies required to run the app.
- `.gitignore` - Files and folders to ignore in Git.

## Run locally

1. Install Python 3.11 or newer.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the app locally:
   ```bash
   streamlit run streamlit_app.py
   ```

## Deploy on GitHub

GitHub cannot directly host Python apps as a web service, but you can deploy this Streamlit app using Streamlit Community Cloud by connecting to a GitHub repository.

### Steps

1. Create a new repository on GitHub and push this project.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app" and select your repository.
4. Set the main file to `dashboard_V2.py` and choose the branch where you pushed the code.
5. Deploy.

## Optional GitHub Actions

If you want continuous validation on each push, you can add a GitHub Actions workflow to install dependencies and verify that the app file compiles.
