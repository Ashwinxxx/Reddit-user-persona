import os
import streamlit as st
st.write(" Secrets Loaded:")
st.write(st.secrets)

import praw
import nltk
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from nltk.sentiment import SentimentIntensityAnalyzer
from collections import Counter, defaultdict
from urllib.parse import urlparse
from openai import OpenAI
nltk.download('vader_lexicon')
try:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", st.secrets["openai_api_key"])
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", st.secrets["reddit_client_id"])
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", st.secrets["reddit_client_secret"])
except Exception as e:
    st.error("❌ API credentials missing. Set in .env or Streamlit secrets.")
    st.stop()
client = OpenAI(api_key=OPENAI_API_KEY)
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent="RedditPersonaApp:v1.0 (by /u/your_username)"
)

st.set_page_config(page_title="Reddit PersonaBox", layout="wide")
st.title("Reddit User Persona Generator")
st.markdown("Analyze any Reddit user's personality, tone, interests, and subreddit activity. GPT-powered + chart.")
def extract_username(url):
    return urlparse(url.rstrip("/")).path.split("/")[-1]

def fetch_user_activity(username, limit=100):
    user = reddit.redditor(username)
    comments = list(user.comments.new(limit=limit))
    posts = list(user.submissions.new(limit=limit))
    return comments, posts

def generate_gpt_persona(username, posts_comments, max_chars=6000):
    combined_text = ""
    for item in posts_comments:
        content = item.body if hasattr(item, "body") else item.title + " - " + item.selftext
        combined_text += f"- {content.strip()}\n\n"
        if len(combined_text) > max_chars:
            break

    prompt = f"""
You are a behavioral analyst. Based on the Reddit activity for u/{username} below, generate a structured user persona. Cover tone, interests, subreddit preferences, writing style, and inferred personality traits.

### Reddit Activity:
{combined_text}

### Persona:
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {str(e)}"

def infer_user_persona(comments, posts):
    sia = SentimentIntensityAnalyzer()
    subreddits = Counter()
    interests = Counter()
    tone_scores = []
    writing_styles = []
    citations = defaultdict(list)

    for comment in comments:
        text = comment.body.lower()
        subreddits[comment.subreddit.display_name] += 1
        sentiment = sia.polarity_scores(text)
        tone_scores.append(sentiment['compound'])

        if 'python' in text or 'programming' in text:
            interests['Programming'] += 1
            citations['Interests'].append((text, comment.permalink))
        if 'game' in text or 'gaming' in text:
            interests['Gaming'] += 1
            citations['Interests'].append((text, comment.permalink))
        if 'politics' in text:
            interests['Politics'] += 1
            citations['Interests'].append((text, comment.permalink))

        if len(text.split()) > 30:
            writing_styles.append('Long-form')
        else:
            writing_styles.append('Short-form')

    persona = {
        'Favorite Subreddits': [s for s, _ in subreddits.most_common(3)],
        'Interests': [i for i, _ in interests.most_common(3)],
        'Tone': 'Positive' if tone_scores and sum(tone_scores)/len(tone_scores) > 0.2 else 'Neutral or Negative',
        'Writing Style': Counter(writing_styles).most_common(1)[0][0] if writing_styles else 'Unknown',
    }

    return persona, citations, subreddits

def format_persona(username, persona, citations):
    output = f"User Persona for u/{username}\n\n"
    for trait, value in persona.items():
        output += f"{trait}:\n"
        if isinstance(value, list):
            for v in value:
                output += f"  - {v}\n"
        else:
            output += f"  {value}\n"
        if trait in citations:
            output += "  Cited from:\n"
            for text, link in citations[trait][:2]:
                snippet = text.strip().replace('\n', ' ')[:150]
                output += f"    - \"{snippet}...\" (https://reddit.com{link})\n"
        output += "\n"
    return output
profile_url = st.text_input("Reddit Profile URL", placeholder="e.g. https://www.reddit.com/user/spez/")
use_gpt = st.checkbox(" Use GPT-4 for persona generation", value=True)

if st.button("🚀 Generate Persona"):
    if not profile_url.strip():
        st.warning("Please enter a valid Reddit profile URL.")
    else:
        try:
            username = extract_username(profile_url)
            with st.spinner(f"Fetching Reddit data for u/{username}..."):
                comments, posts = fetch_user_activity(username)
                if not comments and not posts:
                    st.warning("No recent activity found.")
                else:
                    if use_gpt:
                        persona_output = generate_gpt_persona(username, comments + posts)
                    else:
                        persona, citations, subreddit_counts = infer_user_persona(comments, posts)
                        persona_output = format_persona(username, persona, citations)

                    st.success("Persona Generated!")
                    st.text_area(" Persona Output", persona_output, height=500)

                    st.download_button(
                        label="📥 Download Persona (.txt)",
                        data=persona_output,
                        file_name=f"user_persona_{username}.txt",
                        mime="text/plain"
                    )

                    if not use_gpt and subreddit_counts:
                        st.markdown("### 📊 Top Subreddits")
                        df_subs = pd.DataFrame(subreddit_counts.items(), columns=["Subreddit", "Posts/Comments"])
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
            st.error(f"❌ Error: {str(e)}")
