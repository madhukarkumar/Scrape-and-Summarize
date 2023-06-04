# Summarizer and PDF Jarvis using OpenAI
The App has two pages and features:

**Home page** - A simple example of a Python app that takes a URL, scrapes the data and then sends to Open AI to summarize.
If the scraped data is too long, it will be split into multiple requests to Open AI.

**PDF Jarvis** - An app that reads the uploaded PDF, converts them to embeddings, loads them into a SingleStore database. When the user asks a question, the app does a semantic match against the emebeddings in SingleStore and then sends that as a context to OpenAI to print back the answer.


To run the app locally,
Create a venv with Python 3.9.16
pip install -r requirements.text

streamlit run main.app
