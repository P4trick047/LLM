import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

# THIS IS THE CORRECT IMPORT THAT WORKS ON STREAMLIT CLOUD
from langchain_community.chat_models import ChatOllama

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

# ========== CONFIGURATION ==========
# PASTE YOUR MICROSOFT EXCEL ONLINE SHARE LINK HERE
EXCEL_SHARE_LINK = "https://aayursolutions.sharepoint.com/:x:/s/healthcareoperations/E<your_long_code_here>?e=XXXXXX"  # ← REPLACE THIS!

CACHE_TTL = 3600  # Refresh every hour

# Global DataFrame
df_global = None

@st.cache_data(ttl=CACHE_TTL)
def load_excel_data(share_link: str):
    """Load Excel from MS Online (public share link) and deduplicate."""
    global df_global
    try:
        # Method 1: Add &download=1
        download_url = share_link + ("&download=1" if "?" in share_link else "?download=1")
        resp = requests.get(download_url, timeout=30)
        resp.raise_for_status()
        df = pd.read_excel(BytesIO(resp.content))
    except:
        # Method 2: OneDrive base64 fallback
        try:
            encoded = base64.b64encode(share_link.encode()).decode()
            encoded = encoded.replace('/', '_').replace('+', '-').rstrip('=')
            direct_url = f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"
            resp = requests.get(direct_url, timeout=30)
            resp.raise_for_status()
            df = pd.read_excel(BytesIO(resp.content))
        except Exception as e:
            st.error(f"Failed to load Excel: {e}\n\nCheck your share link — it must allow 'Anyone with the link' to view and download.")
            return pd.DataFrame()

    # Deduplicate repeated rows (common in templates)
    df = df.drop_duplicates().reset_index(drop=True)
    st.success(f"Loaded {len(df)} unique rows | {df['Denial Code'].nunique()} codes")
    df_global = df
    return df

# ========== TOOLS ==========
@tool
def lookup_denial_code(code: str) -> str:
    """Get full details for a specific denial code (e.g., 'CO-50')."""
    if df_global is None or df_global.empty:
        return "No data loaded yet. Click 'Refresh Excel Data'."

    matches = df_global[df_global['Denial Code'].str.upper() == code.strip().upper()]
    if matches.empty:
        matches = df_global[df_global['Denial Code'].str.contains(code.strip(), case=False, na=False)]

    if matches.empty:
        return f"No match found for '{code}'. Available codes: {', '.join(sorted(df_global['Denial Code'].unique()))}"

    result = "**Denial Code Details**\n\n"
    for _, row in matches.iterrows():
        result += f"**{row['Denial Code']}** — {row['Scenario / Sub-Category']}\n"
        result += f"- **Description**: {row['Denial Short Description']}\n"
        result += f"- **Explanation**: {row['Detailed Explanation']}\n"
        result += f"- **Action**: {row['Step-by-Step Action']}\n"
        result += f"- **EHR Notes**: {row['EHR Notes to Add']}\n"
        result += f"- **Documents Needed**: {row['Documents Needed']}\n"
        result += f"- **Payer Notes**: {row['Payer-Specific Notes']}\n"
        result += f"- **Rebill/Appeal**: {row['Rebill / Appeal Required']}\n"
        result += f"- **TAT**: {row['TAT (Days)']} days\n"
        result += f"- **Additional**: {row['Additional Notes']}\n\n"
    return result

@tool
def list_all_codes() -> str:
    """List all unique denial codes with categories."""
    if df_global is None or df_global.empty:
        return "No data loaded."
    summary = df_global[['Denial Code', 'Scenario / Sub-Category', 'Rebill / Appeal Required', 'TAT (Days)']].drop_duplicates()
    return summary.to_markdown(index=False)

