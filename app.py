import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import praw
import nltk
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter, defaultdict
from urllib.parse import urlparse
from openai import OpenAI

nltk.download('vader_lexicon', quiet=True)

try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets.get("openai_api_key"))
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", st.secrets.get("reddit_client_id"))
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", st.secrets.get("reddit_client_secret"))

    if not OPENAI_API_KEY or not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("One or more API credentials (OPENAI_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET) are missing.")

except Exception as e:
    st.error(
        f"❌ API credentials missing. Please set them in a `.env` file (for local development) "
        f"or in Streamlit secrets (for Streamlit Cloud deployment). Error details: {e}"
    )
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="RedditPersonaApp:v1.0 (by /u/YourActualRedditUsername)" # REMEMBER TO CHANGE THIS!
)

st.set_page_config(page_title="Reddit PersonaBox", layout="wide")
st.title("Reddit User Persona Generator")
st.markdown("Analyze any Reddit user's personality, tone, interests, and subreddit activity. GPT-powered + chart.")

def extract_username(url: str) -> str:
    parsed_url = urlparse(url.rstrip("/"))
    return parsed_url.path.split("/")[-1]

def fetch_user_activity(username: str, limit: int = 100):
    try:
        user = reddit.redditor("Responsible-badger_17") # CORRECTED LINE
        comments = list(user.comments.new(limit=limit))
        posts = list(user.submissions.new(limit=limit))
        return comments, posts
    except Exception as e:
        st.error(f"Failed to fetch user activity for u/{username}. Error: {e}")
        st.info("Please ensure the username is correct and the profile is public.")
        return [], []

