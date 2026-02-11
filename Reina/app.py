import streamlit as st
import pandas as pd
import requests
from io import StringIO
from anthropic import Anthropic
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

# Initialize embedding model
@st.cache_resource
def get_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')  # Dimension: 384

# Function to split text into chunks
def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# Function to fetch and process Google Sheet
def fetch_google_sheet(url: str) -> pd.DataFrame:
    if 'docs.google.com/spreadsheets/d/' in url:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        response = requests.get(csv_url)
        if response.status_code == 200:
            df = pd.read_csv(StringIO(response.text))
            df = df.drop_duplicates()  # Handle duplicates as per notes
            return df
        else:
            st.error(f"Error fetching sheet: {response.status_code}")
    else:
        st.error("Invalid Google Sheet URL")
    return None

# Function to process dataframe into chunks and embeddings
def process_df(df: pd.DataFrame, source_name: str, model) -> Tuple[List[str], np.ndarray, List[str]]:
    chunks = []
    sources = []
    for _, row in df.iterrows():
        chunk = ' '.join(f"{col}: {str(row[col])}" for col in df.columns)
        chunks.append(chunk)
        sources.append(source_name)  # Tag with source
    embeddings = model.encode(chunks)
    return chunks, embeddings, sources

# Function to process uploaded file
def process_file(file, model) -> Tuple[List[str], np.ndarray, List[str]]:
    chunks = []
    sources = []
    if file.type == "text/csv":
        df = pd.read_csv(file)
        df = df.drop_duplicates()
        file_chunks, file_embeddings, file_sources = process_df(df, file.name, model)
        chunks.extend(file_chunks)
        sources.extend(file_sources)
        return chunks, file_embeddings, sources
    else:  # txt, md
        text = file.read().decode('utf-8')
        file_chunks = split_text(text)
        for chunk in file_chunks:
            chunks.append(chunk)
            sources.append(file.name)
        embeddings = model.encode(chunks)
        return chunks, embeddings, sources

# Main app
st.title("RAG Chatbot with Google Sheets Integration")

# Customization parameters (as per notes)
chunk_size = 500
overlap = 100
top_k = 3
# Embedding dimension not directly used since model defines it

# Session state initialization
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'chunks' not in st.session_state:
    st.session_state.chunks = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'messages' not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Configuration")
    st.session_state.api_key = st.text_input(
        "Claude API Key",
        type="password",
        value=st.session_state.api_key,
        help="Enter your Anthropic Claude API key"
    )
    
    st.header("Data Sources")
    
    # Option A: Upload Files
    uploaded_files = st.file_uploader("Upload Files (.txt, .md, .csv)", accept_multiple_files=True)
    if st.button("Process Files") and uploaded_files:
        model = get_embedding_model()
        all_chunks = []
        all_embeddings = []
        all_sources = []
        for file in uploaded_files:
            if file.name.endswith(('.txt', '.md', '.csv')):
                file_chunks, file_embeddings, file_sources = process_file(file, model)
                all_chunks.extend(file_chunks)
                all_embeddings.extend(file_embeddings)
                all_sources.extend(file_sources)
            else:
                st.warning(f"Unsupported file type: {file.name}")
        if all_chunks:
            st.session_state.chunks.extend(all_chunks)
            if st.session_state.embeddings is None:
                st.session_state.embeddings = np.array(all_embeddings)
            else:
                st.session_state.embeddings = np.vstack((st.session_state.embeddings, all_embeddings))
            st.session_state.sources.extend(all_sources)
            st.success(f"Processed {len(uploaded_files)} files!")

    # Option B: Google Sheet
    sheet_url = st.text_input("Google Sheet URL")
    if st.button("Connect Sheet"):
        if sheet_url:
            df = fetch_google_sheet(sheet_url)
            if df is not None:
                model = get_embedding_model()
                sheet_chunks, sheet_embeddings, sheet_sources = process_df(df, "Google Sheet", model)
                st.session_state.chunks.extend(sheet_chunks)
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = sheet_embeddings
                else:
                    st.session_state.embeddings = np.vstack((st.session_state.embeddings, sheet_embeddings))
                st.session_state.sources.extend(sheet_sources)
                st.success("Google Sheet connected and processed!")
        else:
            st.warning("Please enter a Google Sheet URL")

# Chat interface
if st.session_state.chunks:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about your data"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not st.session_state.api_key:
            st.error("Please enter your Claude API key in the sidebar.")
        else:
            model = get_embedding_model()
            query_emb = model.encode(prompt)

            # Compute cosine similarities
            similarities = np.dot(st.session_state.embeddings, query_emb) / (
                np.linalg.norm(st.session_state.embeddings, axis=1) * np.linalg.norm(query_emb)
            )

            # Get top_k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            relevant_chunks = [st.session_state.chunks[i] for i in top_indices]
            relevant_sources = [st.session_state.sources[i] for i in top_indices]

            context = "\n\n".join(relevant_chunks)

            # Generate answer with Claude
            client = Anthropic(api_key=st.session_state.api_key)
            try:
                response = client.messages.create(
                    model="claude-3-sonnet-20240229",  # Or use latest model
                    max_tokens=1000,
                    system="You are a helpful assistant. Use the following context to answer the user's question accurately and concisely. If the context doesn't have the information, say so.",
                    messages=[
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {prompt}"}
                    ]
                )
                answer = response.content[0].text
            except Exception as e:
                answer = f"Error generating response: {str(e)}"

            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)

            # Display sources
            st.subheader("Sources Used")
            for source, chunk in zip(relevant_sources, relevant_chunks):
                with st.expander(f"From {source}"):
                    st.write(chunk)
else:
    st.info("Please upload files or connect a Google Sheet to start chatting.")
