import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import base64
from langchain_community.chat_models import ChatOllama
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
import json
from datetime import datetime

# ========== CONFIGURATION ==========
# PASTE YOUR MS EXCEL ONLINE SHARE LINK HERE
EXCEL_SHARE_LINK = "https://1drv.ms/x/s/yourlink?e=abc OR https://yourcompany.sharepoint.com/:x:/s/Site/EXxx/e=123"

CACHE_TTL = 3600  # 1 hour cache for daily updates

# Global DF (loaded once)
df_global = None

@st.cache_data(ttl=CACHE_TTL)
def load_excel_data(share_link: str):
    """Load & deduplicate MS Excel Online data."""
    global df_global
    try:
        # Direct download
        download_url = share_link + ("&download=1" if "?" in share_link else "?download=1")
        resp = requests.get(download_url, timeout=30)
        resp.raise_for_status()
        df = pd.read_excel(BytesIO(resp.content))
        
        # Deduplicate (your file has repeats)
        df = df.drop_duplicates()
        st.success(f"✅ Loaded {len(df)} unique rows | {df['Denial Code'].nunique()} codes | Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        return df
    except:
        # OneDrive base64 fallback
        try:
            b64 = base64.b64encode(share_link.encode()).decode().replace('/', '_').replace('+', '-').rstrip('=')
            direct_url = f"https://api.onedrive.com/v1.0/shares/u!{b64}/root/content"
            resp = requests.get(direct_url, timeout=30)
            resp.raise_for_status()
            df = pd.read_excel(BytesIO(resp.content))
            df = df.drop_duplicates()
            return df
        except Exception as e:
            st.error(f"❌ Load failed: {e}. Verify link downloads .xlsx directly (incognito test).")
            return pd.DataFrame()

# ========== DENIAL LIBRARY TOOLS ==========
@tool
def lookup_denial_code(code: str) -> str:
    """Lookup full details for a denial code (e.g., 'CO-50')."""
    if df_global is None or df_global.empty:
        return "❌ Load data first (Refresh button)."
    matches = df_global[df_global['Denial Code'].str.contains(code.upper(), case=False, na=False)]
    if matches.empty:
        return f"❌ No match for '{code}'. Try: {', '.join(df_global['Denial Code'].unique())}"
    
    result = "**📋 Denial Details:**\n\n"
    for _, row in matches.iterrows():
        result += f"**Code:** {row['Denial Code']}\n"
        result += f"**Category:** {row['Scenario / Sub-Category']}\n"
        result += f"**Short Desc:** {row['Denial Short Description']}\n"
        result += f"**Explanation:** {row['Detailed Explanation']}\n"
        result += f"**Action:** {row['Step-by-Step Action']}\n"
        result += f"**EHR Notes:** {row['EHR Notes to Add']}\n"
        result += f"**Docs Needed:** {row['Documents Needed']}\n"
        result += f"**Payer Notes:** {row['Payer-Specific Notes']}\n"
        result += f"**Rebill/Appeal:** {row['Rebill / Appeal Required']}\n"
        result += f"**TAT:** {row['TAT (Days)']} days\n"
        result += f"**Notes:** {row['Additional Notes']}\n\n---\n"
    return result.strip()

@tool
def list_codes_summary() -> str:
    """List all unique codes + categories."""
    if df_global is None or df_global.empty:
        return "No data."
    summary = df_global.groupby(['Denial Code', 'Scenario / Sub-Category']).size().reset_index(name='Count')
    return summary.to_markdown(index=False)

@tool
def analyze_denials(query: str) -> str:
    """Analyze: e.g., 'appeal required', 'by TAT', 'medical necessity'."""
    if df_global is None or df_global.empty:
        return "No data."
    df = df_global.copy()
    if 'appeal' in query.lower():
        appeals = df[df['Rebill / Appeal Required'].str.contains('Appeal', na=False)]
        return f"**Appeals ({len(appeals)}):**\n{appeals[['Denial Code', 'TAT (Days)']].to_markdown(index=False)}"
    elif 'tat' in query.lower() or 'turnaround' in query.lower():
        return f"**TAT Summary:**\n{df['TAT (Days)'].describe().to_string()}\nTop TAT: {df.nlargest(3, 'TAT (Days)')[['Denial Code', 'TAT (Days)']].to_markdown(index=False)}"
    elif 'missing info' in query.lower():
        missing = df[df['Scenario / Sub-Category'] == 'Missing Info']
        return f"**Missing Info ({len(missing)}):**\n{missing.to_markdown(index=False)}"
    else:
        # Pandas query
        return df.query(query).to_markdown(index=False) if '==' not in query else df.head().to_markdown()

@tool
def custom_analysis(code: str) -> str:
    """Run Python on data (e.g., 'df[df["TAT (Days)"] > 30]')."""
    if df_global is None:
        return "No data."
    try:
        repl = PythonREPL()
        result = repl.run(f"df = df_global.copy()\n{code}\nprint(df.head())")
        return result
    except Exception as e:
        return f"Error: {e}"

agent_tools = [lookup_denial_code, list_codes_summary, analyze_denials, custom_analysis]

# ========== AGENT ==========
@st.cache_resource
def create_agent():
    llm = ChatOllama(model="llama3.1", temperature=0)
    system = SystemMessage(content="""DME Denial Code Agent. Excel has denial library (CO-50 Medical Necessity, CO-16 Missing Info, etc.).

**Always**:
1. `list_codes_summary()` if unknown query.
2. `lookup_denial_code(CO-XX)` for specifics (actions, TAT, docs).
3. `analyze_denials('appeal')` for summaries.
4. `custom_analysis()` for filters (e.g., TAT>30).

Queries: "Fix CO-16", "Appeals list", "High TAT codes", "Missing info actions."""")
    
    return create_react_agent(llm.bind_tools(agent_tools), tools=agent_tools, state_modifier=system)

# ========== STREAMLIT APP ==========
st.set_page_config(page_title="🚫 DME Denial Agent", layout="wide", initial_sidebar_state="expanded")
st.title("🚫 DME Denial Code Library Agent")
st.markdown("**Powered by your MS Excel Online** | Local AI | Daily Updates")

# Sidebar: Data
with st.sidebar:
    st.header("📊 Data")
    if st.button("🔄 Refresh Excel", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if 'df_global' not in globals() or df_global is None:
        with st.spinner("Loading Denial Library..."):
            df_global = load_excel_data(EXCEL_SHARE_LINK)
    
    if df_global is not None and not df_global.empty:
        st.metric("Rows (Unique)", len(df_global))
        st.metric("Codes", df_global['Denial Code'].nunique())
        st.dataframe(df_global[['Denial Code', 'Scenario / Sub-Category', 'Rebill / Appeal Required', 'TAT (Days)']].drop_duplicates(), use_container_width=True)
        st.info(f"Columns: {', '.join(df_global.columns)}")
    else:
        st.error("🚨 **Paste EXCEL_SHARE_LINK (line 45)** & refresh. Test: Link should download .xlsx.")
        st.stop()

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

agent = create_agent()

col1, col2, col3 = st.columns([1,1,1])
with col1: debug = st.checkbox("🐛 Debug")
with col2: preview = st.checkbox("📋 Preview Data")
with col3: if st.button("🗑️ Clear Chat"): st.session_state.messages = []; st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("e.g., 'What to do for CO-50?' or 'List appeals'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent reasoning... (Llama3.1)"):
            result = agent.invoke({"messages": [("user", prompt)]})
            response = result['messages'][-1].content
            
            if debug:
                with st.expander("🔍 Agent Steps"):
                    st.json({m.type: str(m.content)[:300] for m in result['messages']})
            
            if preview:
                with st.expander("📊 Data Preview"): st.dataframe(df_global.head())
            
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
st.markdown("**💡 Tips**: Natural language OK. Handles lookups, appeals (CO-50/204/29), quick rebills (CO-16/4), TAT analysis. **Local only**.")
