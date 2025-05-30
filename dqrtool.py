# Domain Quality Rating Tool with Streamlit Interface

import streamlit as st
import requests
from bs4 import BeautifulSoup
import tldextract
from langdetect import detect
import re

# --------------------- Helper Functions ---------------------
def extract_domain(url):
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def fetch_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        page = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(page.text, "html.parser")
        return soup
    except Exception as e:
        st.error(f"Error fetching page: {e}")
        return None

def detect_language(soup):
    try:
        text = soup.get_text()
        return detect(text)
    except:
        return "unknown"

def detect_ads(soup):
    ads = soup.find_all(["iframe", "script", "ins", "img"], src=True)
    return len(ads)

def extract_main_content(soup):
    texts = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    return "\n".join(texts)

def is_ymyl_topic(text):
    ymyl_keywords = ["health", "finance", "investment", "disease", "legal", "bank", "loan", "prescription"]
    return any(word.lower() in text.lower() for word in ymyl_keywords)

def estimate_content_quality(text):
    if len(text) < 300:
        return "Low"
    elif len(text) < 1000:
        return "Medium"
    else:
        return "High"

def rate_domain(url):
    soup = fetch_page(url)
    if not soup:
        return "Lowest (Unreachable or Unsafe)", {}, ""

    lang = detect_language(soup)
    ads_count = detect_ads(soup)
    content = extract_main_content(soup)
    content_quality = estimate_content_quality(content)
    is_ymyl = is_ymyl_topic(content)

    # Domain Quality Logic
    if ads_count > 10 and content_quality == "Low":
        rating = "Lowest"
    elif is_ymyl and content_quality != "High":
        rating = "Low"
    elif content_quality == "High" and ads_count < 5:
        rating = "High"
    else:
        rating = "Medium"

    metadata = {
        "Language": lang,
        "Ad Elements Found": ads_count,
        "Content Quality": content_quality,
        "YMYL Topic Detected": is_ymyl
    }

    return rating, metadata, content

# --------------------- Streamlit UI ---------------------
st.title("\U0001F50E Domain Quality Rating Tool")
st.markdown("This tool evaluates the quality of a domain using the uploaded guideline standards.")

url_input = st.text_input("Enter Website URL")
if st.button("Rate Domain") and url_input:
    with st.spinner("Analyzing domain..."):
        rating, meta, content = rate_domain(url_input)

    st.success(f"Domain Quality Rating: **{rating}**")
    st.subheader("Metadata")
    st.json(meta)

    if content:
        with st.expander("View Extracted Main Content"):
            st.text_area("Main Content", content, height=300)
