import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub
# for creating embeddings and inserting them into a table in SingleStore
import sqlalchemy as db
import os
from sqlalchemy import text as sql_text

#Initialize OpenAIEmbeddings
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
embedder = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)#TODO: replace with your API key

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

#this method accepts a list of text chunks and returns a vectorstore
def get_vectorstore(text_chunks):
    embeddings = OpenAIEmbeddings()
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

#function that takes a list of text chunks, creates embeddings and inserts them into a table in SingleStore
def create_embeddings_and_insert(text_chunks):
    password = os.environ.get("SINGLESTORE_PASSWORD")
    connection = db.create_engine(
        f"mysql+pymysql://admin:{password}@svc-bdaf1a6b-098e-47a4-97c7-01d3b678e08d-dml.aws-virginia-6.svc.singlestore.com:3306/winter_wikipedia")
    with connection.begin() as conn:
        # Iterate over the text chunks
        for i, text in enumerate(text_chunks):
            # Convert the text to embeddings
            embedding = embedder.embed_documents([text])[0]

            # Insert the text and its embedding into the database
            stmt = sql_text("""
                INSERT INTO multiple_pdf_example (
                    text,
                    embeddings
                )
                VALUES (
                    :text,
                    JSON_ARRAY_PACK_F32(:embeddings)
                )
            """)

            conn.execute(stmt, {"text": str(text), "embeddings": str(embedding)})


def get_conversation_chain(vectorstore):
    llm = ChatOpenAI()
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    memory = ConversationBufferMemory(
        memory_key='chat_history', return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain


def handle_userinput(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    load_dotenv()
    #st.set_page_config(page_title="Chat with multiple PDFs",
    #                   page_icon=":books:")
    #st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with multiple PDFs :books:")
    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        handle_userinput(user_question)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"):
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)

                # get the text chunks
                text_chunks = get_text_chunks(raw_text)

                # Test the function
                text_chunks = ["This is a test.", "This is another test."]
                create_embeddings_and_insert(text_chunks)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain
                st.session_state.conversation = get_conversation_chain(
                    vectorstore)


#if __name__ == '__main__':
#    main()
