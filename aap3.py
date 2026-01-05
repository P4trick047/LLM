import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from openai import OpenAI
import json  # For potential data handling

# Your DeepSeek API key (use st.secrets["DEEPSEEK_API_KEY"] in production for security)
DEEPSEEK_API_KEY = "sk-42ec3644fd1f4fcab6b84b40b9424cb0"

# SharePoint direct download URL (fix sharing as noted)
SHAREPOINT_URL = "https://aayursolutions.sharepoint.com/:x:/r/sites/healthcareoperations/_layouts/15/Doc.aspx?sourcedoc=%7B34765B3E-BB02-42E3-874B-D33CD2B4C312%7D&file=Denial_Code_Library_Template%201.xlsx&action=default&mobileredirect=true"

# Initialize DeepSeek client
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Hardcoded fallback data from the provided sheet (unique entries; duplicates removed for efficiency)
FALLBACK_DATA = [
    {"Denial Code": "CO-50", "Scenario / Sub-Category": "Medical Necessity", "Denial Short Description": "DME not medically necessary", "Detailed Explanation": "Records do not support DME need", "Step-by-Step Action": "Review LCD → Add clinicals → Appeal", "EHR Notes to Add": "Clinical necessity documented", "Documents Needed": "Doctor notes, CMN", "Payer-Specific Notes": "Medicare LCD", "Rebill / Appeal Required": "Appeal", "TAT (Days)": 30, "Additional Notes": "Use LCD language"},
    {"Denial Code": "CO-204", "Scenario / Sub-Category": "Authorization", "Denial Short Description": "No prior authorization", "Detailed Explanation": "Auth required but missing", "Step-by-Step Action": "Request retro auth → Appeal", "EHR Notes to Add": "Retro auth requested", "Documents Needed": "Auth form", "Payer-Specific Notes": "Plan specific", "Rebill / Appeal Required": "Appeal", "TAT (Days)": 30, "Additional Notes": "High dollar DME"},
    {"Denial Code": "CO-16", "Scenario / Sub-Category": "Missing Info", "Denial Short Description": "Incomplete CMN", "Detailed Explanation": "CMN missing details", "Step-by-Step Action": "Complete CMN → Rebill", "EHR Notes to Add": "CMN completed", "Documents Needed": "CMN/DWO", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "Rebill", "TAT (Days)": 7, "Additional Notes": "Common DME denial"},
    {"Denial Code": "CO-96", "Scenario / Sub-Category": "Non-covered", "Denial Short Description": "Item not covered", "Detailed Explanation": "DME excluded from benefits", "Step-by-Step Action": "Write-off / Bill patient", "EHR Notes to Add": "Non-covered noted", "Documents Needed": "Policy", "Payer-Specific Notes": "Medicare excluded", "Rebill / Appeal Required": "No", "TAT (Days)": 5, "Additional Notes": "ABN needed"},
    {"Denial Code": "CO-29", "Scenario / Sub-Category": "Timely Filing", "Denial Short Description": "Late DME claim", "Detailed Explanation": "Filed after payer limit", "Step-by-Step Action": "Check proof → Appeal", "EHR Notes to Add": "Timely proof added", "Documents Needed": "Submission proof", "Payer-Specific Notes": "Strict timelines", "Rebill / Appeal Required": "Appeal", "TAT (Days)": 45, "Additional Notes": "Track DOS"},
    {"Denial Code": "CO-151", "Scenario / Sub-Category": "Invalid NPI", "Denial Short Description": "Supplier NPI invalid", "Detailed Explanation": "Inactive billing NPI", "Step-by-Step Action": "Correct NPI → Rebill", "EHR Notes to Add": "NPI corrected", "Documents Needed": "CMS NPI record", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "Rebill", "TAT (Days)": 7, "Additional Notes": "Credentialing"},
    {"Denial Code": "CO-27", "Scenario / Sub-Category": "Eligibility", "Denial Short Description": "Patient not eligible", "Detailed Explanation": "Coverage inactive on DOS", "Step-by-Step Action": "Verify eligibility → Bill patient", "EHR Notes to Add": "Eligibility checked", "Documents Needed": "Eligibility report", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "No", "TAT (Days)": 5, "Additional Notes": "Front-end check"},
    {"Denial Code": "CO-4", "Scenario / Sub-Category": "Modifier Missing", "Denial Short Description": "RR/NU missing", "Detailed Explanation": "Required DME modifier missing", "Step-by-Step Action": "Add modifier → Rebill", "EHR Notes to Add": "Modifier added", "Documents Needed": "Claim form", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "Rebill", "TAT (Days)": 7, "Additional Notes": "RR/NU critical"},
    {"Denial Code": "CO-18", "Scenario / Sub-Category": "Duplicate", "Denial Short Description": "Duplicate DME claim", "Detailed Explanation": "Claim already processed", "Step-by-Step Action": "Verify EOB → Close", "EHR Notes to Add": "Duplicate verified", "Documents Needed": "EOB", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "No", "TAT (Days)": 3, "Additional Notes": "System issue"},
    {"Denial Code": "CO-16", "Scenario / Sub-Category": "Missing Info", "Denial Short Description": "Proof of delivery missing", "Detailed Explanation": "No POD on file", "Step-by-Step Action": "Obtain POD → Rebill", "EHR Notes to Add": "POD uploaded", "Documents Needed": "Signed POD", "Payer-Specific Notes": "—", "Rebill / Appeal Required": "Rebill", "TAT (Days)": 7, "Additional Notes": "Critical for DME"},
]

# Function to load Excel data (try online, fallback to hardcoded)
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_excel_data(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        df = pd.read_excel(BytesIO(response.content), sheet_name="DME_Denials_100")
        st.info("Loaded data from SharePoint successfully.")
        return df
    except Exception as e:
        st.warning(f"SharePoint download failed ({str(e)}). Using hardcoded fallback data.")
        return pd.DataFrame(FALLBACK_DATA)

# Load data
df = load_excel_data(SHAREPOINT_URL)

# Get context from data (filter based on query for better relevance)
def get_data_context(df, query):
    if df.empty:
        return "No data available."
    
    # Filter rows where 'Denial Code' or 'Denial Short Description' matches query (case-insensitive)
    filtered = df[df.apply(lambda row: query.lower() in ' '.join(row.astype(str)).lower(), axis=1)]
    if filtered.empty:
        data_text = df.to_string(index=False)[:4000]  # Full data if no match
    else:
        data_text = filtered.to_string(index=False)
    
    return f"Use this denial code library data to answer accurately:\n{data_text}"

# Streamlit UI
st.title("DeepSeek-Powered Grok-like Chatbot with DME Denial Codes")
st.caption("Ask about DME denials; uses your Excel data for context.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question (e.g., 'What to do for CO-50 denial?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get context
    context = get_data_context(df, prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": f"You are a helpful Grok-like AI for healthcare denials. Use the provided DME denial code data for precise answers. {context}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"Error: {str(e)}"
            message_placeholder.error(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
