import streamlit as st
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from supabase import create_client, Client
import threading
import time
import json

# LangChain & Chroma imports for RAG
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- Configurations ---
GEMINI_API_KEY = "AIzaSyCzSUTBrRJzeelCmRMuNCfb2C-dPPtgBAM"  # Same key works for embeddings
SHEET_ID = "https://docs.google.com/spreadsheets/d/1ATllEOsVzBIHm4egctEVbf7CDzmHtFfyEMmT7U6NNnw/edit?gid=0#gid=0"
SUPABASE_URL = "https://pwjkofyouvwznftprgzc.supabase.co"
SUPABASE_KEY = "sb_publishable_Yp67u_MsHh80anguNcK0Fw_v4nZvAUy"
SHEET_RANGE = "Sheet1!A1:Z1000"  # Adjust as needed
REFRESH_INTERVAL = 30  # Reduced polling since we have RAG now
PERSIST_DIRECTORY = "/tmp/chroma_db"  # Folder for Chroma persistence

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Embeddings & Model
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to read Google Sheet
def read_google_sheet():
    scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    if 'creds' not in st.session_state:
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', scopes)
        creds = flow.run_local_server(port=0)
        st.session_state['creds'] = creds
    else:
        creds = st.session_state['creds']
    service = build('sheets', 'v4', credentials=creds)
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
    return result.get('values', [])

# Function to index sheet data into Chroma (RAG setup)
def index_sheet_data():
    with st.spinner("Indexing Google Sheet data for RAG (this may take a minute first time)..."):
        raw_data = read_google_sheet()
        if not raw_data:
            st.warning("No data found in sheet.")
            return

        # Convert rows to documents (chunk by row or small groups)
        documents = []
        headers = raw_data[0]  # Assume first row is headers
        for i, row in enumerate(raw_data[1:]):  # Skip headers
            # Pad row if shorter than headers
            row += [''] * (len(headers) - len(row))
            content = "\n".join([f"{headers[j]}: {row[j]}" for j in range(len(headers))])
            documents.append(Document(page_content=content, metadata={"row": i+2}))

        # Split if rows are very long (optional)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)

        # Create or update vectorstore
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=PERSIST_DIRECTORY
        )
        vectorstore.persist()
        st.session_state['vectorstore'] = vectorstore
        st.session_state['retriever'] = vectorstore.as_retriever(search_kwargs={"k": 5})  # Top 5 chunks
        st.success(f"Indexed {len(splits)} chunks from {len(raw_data)-1} rows.")

# Auto-refresh raw sheet data (lightweight, for display or fallback)
def auto_refresh_sheet():
    while True:
        try:
            st.session_state['sheet_data'] = read_google_sheet()
        except Exception as e:
            print(f"Sheet refresh error: {e}")
        time.sleep(REFRESH_INTERVAL)

if 'refresh_thread' not in st.session_state:
    st.session_state['refresh_thread'] = threading.Thread(target=auto_refresh_sheet, daemon=True)
    st.session_state['refresh_thread'].start()

# Load chat history
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
    response = supabase.table('chat_history').select('messages').eq('user_id', 'demo_user').execute()
    if response.data:
        st.session_state['messages'] = json.loads(response.data[0]['messages'])

# Setup RAG chain (only if indexed)
def setup_rag_chain():
    if 'retriever' not in st.session_state:
        return None
    
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    Answer:"""
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": st.session_state['retriever'], "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    return chain

# --- Streamlit UI ---
st.title("AI Chatbot with RAG (Powered by Gemini)")

# Manual refresh button for RAG indexing
if st.button("Refresh & Re-index Data from Google Sheet (for latest RAG)"):
    index_sheet_data()

# Auto-load index on first run
if 'vectorstore' not in st.session_state:
    if Chroma.persist_directory_exists(PERSIST_DIRECTORY):
        st.info("Loading existing index...")
        vectorstore = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embeddings)
        st.session_state['vectorstore'] = vectorstore
        st.session_state['retriever'] = vectorstore.as_retriever(search_kwargs={"k": 5})
    else:
        st.info("No index found. Click the button above to index your sheet data.")
        index_sheet_data()

# Display chat
for msg in st.session_state['messages']:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# User input
if prompt := st.chat_input("Ask about your sheet data..."):
    st.session_state['messages'].append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)

    rag_chain = setup_rag_chain()
    if rag_chain:
        with st.chat_message('assistant'):
            with st.spinner("Thinking..."):
                response = rag_chain.invoke(prompt)
            st.markdown(response)
        st.session_state['messages'].append({'role': 'assistant', 'content': response})
    else:
        st.warning("Please index the data first.")

    # Save history
    supabase.table('chat_history').upsert({'user_id': 'demo_user', 'messages': json.dumps(st.session_state['messages'])}).execute()
