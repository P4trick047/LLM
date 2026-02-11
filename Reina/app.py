import streamlit as st
import pandas as pd
import requests
from io import StringIO
from anthropic import Anthropic, AnthropicError
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

# ────────────────────────────────────────────────
#  CACHE EMBEDDING MODEL
# ────────────────────────────────────────────────
@st.cache_resource
def get_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions


# ────────────────────────────────────────────────
#  TEXT SPLITTING
# ────────────────────────────────────────────────
def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


# ────────────────────────────────────────────────
#  FETCH GOOGLE SHEET AS CSV
# ────────────────────────────────────────────────
def fetch_google_sheet(url: str) -> pd.DataFrame | None:
    if 'docs.google.com/spreadsheets/d/' not in url:
        st.error("Invalid Google Sheet URL format.")
        return None

    try:
        sheet_id = url.split('/d/')[1].split('/')[0]
        csv_url = f"https://docs.google.com/spreadsheets/d/1ATllEOsVzBIHm4egctEVbf7CDzmHtFfyEMmT7U6NNnw/edit?gid=0#gid=0{sheet_id}/export?format=csv"
        response = requests.get(csv_url, timeout=15)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))
        df = df.drop_duplicates()
        return df
    except Exception as e:
        st.error(f"Could not fetch Google Sheet: {str(e)}")
        return None


# ────────────────────────────────────────────────
#  PROCESS DATAFRAME → CHUNKS + EMBEDDINGS
# ────────────────────────────────────────────────
def process_df(df: pd.DataFrame, source_name: str, model) -> Tuple[List[str], np.ndarray, List[str]]:
    chunks = []
    sources = []
    for _, row in df.iterrows():
        # You can customize this line if you want to use only specific columns
        chunk = ' '.join(f"{col}: {str(row[col])}" for col in df.columns)
        chunks.append(chunk)
        sources.append(source_name)
    embeddings = model.encode(chunks, show_progress_bar=False)
    return chunks, embeddings, sources


# ────────────────────────────────────────────────
#  PROCESS UPLOADED FILE
# ────────────────────────────────────────────────
def process_file(file, model) -> Tuple[List[str], np.ndarray, List[str]]:
    chunks = []
    sources = []

    if file.type == "text/csv":
        df = pd.read_csv(file)
        df = df.drop_duplicates()
        file_chunks, file_emb, file_src = process_df(df, file.name, model)
        chunks.extend(file_chunks)
        sources.extend(file_src)
        return chunks, file_emb, sources

    else:  # .txt, .md
        text = file.read().decode('utf-8', errors='ignore')
        file_chunks = split_text(text)
        for chunk in file_chunks:
            chunks.append(chunk)
            sources.append(file.name)
        embeddings = model.encode(chunks, show_progress_bar=False)
        return chunks, embeddings, sources


# ────────────────────────────────────────────────
#  MAIN APP
# ────────────────────────────────────────────────
st.set_page_config(page_title="RAG Chatbot – Google Sheets", layout="wide")
st.title("RAG Chatbot with Google Sheets Integration")

# Parameters
CHUNK_SIZE = 500
OVERLAP = 100
TOP_K = 3

# Session state
if 'chunks' not in st.session_state:
    st.session_state.chunks = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'messages' not in st.session_state:
    st.session_state.messages = []


