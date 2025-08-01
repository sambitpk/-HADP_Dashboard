# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import gc
from googletrans import Translator
import numpy as np
import bcrypt

# === PAGE CONFIG ===
st.set_page_config(page_title="Jansahayak RTI Dashboard", layout="wide")

# === CUSTOM CSS FOR MARATHI ===
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;700&display=swap');
    .marathi {
        font-family: 'Noto Sans Devanagari', sans-serif;
    }
    .stTextInput > div > input,
    .stSelectbox > div > div > div,
    .stMarkdown {
        font-family: 'Noto Sans Devanagari', sans-serif;
    }
    .info-box {
        background-color: #dbeafe;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-family: 'Noto Sans Devanagari', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# === TRANSLATIONS ===
translations = {
    "en": {
        "title": "Jansahayak RTI Dashboard",
        "srNo": "Sr. No.",
        "taluka": "Taluka",
        "year": "Year",
        "workName": "Work Name",
        "amount": "Amount (in thousands)",
        "agency": "Agency",
        "type": "Type (A/G)",
        "filterTaluka": "Filter by Taluka",
        "filterYear": "Filter by Year",
        "filterType": "Filter by Type",
        "searchPlaceholder": "Search by work name...",
        "searchButton": "Search",
        "all": "All",
        "interestingFact": "Interesting Fact",
        "tableTitle": "Project Details",
        "costByTaluka": "Total Project Cost by Taluka",
        "projectsByYear": "Number of Projects by Year",
        "projectTypeDist": "Project Type Distribution",
        "language": "Language",
        "english": "English",
        "marathi": "Marathi",
        "errorFile": "Error: HADP_WORK_LIST_MASTER.xlsx not found. Please upload the file.",
        "errorColumns": "Error: Required columns not found in the Excel file.",
        "chatbotTitle": "Jansahayak Chatbot",
        "chatbotPrompt": "Ask a question about the projects...",
        "chatbotError": "Chatbot is currently unavailable.",
        "demoHint": "Try: Which taluka has highest spending?",
        "adminLogin": "Admin Login",
        "adminPassword": "Password",
        "loginButton": "Log In",
        "loginFailed": "❌ Invalid password",
        "adminPage": "Admin Panel",
        "clearChat": "Clear Chat History",
        "chatCleared": "✅ Chat history cleared!",
        "viewChat": "View Chat History",
        "exportChat": "Export Chat (JSON)",
        "backToDashboard": "Back to Dashboard"
    },
    "mr": {
        "title": "जनसहायक आरटीआय डॅशबोर्ड",
        "srNo": "अ. क्र.",
        "taluka": "तालुका",
        "year": "वर्ष",
        "workName": "कामाचे नाव",
        "amount": "प्र.मा रक्कम (हजारात)",
        "agency": "यंत्रणा",
        "type": "प्रकार (A/G)",
        "filterTaluka": "तालुक्याने फिल्टर करा",
        "filterYear": "वर्षानुसार फिल्टर करा",
        "filterType": "प्रकारानुसार फिल्टर करा",
        "searchPlaceholder": "कामाच्या नावाने शोधा...",
        "searchButton": "शोधा",
        "all": "सर्व",
        "interestingFact": "रोचक तथ्य",
        "tableTitle": "प्रकल्प तपशील",
        "costByTaluka": "तालुक्यांनुसार एकूण प्रकल्प खर्च",
        "projectsByYear": "वर्षानुसार प्रकल्पांची संख्या",
        "projectTypeDist": "प्रकल्प प्रकार वितरण",
        "language": "भाषा",
        "english": "इंग्रजी",
        "marathi": "मराठी",
        "errorFile": "त्रुटी: HADP_WORK_LIST_MASTER.xlsx फाइल सापडली नाही. कृपया फाइल अपलोड करा.",
        "errorColumns": "त्रुटी: एक्सेल फाइलमध्ये आवश्यक कॉलम्स सापडले नाहीत.",
        "chatbotTitle": "जनसहायक चॅटबॉट",
        "chatbotPrompt": "प्रकल्पांबद्दल प्रश्न विचारा...",
        "chatbotError": "चॅटबॉट उपलब्ध नाही.",
        "demoHint": "प्रयत्न करा: कोणत्या तालुक्यात सर्वाधिक खर्च झाला?",
        "adminLogin": "प्रशासक लॉगिन",
        "adminPassword": "पासवर्ड",
        "loginButton": "लॉग इन",
        "loginFailed": "❌ अवैध पासवर्ड",
        "adminPage": "प्रशासक पॅनेल",
        "clearChat": "चॅट इतिहास साफ करा",
        "chatCleared": "✅ चॅट इतिहास साफ केला!",
        "viewChat": "चॅट इतिहास पहा",
        "exportChat": "चॅट एक्सपोर्ट (JSON)",
        "backToDashboard": "डॅशबोर्डवर परत जा"
    }
}

language_names = {
    "en": translations["en"]["english"],
    "mr": translations["mr"]["marathi"]
}

# === HELPER: Abbreviate Numbers ===
def abbreviate_number(num):
    if pd.isna(num) or num is None:
        return "0"
    if num >= 1000000:
        return f"{num / 1000000:.1f}M"
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return str(int(num))

# === LOAD DATA ===
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("data/HADP_WORK_LIST_MASTER.xlsx")  # Ensure file is in data/
        column_mapping = {
            "अ. क्र.": "srNo",
            "तालुका": "taluka",
            "वर्ष": "year",
            "कामाचे नाव": "workName",
            "प्र.मा रक्कम": "amount",
            "यंत्रणा": "agency",
            "प्रकार (A/G)": "type"
        }
        missing = [col for col in column_mapping.keys() if col not in df.columns]
        if missing:
            st.error(f"{translations['en']['errorColumns']} Missing: {', '.join(missing)}")
            return pd.DataFrame()
        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=["srNo", "amount"])
        df["srNo"] = df["srNo"].astype(int)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df.fillna({"taluka": "", "workName": "", "agency": "", "type": ""})
        return df
    except FileNotFoundError:
        st.error(translations["en"]["errorFile"])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# === CHAT HISTORY ===
