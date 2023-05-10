import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain import agents


def scrape_website(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    else:
        raise Exception(f"Unable to access website with status code: {response.status_code}")



def get_summary(api_key, text):

    # Truncate the text to 2000 tokens
    #truncated_text = text[:2000]
    #truncate text to 2000 tokens
    truncated_text = text[:2000]

    #add prompt
    prompt_text = "Summarize this text:\n\n" + truncated_text

    # Send the text to the OpenAI API to summarize
    openai.api_key = api_key
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt_text,
        temperature=0.3,
        max_tokens=200,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=["\n", "Summary:"]
    )

    # Return the summary
    summary = response.choices[0].text
    return summary
   


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
            soup = scrape_website(url_input)
            extracted_text = soup.get_text()
            st.write(extracted_text)
        except Exception as e:
            st.error(f"Error: {e}")

    if summarize_button:
        if not extracted_text:
            try:
                soup = scrape_website(url_input)
                extracted_text = soup.get_text()
            except Exception as e:
                st.error(f"Error: {e}")

        if api_key_input:
            try:
                summary = get_summary(api_key_input, extracted_text)
                st.write(summary)
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