# ─── SIDEBAR ─────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    # Try to load API key from secrets first
    api_key = st.secrets.get("ANTHROPIC_API_KEY", None)

    if api_key:
        st.session_state.api_key = api_key
        st.success("API key loaded from secrets ✓")
    else:
        st.session_state.api_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="You can also place it in .streamlit/secrets.toml as ANTHROPIC_API_KEY = \"sk-...\""
        )

    st.header("Data Sources")

    # File upload
    uploaded_files = st.file_uploader(
        "Upload .txt / .md / .csv files",
        accept_multiple_files=True,
        type=['txt', 'md', 'csv']
    )

    if st.button("Process Uploaded Files") and uploaded_files:
        if not st.session_state.api_key:
            st.error("Please provide Claude API key first.")
        else:
            with st.spinner("Processing files..."):
                model = get_embedding_model()
                all_chunks, all_emb, all_src = [], [], []
                for file in uploaded_files:
                    if file.name.lower().endswith(('.txt', '.md', '.csv')):
                        ch, emb, src = process_file(file, model)
                        all_chunks.extend(ch)
                        all_emb.extend(emb)
                        all_src.extend(src)
                    else:
                        st.warning(f"Skipped unsupported file: {file.name}")

                if all_chunks:
                    st.session_state.chunks.extend(all_chunks)
                    if st.session_state.embeddings is None:
                        st.session_state.embeddings = np.array(all_emb)
                    else:
                        st.session_state.embeddings = np.vstack([st.session_state.embeddings, all_emb])
                    st.session_state.sources.extend(all_src)
                    st.success(f"Added {len(all_chunks)} chunks from {len(uploaded_files)} file(s)")

    # Google Sheet
    sheet_url = st.text_input("https://docs.google.com/spreadsheets/d/1ATllEOsVzBIHm4egctEVbf7CDzmHtFfyEMmT7U6NNnw/edit?gid=0#gid=0")
    if st.button("Connect & Process Sheet"):
        if not sheet_url:
            st.warning("https://docs.google.com/spreadsheets/d/1ATllEOsVzBIHm4egctEVbf7CDzmHtFfyEMmT7U6NNnw/edit?gid=0#gid=0")
        elif not st.session_state.api_key:
            st.error("Please provide Claude API key first.")
        else:
            with st.spinner("Fetching and processing sheet..."):
                df = fetch_google_sheet(sheet_url)
                if df is not None:
                    model = get_embedding_model()
                    ch, emb, src = process_df(df, "Google Sheet", model)
                    st.session_state.chunks.extend(ch)
                    if st.session_state.embeddings is None:
                        st.session_state.embeddings = emb
                    else:
                        st.session_state.embeddings = np.vstack([st.session_state.embeddings, emb])
                    st.session_state.sources.extend(src)
                    st.success(f"Processed {len(ch)} rows from Google Sheet")


# ─── CHAT INTERFACE ─────────────────────────────────
if st.session_state.get('embeddings') is not None and len(st.session_state.chunks) > 0:
    # Show history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New message
    if prompt := st.chat_input("Ask anything about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not st.session_state.api_key:
            st.error("Claude API key is missing.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        model = get_embedding_model()
                        q_emb = model.encode(prompt)

                        # Cosine similarity
                        norms = np.linalg.norm(st.session_state.embeddings, axis=1)
                        sim = np.dot(st.session_state.embeddings, q_emb) / (norms * np.linalg.norm(q_emb) + 1e-10)
                        top_idx = np.argsort(sim)[-TOP_K:][::-1]

                        rel_chunks = [st.session_state.chunks[i] for i in top_idx]
                        rel_sources = [st.session_state.sources[i] for i in top_idx]

                        context = "\n\n".join(rel_chunks)

                        client = Anthropic(api_key=st.session_state.api_key)

                        response = client.messages.create(
                            model="claude-3-5-sonnet-20241022",     # ← updated model
                            max_tokens=1200,
                            temperature=0.3,
                            system=(
                                "You are a precise, helpful assistant. "
                                "Answer using ONLY the provided context. "
                                "If the information is not in the context, say: "
                                "\"I don't have that information in the provided data.\""
                            ),
                            messages=[{
                                "role": "user",
                                "content": f"Context:\n{context}\n\nQuestion: {prompt}"
                            }]
                        )

                        answer = response.content[0].text
                        st.markdown(answer)

                        # Sources
                        with st.expander("Sources used", expanded=False):
                            for src, chunk in zip(rel_sources, rel_chunks):
                                st.markdown(f"**{src}**\n\n{chunk[:400]}...")

                        st.session_state.messages.append({"role": "assistant", "content": answer})

                    except AnthropicError as e:
                        st.error(f"Claude API error: {e}")
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")

else:
    st.info("Connect a Google Sheet or upload files to start asking questions.")