CHAT_FILE = "chat_history.json"

def load_chat_history():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_chat_history(messages):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)

# === TRANSLATOR ===
@st.cache_resource
def get_translator():
    return Translator()

def translate_text(text, dest_lang):
    if dest_lang == "en":
        return text
    try:
        translator = get_translator()
        result = translator.translate(text, src='en', dest='mr')
        return result.text
    except Exception:
        return "माफ करा, भाषांतर उपलब्ध नाही"

# === RULE-BASED CHATBOT (NO transformers, NO torch) ===
def get_chatbot_response(prompt, df, lang):
    try:
        if df.empty:
            return "No data." if lang == "en" else "माहिती नाही."

        prompt_lower = prompt.lower()

        if "highest spending" in prompt_lower or "top taluka" in prompt_lower or "खर्च" in prompt_lower:
            top = df.groupby("taluka")["amount"].sum().idxmax()
            amt = df.groupby("taluka")["amount"].sum().max()
            resp = f"Taluka {top} has highest spending: ₹{amt:,.0f}K."
            return resp if lang == "en" else translate_text(resp, "mr")

        elif "how many projects" in prompt_lower or "एकूण प्रकल्प" in prompt_lower:
            cnt = len(df)
            resp = f"There are {cnt} projects."
            return resp if lang == "en" else translate_text(resp, "mr")

        elif "average cost" in prompt_lower or "सरासरी खर्च" in prompt_lower:
            avg = df["amount"].mean()
            resp = f"Average cost: ₹{avg/1000:.1f}K."
            return resp if lang == "en" else translate_text(resp, "mr")

        elif "most common type" in prompt_lower or "प्रकार" in prompt_lower:
            typ = df["type"].mode()[0]
            cnt = df["type"].value_counts()[typ]
            resp = f"Most common type: '{typ}' ({cnt} projects)."
            return resp if lang == "en" else translate_text(resp, "mr")

        elif "agency" in prompt_lower and "highest" in prompt_lower:
            agency = df.groupby("agency")["amount"].sum().idxmax()
            resp = f"Agency with highest spending: {agency}."
            return resp if lang == "en" else translate_text(resp, "mr")

        else:
            resp = "Ask about spending, projects, or types. Try: 'Which taluka has highest spending?'"
            return resp if lang == "en" else translate_text(resp, "mr")

    except Exception:
        return translations[lang]["chatbotError"]

# === ADMIN LOGIN ===
def admin_login():
    t = translations[lang]
    st.title(t["adminLogin"])
    pwd = st.text_input(t["adminPassword"], type="password")
    if st.button(t["loginButton"]):
        try:
            expected = st.secrets["admin"]["password"]
            if bcrypt.checkpw(pwd.encode(), bcrypt.hashpw(expected.encode(), bcrypt.gensalt())):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error(t["loginFailed"])
        except:
            st.error("Admin config missing.")

def admin_panel():
    t = translations[lang]
    st.title(t["adminPage"])
    if st.button(t["backToDashboard"]):
        st.session_state.admin_logged_in = False
        st.rerun()

    st.subheader(t["viewChat"])
    log = load_chat_history()
    for msg in log:
        st.text(f"[{msg['time']}] {msg['role']}: {msg['content']}")

    if st.button(t["clearChat"]):
        if os.path.exists(CHAT_FILE):
            os.remove(CHAT_FILE)
        st.session_state.messages = [{"role": "assistant", "content": translations[lang]["chatbotPrompt"]}]
        st.success(t["chatCleared"])

    st.download_button(
        label=t["exportChat"],
        data=json.dumps(log, indent=2, ensure_ascii=False),
        file_name="chat_history.json",
        mime="application/json"
    )