@tool
def analyze_denials(query: str) -> str:
    """Analyze denials: appeals, high TAT, missing info, etc."""
    if df_global is None or df_global.empty:
        return "No data loaded."

    df = df_global
    lower = query.lower()
    if "appeal" in lower:
        appeals = df[df['Rebill / Appeal Required'].str.contains("Appeal", na=False)]
        return f"**Appeals Required ({len(appeals)} codes):**\n\n{appeals[['Denial Code', 'TAT (Days)']].to_markdown(index=False)}"
    elif "tat" in lower or "turnaround" in lower:
        return f"**TAT Summary**\n\n{df['TAT (Days)'].describe().to_string()}\n\n**Highest TAT Codes**\n{df.nlargest(5, 'TAT (Days)')[['Denial Code', 'TAT (Days)']]}"
    elif "missing" in lower:
        missing = df[df['Scenario / Sub-Category'] == 'Missing Info']
        return f"**Missing Info Denials**\n\n{missing[['Denial Code', 'Documents Needed', 'Step-by-Step Action']].to_markdown(index=False)}"
    else:
        return "Try asking: 'appeals', 'high TAT', 'missing info'."

@tool
def custom_python(code: str) -> str:
    """Run custom Python analysis on the denial data."""
    if df_global is None or df_global.empty:
        return "No data loaded."
    try:
        repl = PythonREPL()
        safe_code = f"import pandas as pd\ndf = df_global.copy()\n{code}"
        return repl.run(safe_code)
    except Exception as e:
        return f"Code error: {str(e)}"

agent_tools = [lookup_denial_code, list_all_codes, analyze_denials, custom_python]

# ========== AGENT ==========
@st.cache_resource
def create_agent():
    llm = ChatOllama(model="llama3.1", temperature=0)

    system_prompt = SystemMessage(content="""
You are a DME Denial Code Expert Agent using the daily-updated Denial_Code_Library_Template 1.xlsx.

Available codes include: CO-50 (Medical Necessity), CO-16 (Missing Info), CO-204 (Authorization), CO-96 (Non-covered), CO-29 (Timely Filing), etc.

Workflow:
1. Use list_all_codes() to show all codes.
2. Use lookup_denial_code("CO-50") for full details (action steps, documents, TAT, appeal/rebill).
3. Use analyze_denials("appeal") for summaries like appeals or high TAT.
4. Use custom_python() for advanced queries.

Answer clearly with bullet points and tables when possible.
""")

    return create_react_agent(
        model=llm.bind_tools(agent_tools),
        tools=agent_tools,
        prompt=system_prompt
    )

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="DME Denial Code Agent", layout="wide")
st.title("🚫 DME Denial Code Library Agent")
st.markdown("**Live from your MS Excel Online file** • Local AI • Daily Updates")

# Sidebar
with st.sidebar:
    st.header("Data Controls")
    if st.button("🔄 Refresh Excel Data", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Share link must allow **Anyone with the link** to view/download.")

# Load data
if df_global is None:
    with st.spinner("Loading denial library from Excel Online..."):
        df_global = load_excel_data(EXCEL_SHARE_LINK)

if df_global is not None and not df_global.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Unique Codes", df_global['Denial Code'].nunique())
    with col2:
        st.metric("Total Rows (Unique)", len(df_global))

    with st.expander("📋 View Raw Data"):
        st.dataframe(df_global, use_container_width=True)
else:
    st.warning("No data loaded. Check your EXCEL_SHARE_LINK at the top of the code.")
    st.stop()

# Agent
agent = create_agent()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Options
col_debug, col_preview = st.columns(2)
debug = col_debug.checkbox("Show Debug")
preview = col_preview.checkbox("Preview Data")

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask about a denial code, e.g., 'CO-50 action steps' or 'list appeals'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = agent.invoke({"messages": [("user", prompt)]})
            response = result["messages"][-1].content

        if debug:
            with st.expander("Agent Trace"):
                st.json([{"type": m.type, "content": str(m.content)[:500]} for m in result["messages"]])

        if preview:
            with st.expander("Data Preview"):
                st.dataframe(df_global.head())

        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

st.caption("Built with Streamlit • LangGraph • Ollama (Llama3.1) • Your Excel Online Data")
