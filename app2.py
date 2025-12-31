import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

# CORRECT OLLAMA IMPORT - THIS WORKS ON STREAMLIT CLOUD
from langchain_community.chat_models import ChatOllama

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

# ========== CONFIGURATION ==========
# CRITICAL: This link MUST directly download the file in incognito mode
EXCEL_SHARE_LINK = "https://aayursolutions.sharepoint.com/:x:/s/healthcareoperations/IQA-W3Y0ArvjQodL0zzStMMSAXL_eV3lw2vv9nG9Kt4qRBQ?e=2gKJkT&download=1"

CACHE_TTL = 3600
df_global = None

@st.cache_data(ttl=CACHE_TTL)
def load_excel_data(share_link: str):
    global df_global
    try:
        # Ensure download parameter
        if "&download=1" not in share_link:
            share_link += "&download=1"

        resp = requests.get(share_link, timeout=60)
        resp.raise_for_status()

        # Try different header rows (0 to 4)
        df = None
        for header_row in range(5):
            try:
                temp_df = pd.read_excel(BytesIO(resp.content), header=header_row)
                if temp_df.shape[1] > 2 and temp_df.shape[0] > 1:
                    df = temp_df
                    st.info(f"Successfully loaded using header row {header_row}")
                    break
            except:
                continue

        if df is None:
            st.error("Could not read the Excel file. No valid table found.")
            return pd.DataFrame()

        # Clean column names
        df.columns = df.columns.astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)

        # Auto-detect denial code column by content (looks for CO-, PR-, etc.)
        code_col = None
        for col in df.columns:
            sample = df[col].dropna().astype(str).str.upper()
            if sample.str.contains(r'\bCO-|\bPR-|\bCR-|\bPI-').any():
                code_col = col
                st.info(f"Detected denial code column: '{col}'")
                break

        if not code_col:
            # Fallback: use first column
            code_col = df.columns[0]
            st.warning(f"No denial code pattern found. Using first column: '{code_col}'")

        df = df.rename(columns={code_col: 'Denial Code'})
        df = df.dropna(subset=['Denial Code'])
        df = df.drop_duplicates().reset_index(drop=True)

        st.success(f"Loaded {len(df)} rows | {df['Denial Code'].nunique()} unique codes")
        df_global = df
        return df

    except Exception as e:
        st.error(f"Failed to load Excel: {str(e)}")
        st.info("""
**How to fix the link:**
1. Open the file in SharePoint
2. Click Share → "Anyone with the link" → Can view
3. Click "Copy link" (get a fresh link)
4. Add `&download=1` at the end
5. Test in incognito browser — it MUST download the .xlsx file directly
        """)
        return pd.DataFrame()

# ========== TOOLS ==========
@tool
def lookup_denial_code(code: str) -> str:
    if df_global is None or df_global.empty:
        return "No data loaded. Please refresh."
    matches = df_global[df_global['Denial Code'].str.contains(code.strip(), case=False, na=False)]
    if matches.empty:
        return f"No match for '{code}'. Try 'list codes' first."
    result = ""
    for _, row in matches.iterrows():
        result += f"**{row['Denial Code']}**\n"
        for col in df_global.columns:
            if col != 'Denial Code':
                result += f"- **{col}**: {row.get(col, 'N/A')}\n"
        result += "\n"
    return result

@tool
def list_all_codes() -> str:
    if df_global is None or df_global.empty:
        return "No data loaded."
    return df_global[['Denial Code']].drop_duplicates().to_markdown(index=False)

agent_tools = [lookup_denial_code, list_all_codes]

# ========== AGENT ==========
@st.cache_resource
def create_agent():
    llm = ChatOllama(model="llama3.1", temperature=0)
    system_prompt = SystemMessage(content="""
You are a DME Denial Code Expert.
Use lookup_denial_code("CO-50") for full details.
Use list_all_codes() for an overview.
Answer clearly with bullet points.
""")
    return create_react_agent(
        model=llm.bind_tools(agent_tools),
        tools=agent_tools,
        state_modifier=system_prompt
    )

# ========== UI ==========
st.set_page_config(page_title="DME Denial Code Agent", layout="wide")
st.title("🚫 DME Denial Code Library Agent")
st.markdown("**Live from Excel Online** • Local AI • Daily Updates")

with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

# Load data
if df_global is None:
    with st.spinner("Loading from Excel Online..."):
        df_global = load_excel_data(EXCEL_SHARE_LINK)

if df_global is None or df_global.empty:
    st.stop()

# Metrics
st.metric("Unique Codes", df_global['Denial Code'].nunique())
with st.expander("📋 View Full Data"):
    st.dataframe(df_global)

# Agent
agent = create_agent()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask: 'CO-50', 'list codes', 'appeals', etc."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({"messages": [("user", prompt)]})
            response = result["messages"][-1].content
        st.markdown(response)

    # st.session_state.messages.append({"role": "assistant", "content": response))
if prompt := st.chat_input("Ask: 'CO-50', 'list codes', 'appeals', etc."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({"messages": [("user", prompt)]})
            response = result["messages"][-1].content
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

st.caption("Built with Streamlit • LangGraph • Ollama Llama3.1")
