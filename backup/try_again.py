import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from langchain import OpenAI
from langchain import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain import agents
from langchain.docstore.document import Document
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')

def scrape_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()  # Return text directly
    else:
        raise Exception(f"Unable to access website with status code: {response.status_code}")

def split_text(text, max_tokens):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []

    for sentence in sentences:
        current_chunk.append(sentence)
        if len(" ".join(current_chunk)) >= max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks




def get_summary(api_key, text):
    llm = OpenAI(openai_api_key=api_key)
    chain = load_summarize_chain(llm, chain_type="map_reduce")
    
    max_tokens = 4097 - 256  # 256 tokens reserved for completion
    text_chunks = split_text(text, max_tokens)

    summaries = []
    for chunk in text_chunks:
        doc = Document(page_content=chunk)
        summary = chain.run([doc])
        summaries.append(summary)

    return summaries
   


def main():
    st.title("Website Scraper and Summarizer")

    with st.sidebar:
        url_input = st.text_input("Enter the website URL:", "https://news.ycombinator.com/item?id=35826929")
        api_key_input = st.text_input("Enter your OpenAI API Key:", "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")
        scrape_button = st.button("Scrape", key="scrape")
        summarize_button = st.button("Summarize with GPT", key="summarize")

    extracted_text = None

    if scrape_button:
        try:
            extracted_text = scrape_website(url_input)
            st.write(extracted_text)
        except Exception as e:
            st.error(f"Error: {e}")

    if summarize_button:
        if not extracted_text:
            try:
                extracted_text = scrape_website(url_input)
            except Exception as e:
                st.error(f"Error: {e}")

        if api_key_input:
            try:
                if extracted_text:
                    summaries = get_summary(api_key_input, extracted_text)
                    combined_summary = " ".join(summaries)
                    st.write(combined_summary)
                else:
                    st.error("Could not extract text from the website.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please enter your OpenAI API Key.")

    st.markdown("""
        <style>
            .stButton>button {
                background-color: blue;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