# === MAIN DASHBOARD ===
def dashboard():
    df = load_data()
    if df.empty:
        return

    lang = st.sidebar.selectbox(
        translations["en"]["language"],
        options=["en", "mr"],
        format_func=lambda x: language_names[x],
        key="lang_select"
    )
    t = translations[lang]
    st.session_state.lang = lang

    st.title(t["title"])

    # Filters
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        taluka_filter = st.selectbox(t["filterTaluka"], [""] + sorted(df["taluka"].unique()),
                                     format_func=lambda x: t["all"] if x == "" else x)
    with col2:
        year_filter = st.selectbox(t["filterYear"], [""] + sorted(df["year"].unique()),
                                   format_func=lambda x: t["all"] if x == "" else x)
    with col3:
        type_filter = st.selectbox(t["filterType"], [""] + sorted(df["type"].unique()),
                                   format_func=lambda x: t["all"] if x == "" else x)

    col4, col5 = st.columns([3, 1])
    with col4:
        search_term = st.text_input(t["searchPlaceholder"], key="search")
    with col5:
        search_button = st.button(t["searchButton"])

    filtered_df = df.copy()
    if taluka_filter: filtered_df = filtered_df[filtered_df["taluka"] == taluka_filter]
    if year_filter: filtered_df = filtered_df[filtered_df["year"] == year_filter]
    if type_filter: filtered_df = filtered_df[filtered_df["type"] == type_filter]
    if search_button and search_term:
        filtered_df = filtered_df[filtered_df["workName"].str.contains(search_term, case=False, na=False)]

    # Interesting Fact
    if not filtered_df.empty:
        max_taluka = df.groupby("taluka")["amount"].sum().idxmax()
        max_amt = df.groupby("taluka")["amount"].sum().max()
        fact_en = f"Taluka '{max_taluka}' has highest cost: ₹{max_amt:,.0f}K."
        fact = fact_en if lang == "en" else translate_text(fact_en, "mr")
        st.markdown(f'<div class="info-box">{t["interestingFact"]}: {fact}</div>', unsafe_allow_html=True)

    # Visualizations
    if not filtered_df.empty:
        st.subheader(t["costByTaluka"])
        cost_df = df.groupby("taluka")["amount"].sum().reset_index()
        fig1 = px.bar(cost_df, x="taluka", y="amount", labels={"amount": t["amount"], "taluka": t["taluka"]},
                      color_discrete_sequence=["#3B82F6"])
        fig1.update_layout(xaxis_tickangle=45, font=dict(family="Noto Sans Devanagari"))
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader(t["projectsByYear"])
        proj_df = df.groupby("year").size().reset_index(name="count")
        fig2 = px.line(proj_df, x="year", y="count", labels={"count": t["projectsByYear"], "year": t["year"]},
                       color_discrete_sequence=["#10B981"])
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader(t["projectTypeDist"])
        type_df = df["type"].value_counts().reset_index(name="count")
        type_df.columns = ["type", "count"]
        fig3 = px.pie(type_df, names="type", values="count", color_discrete_sequence=["#3B82F6", "#10B981"])
        st.plotly_chart(fig3, use_container_width=True)

    # Table
    st.subheader(t["tableTitle"])
    disp_df = filtered_df.copy()
    disp_df["amount"] = disp_df["amount"].apply(abbreviate_number)
    disp_df.columns = [t[key] for key in ["srNo", "taluka", "year", "workName", "amount", "agency", "type"]]
    st.dataframe(disp_df, use_container_width=True)

    # Chatbot
    st.subheader(t["chatbotTitle"])
    st.caption(t["demoHint"])

    if "messages" not in st.session_state:
        st.session_state.messages = load_chat_history()
        if not st.session_state.messages:
            st.session_state.messages = [{"role": "assistant", "content": t["chatbotPrompt"]}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(t["chatbotPrompt"]):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chatbot_response(prompt, df, lang)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Save to chat history
        from datetime import datetime
        log_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": "user",
            "content": prompt
        }
        log_response = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": "assistant",
            "content": response
        }
        chat_log = load_chat_history()
        chat_log.extend([log_entry, log_response])
        save_chat_history(chat_log)

# === MAIN ROUTER ===
def main():
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "lang" not in st.session_state:
        st.session_state.lang = "en"

    lang = st.session_state.lang

    if not st.session_state.admin_logged_in:
        choice = st.sidebar.radio("Mode", ["Dashboard", "Admin Login"])
        if choice == "Admin Login":
            admin_login()
        else:
            dashboard()
    else:
        st.sidebar.markdown("---")
        if st.sidebar.button(translations[lang]["backToDashboard"]):
            st.session_state.admin_logged_in = False
            st.rerun()
        admin_panel()

if __name__ == "__main__":
    main()
