import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
import re
from typing import List, Dict, Tuple

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot with Google Sheets",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def create_embedding(text: str, dimension: int = 128) -> np.ndarray:
    embedding = np.zeros(dimension)
    for i, char in enumerate(text):
        char_code = ord(char)
        index = char_code % dimension
        embedding[index] += char_code / 255
    magnitude = np.linalg.norm(embedding)
    if magnitude > 0:
        embedding = embedding / magnitude
    return embedding

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    dot_product = np.dot(vec_a, vec_b)
    magnitude_a = np.linalg.norm(vec_a)
    magnitude_b = np.linalg.norm(vec_b)
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def extract_sheet_id(url: str) -> str:
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None

def fetch_google_sheet_data(url: str) -> Tuple[bool, str, pd.DataFrame]:
    try:
        sheet_id = extract_sheet_id(url)
        if not sheet_id:
            return False, "Invalid Google Sheets URL", None
        
        api_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:json"
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        json_text = response.text[47:-2]
        data = json.loads(json_text)
        
        rows = []
        for row in data['table']['rows']:
            row_data = [cell['v'] if cell else '' for cell in row['c']]
            rows.append(row_data)
        
        if len(rows) == 0:
            return False, "No data found", None
        
        df = pd.DataFrame(rows[1:], columns=rows[0])
        return True, f"Loaded {len(df)} rows", df
        
    except Exception as e:
        return False, f"Error: {str(e)}", None

def dataframe_to_text(df: pd.DataFrame, sheet_name: str) -> str:
    text = f"Data from: {sheet_name}\n\n"
    for idx, row in df.iterrows():
        row_text = ", ".join([f"{col}: {row[col]}" for col in df.columns])
        text += f"Row {idx + 1}: {row_text}\n"
    return text

def process_document(name: str, content: str, source: str = "file", url: str = None):
    chunks = chunk_text(content)
    doc_id = datetime.now().timestamp()
    
    document = {
        'id': doc_id,
        'name': name,
        'content': content,
        'source': source,
        'url': url,
        'uploaded_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'chunks': len(chunks)
    }
    st.session_state.documents.append(document)
    
    for idx, chunk in enumerate(chunks):
        vector = {
            'id': f"{doc_id}_chunk_{idx}",
            'doc_id': doc_id,
            'doc_name': name,
            'text': chunk,
            'embedding': create_embedding(chunk)
        }
        st.session_state.vector_store.append(vector)
    
    return len(chunks)

def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[Dict]:
    if len(st.session_state.vector_store) == 0:
        return []
    
    query_embedding = create_embedding(query)
    scored_chunks = []
    
    for chunk in st.session_state.vector_store:
        score = cosine_similarity(query_embedding, chunk['embedding'])
        scored_chunks.append({**chunk, 'score': score})
    
    scored_chunks.sort(key=lambda x: x['score'], reverse=True)
    return scored_chunks[:top_k]

def call_claude_api(query: str, context: str, api_key: str) -> str:
    try:
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        prompt = f"""You are a helpful assistant. Answer based on this context:

Context:
{context}

Question: {query}

Answer clearly and concisely."""
        
        data = {
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 1000,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        return result['content'][0]['text'] if result.get('content') else "Error generating answer"
        
    except Exception as e:
        return f"Error: {str(e)}"

def delete_document(doc_id):
    st.session_state.documents = [d for d in st.session_state.documents if d['id'] != doc_id]
    st.session_state.vector_store = [v for v in st.session_state.vector_store if v['doc_id'] != doc_id]

def main():
    st.markdown('<div class="main-header">🤖 RAG Chatbot with Google Sheets</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Upload documents or connect Google Sheets and ask questions</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_key = st.text_input(
            "Claude API Key",
            type="password",
            value=st.session_state.api_key
        )
        st.session_state.api_key = api_key
        
        if not api_key:
            st.warning("⚠️ Enter API key")
        
        st.divider()
        st.header("📊 Data Sources")
        
        st.subheader("Upload Files")
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['txt', 'md', 'csv'],
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Process Files", type="primary"):
            with st.spinner("Processing..."):
                for file in uploaded_files:
                    content = file.read().decode('utf-8')
                    chunks = process_document(file.name, content, "file")
                    st.success(f"✅ {file.name}: {chunks} chunks")
        
        st.subheader("Google Sheet")
        sheet_url = st.text_input("Sheet URL")
        
        if st.button("Connect", type="primary"):
            if sheet_url:
                with st.spinner("Fetching..."):
                    success, message, df = fetch_google_sheet_data(sheet_url)
                    if success:
                        text = dataframe_to_text(df, "Sheet")
                        chunks = process_document("Google Sheet", text, "google-sheets", sheet_url)
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        st.divider()
        st.header("📚 Documents")
        
        if st.session_state.documents:
            for doc in st.session_state.documents:
                with st.expander(f"{'📊' if doc['source'] == 'google-sheets' else '📄'} {doc['name']}"):
                    st.write(f"Source: {doc['source']}")
                    st.write(f"Chunks: {doc['chunks']}")
                    if st.button("Delete", key=f"del_{doc['id']}"):
                        delete_document(doc['id'])
                        st.rerun()
        else:
            st.info("No documents")
        
        st.write(f"**Vectors:** {len(st.session_state.vector_store)}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "sources" in msg:
                    with st.expander("Sources"):
                        for s in msg["sources"]:
                            st.write(f"**{s['name']}:** {s['snippet']}")
        
        if prompt := st.chat_input("Ask a question..."):
            if not st.session_state.api_key:
                st.error("Enter API key")
            elif not st.session_state.vector_store:
                st.error("Upload data first")
            else:
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        chunks = retrieve_relevant_chunks(prompt)
                        context = "\n\n".join([f"[{c['doc_name']}]\n{c['text']}" for c in chunks])
                        answer = call_claude_api(prompt, context, st.session_state.api_key)
                        
                        st.write(answer)
                        sources = [{"name": c['doc_name'], "snippet": c['text'][:100] + "..."} for c in chunks]
                        
                        with st.expander("Sources"):
                            for s in sources:
                                st.write(f"**{s['name']}:** {s['snippet']}")
                        
                        st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    
    with col2:
        st.header("ℹ️ Guide")
        st.markdown("""
        ### Steps
        1. Add API Key
        2. Upload files/sheet
        3. Ask questions
        
        ### Google Sheets
        - Must be public
        - Use full URL
        
        ### Examples
        - "Total revenue?"
        - "List customers"
        - "Top product?"
        """)
        
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.rerun()

if __name__ == "__main__":
    main()
