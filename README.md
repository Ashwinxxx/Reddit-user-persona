Reddit User Persona Generator
This repository contains a Streamlit application designed to generate detailed user personas from public Reddit profiles. It leverages the Reddit API to scrape user activity and utilizes OpenAI's GPT models for advanced persona generation, alongside rule-based analysis and data visualization.

Assignment Requirements Met:
This project fulfills all the requirements outlined in the "Generative AI Internship Opportunity" assignment:

Takes as input a Reddit user's profile URL: The Streamlit application provides a dedicated input field for Reddit profile URLs.

Scrapes comments and posts created by the Redditor: The fetch_user_activity function uses the PRAW library to retrieve a user's recent comments and submissions.

Builds a User Persona based on details found on their Reddit:

GPT-Powered Persona: The generate_gpt_persona function utilizes the OpenAI API (GPT-4o) to create a comprehensive persona, covering tone, interests, subreddit preferences, writing style, and inferred personality traits.

Programmatic Persona: The infer_user_persona function performs rule-based analysis using NLTK (VADER sentiment) and Python's Counter to identify interests, tone, writing style, and top subreddits.

Outputs the user persona for the input profile in a text file: The generated persona (from either GPT or programmatic analysis) can be downloaded as a .txt file directly from the Streamlit interface.

For each characteristic in the user persona, the script also "cites" the posts or comments it used to extract the specific user persona information: The programmatic persona generation (infer_user_persona and format_persona) includes direct citations with links to the original Reddit content.

Technologies Used: The project is developed entirely in Python, utilizing key libraries such as Streamlit (for the web interface), PRAW (for Reddit API interaction), nltk (for NLP), openai (for LLM integration), pandas (for data handling), plotly (for visualizations), and wordcloud (for text visualization).

Setup and Execution Instructions:
Follow these steps to set up and run the application locally:

Clone the Repository:

git clone https://github.com/Ashwinxxx/Reddit-user-persona.git
cd Reddit-user-persona

Create and Activate a Python Virtual Environment (Recommended):

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

Install Dependencies:
Install all required Python packages using the requirements.txt file:

pip install -r req.txt

Obtain API Credentials:
This application requires API keys for both Reddit and OpenAI.

Reddit API Keys:

Log in to your Reddit account and go to https://www.reddit.com/prefs/apps.

Click "Create App" or "Create Another App."

Select the "script" type.

For "Redirect URI," enter http://localhost:8000 (this is a common placeholder for local script apps).

After creation, note down your Client ID (labeled "personal use script") and Client Secret (labeled "secret").

OpenAI API Key:

Go to https://platform.openai.com/account/api-keys.

Generate a new secret key.

Configure API Credentials (Local Development):
Create a file named .env in the root directory of this project (the same directory as app.py). Add your API keys to this file, replacing the placeholders with your actual keys:

# .env file
OPENAI_API_KEY="sk-YOUR_OPENAI_API_KEY_HERE"
REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID_HERE"
REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET_HERE"

Security Note: The .env file is included in .gitignore to prevent your sensitive API keys from being committed to public repositories.

Set PRAW User-Agent:
Open the app.py file. Locate the praw.Reddit initialization (around line 52) and replace YourActualRedditUsername with the Reddit username you used to register your API application:

user_agent="RedditPersonaApp:v1.0 (by /u/YourActualRedditUsername)"

Run the Streamlit Application:
From your terminal, in the project's root directory, run:

streamlit run app.py

This command will launch the Streamlit application in your default web browser.

Generate Persona for a Reddit Profile:
In the running Streamlit app, paste a Reddit user profile URL (e.g., https://www.reddit.com/user/kojied/ or https://www.reddit.com/user/Hungry-Move-6603/) into the input field and click the "🚀 Generate Persona" button.

Known Issue / Troubleshooting:
Persistent FileNotFoundError: No secrets files found
Problem Description:
During local development, the application occasionally throws a FileNotFoundError with the message "No secrets files found. Valid paths for a secrets.toml file are: C:\Users\shree.streamlit\secrets.toml, C:\Users\shree\library\reddit.streamlit\secrets.toml". This error is then caught by the application's general exception handler and displayed as "❌ API credentials missing...".

Troubleshooting Steps Taken:
Extensive efforts have been made to resolve this specific error, including:

Ensuring from dotenv import load_dotenv and load_dotenv() are correctly placed at the very beginning of app.py to load environment variables from .env.

Verifying the .env file's correct placement in the root directory and its accurate content (key names and values).

Crucially, all instances of st.write(st.secrets) have been removed from the code. This line is known to trigger the FileNotFoundError when Streamlit's local secrets.toml file is not present.

Confirming that API key retrieval uses os.getenv("KEY", st.secrets.get("key")), where st.secrets.get() is designed to gracefully return None if the secret file is absent, preventing a hard error.

Performing clean installations of all dependencies in isolated Python virtual environments.

Ensuring complete restarts of the Streamlit application after any code or .env changes.

Hypothesis on Persistence:
Despite these measures, the error can still manifest intermittently. This suggests a potential deeper interaction within Streamlit's internal local secrets loading mechanism that might, under certain conditions, still attempt to access secrets.toml even when os.getenv is the primary intended method for local environment variables.

Impact on Functionality:
When this FileNotFoundError occurs, the application stops prematurely as it cannot initialize the API clients. However, when the error does not occur (which is often the case after a fresh restart or in certain execution contexts), the application functions entirely as intended