def generate_gpt_persona(username: str, posts_comments: list, max_chars: int = 6000) -> str:
    combined_text = ""
    for item in posts_comments:
        content = ""
        if hasattr(item, "body"):
            content = item.body
        elif hasattr(item, "title") and hasattr(item, "selftext"):
            content = item.title + " - " + item.selftext
        elif hasattr(item, "title"):
            content = item.title

        if content:
            combined_text += f"- {content.strip()}\n\n"
            if len(combined_text) > max_chars:
                combined_text = combined_text[:max_chars]
                break

    if not combined_text:
        return "No sufficient text activity found to generate a GPT persona."

    prompt = f"""
You are a highly skilled behavioral analyst specializing in online user profiles.
Based on the Reddit activity for u/{username} provided below, generate a comprehensive and structured user persona.
Focus on the following aspects:
1.  **Overall Tone and Sentiment:** Is the user generally positive, negative, neutral, sarcastic, aggressive, etc.? Provide examples.
2.  **Primary Interests and Topics:** What subjects does the user frequently discuss or show interest in?
3.  **Subreddit Preferences:** Which subreddits does the user actively participate in?
4.  **Writing Style and Language Use:** Is their language formal, informal, concise, verbose, technical, use of slang, emojis, etc.?
5.  **Inferred Personality Traits:** Based on their interactions, what can you infer about their personality (e.g., helpful, argumentative, curious, cynical, humorous)?
6.  **Potential Demographics (if inferable, be cautious):** Briefly mention any *very obvious* demographic hints (e.g., mentions of being a student, a specific profession, general region), but avoid speculation.

### Reddit Activity:
{combined_text}

### Persona:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: Could not generate persona. Details: {str(e)}"

def infer_user_persona(comments: list, posts: list):
    sia = SentimentIntensityAnalyzer()
    subreddits = Counter()
    interests = Counter()
    tone_scores = []
    writing_styles = []
    citations = defaultdict(list)

    all_activity = comments + posts

    if not all_activity:
        return {
            'Favorite Subreddits': [],
            'Interests': [],
            'Tone': 'No activity',
            'Writing Style': 'No activity',
        }, {}, Counter()

    for item in all_activity:
        text = ""
        permalink = ""
        subreddit_name = ""

        if hasattr(item, "body"):
            text = item.body
            permalink = item.permalink
            subreddit_name = item.subreddit.display_name
        elif hasattr(item, "title"):
            text = item.title + " " + item.selftext if hasattr(item, "selftext") else item.title
            permalink = item.permalink
            subreddit_name = item.subreddit.display_name

        if not text:
            continue

        text_lower = text.lower()
        subreddits[subreddit_name] += 1
        sentiment = sia.polarity_scores(text_lower)
        tone_scores.append(sentiment['compound'])

        if 'python' in text_lower or 'programming' in text_lower or 'code' in text_lower or 'developer' in text_lower:
            interests['Programming/Tech'] += 1
            citations['Interests'].append((text, permalink))
        if 'game' in text_lower or 'gaming' in text_lower or 'nintendo' in text_lower or 'playstation' in text_lower or 'xbox' in text_lower or 'pc master race' in text_lower:
            interests['Gaming'] += 1
            citations['Interests'].append((text, permalink))
        if 'politics' in text_lower or 'government' in text_lower or 'election' in text_lower or 'news' in text_lower:
            interests['Politics/Current Events'] += 1
            citations['Interests'].append((text, permalink))
        if 'stock' in text_lower or 'investing' in text_lower or 'finance' in text_lower or 'money' in text_lower:
            interests['Finance'] += 1
            citations['Interests'].append((text, permalink))
        if 'movie' in text_lower or 'film' in text_lower or 'series' in text_lower or 'show' in text_lower or 'tv' in text_lower:
            interests['Movies/TV'] += 1
            citations['Interests'].append((text, permalink))
        if 'art' in text_lower or 'design' in text_lower or 'creative' in text_lower or 'music' in text_lower:
            interests['Arts/Culture'] += 1
            citations['Interests'].append((text, permalink))

        word_count = len(text.split())
        if word_count > 50:
            writing_styles.append('Verbose/Detailed')
        elif word_count > 10:
            writing_styles.append('Moderate')
        else:
            writing_styles.append('Concise/Short-form')

    avg_tone = sum(tone_scores) / len(tone_scores) if tone_scores else 0
    inferred_tone = 'Positive' if avg_tone > 0.2 else ('Negative' if avg_tone < -0.2 else 'Neutral')

    persona = {
        'Favorite Subreddits': [s for s, _ in subreddits.most_common(5)],
        'Interests': [i for i, _ in interests.most_common(5)],
        'Tone': inferred_tone,
        'Writing Style': Counter(writing_styles).most_common(1)[0][0] if writing_styles else 'Unknown',
    }

    return persona, citations, subreddits

def format_persona(username: str, persona: dict, citations: defaultdict) -> str:
    output = f"## User Persona for u/{username}\n\n"

    for trait, value in persona.items():
        output += f"### {trait}:\n"
        if isinstance(value, list):
            if value:
                for v in value:
                    output += f"- {v}\n"
            else:
                output += "  *N/A - No relevant activity found.*\n"
        else:
            output += f"{value}\n"

        if trait in citations and citations[trait]:
            output += "#### Cited from (examples):\n"
            for i, (text_snippet, permalink) in enumerate(citations[trait][:3]):
                display_snippet = text_snippet.strip().replace('\n', ' ')
                if len(display_snippet) > 100:
                    display_snippet = display_snippet[:100] + "..."
                output += f"- \"{display_snippet}\" ([Link](https://reddit.com{permalink}))\n"
        output += "\n"
    return output

profile_url = st.text_input(
    "Enter Reddit Profile URL",
    placeholder="e.g. https://www.reddit.com/user/spez/ or https://www.reddit.com/user/kojied/"
)

use_gpt = st.checkbox("Use GPT for persona generation (recommended, requires OpenAI API key)", value=True)

if st.button("🚀 Generate Persona"):
    if not profile_url.strip():
        st.warning("Please enter a valid Reddit profile URL.")
    else:
        try:
            username = extract_username(profile_url)
            if not username:
                st.error("Could not extract username from the provided URL. Please check the format.")
                st.stop()

            with st.spinner(f"Fetching Reddit data for u/{username}... This might take a moment."):
                comments, posts = fetch_user_activity(username)

            if not comments and not posts:
                st.warning(f"No recent activity found for u/{username}. This user might have no public posts/comments, or the username is incorrect.")
            else:
                persona_output_text = ""
                subreddit_counts_for_chart = Counter()

                if use_gpt:
                    with st.spinner("Generating GPT-powered persona..."):
                        persona_output_text = generate_gpt_persona(username, comments + posts)
                else:
                    with st.spinner("Inferring persona with NLTK and rule-based analysis..."):
                        persona_data, citations_data, subreddit_counts_for_chart = infer_user_persona(comments, posts)
                        persona_output_text = format_persona(username, persona_data, citations_data)

                st.success("Persona Generated!")
                st.markdown("### Generated Persona")
                st.markdown(persona_output_text)

                st.download_button(
                    label="📥 Download Persona (.txt)",
                    data=persona_output_text,
                    file_name=f"user_persona_{username}.txt",
                    mime="text/plain"
                )

                all_combined_text = ""
                for item in comments + posts:
                    content = item.body if hasattr(item, "body") else (item.title + " " + item.selftext if hasattr(item, "selftext") else item.title)
                    all_combined_text += content + " "

                if all_combined_text:
                    st.markdown("### 📝 Most Used Words (from comments/posts)")
                    wordcloud = WordCloud(width=800, height=400, background_color='white',
                                          collocations=False,
                                          min_font_size=10).generate(all_combined_text)
                    st.image(wordcloud.to_array(), caption='Word Cloud', use_column_width=True)

                if subreddit_counts_for_chart:
                    st.markdown("### 📊 Top Active Subreddits")
                    df_subs = pd.DataFrame(subreddit_counts_for_chart.items(), columns=["Subreddit", "Posts/Comments"])
                    df_subs = df_subs.sort_values(by="Posts/Comments", ascending=False).head(10)

                    fig = px.bar(
                        df_subs,
                        x="Subreddit",
                        y="Posts/Comments",
                        title="Top 10 Most Active Subreddits",
                        text_auto=True,
                        color="Posts/Comments",
                        color_continuous_scale="blues"
                    )
                    fig.update_layout(xaxis_title="Subreddit", yaxis_title="Count", height=400)
                    st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {str(e)}")
            st.info("Please double-check the Reddit profile URL, ensure your API keys are correct, and try again.")
            st.warning("If the issue persists, ensure your Python environment is clean and all dependencies are installed.")
