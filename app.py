# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from transformers import pipeline
import os

# === PAGE CONFIG ===
st.set_page_config(page_title="Jansahayak Dashboard", layout="wide")

# === CUSTOM CSS FOR MARATHI ===
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;700&display=swap');
    * {
        font-family: 'Noto Sans Devanagari', sans-serif;
    }
    .info-box {
        background-color: #f0f9ff;
        padding: 16px;
        border-radius: 8px;
        margin: 20px 0;
        border-left: 4px solid #3b82f6;
    }
    </style>
""", unsafe_allow_html=True)

# === TRANSLATIONS ===
translations = {
    "en": {
        "title": "Jansahayak Dashboard",
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
        "errorFile": "Error: HADP_WORK_LIST_MASTER.xlsx not found.",
        "errorColumns": "Error: Required columns not found.",
        "chatbotTitle": "Jansahayak Chatbot",
        "chatbotPrompt": "Ask a question about the projects...",
        "chatbotError": "Chatbot is temporarily unavailable."
    },
    "mr": {
        "title": "जनसहायक डॅशबोर्ड",
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
        "errorFile": "त्रुटी: HADP_WORK_LIST_MASTER.xlsx फाइल सापडली नाही.",
        "errorColumns": "त्रुटी: आवश्यक कॉलम्स सापडले नाहीत.",
        "chatbotTitle": "जनसहायक चॅटबॉट",
        "chatbotPrompt": "प्रकल्पांबद्दल प्रश्न विचारा...",
        "chatbotError": "चॅटबॉट आत्ता उपलब्ध नाही."
    }
}

language_names = {
    "en": translations["en"]["english"],
    "mr": translations["mr"]["marathi"]
}

# === NUMBER FORMATTER ===
def abbreviate_number(num):
    if pd.isna(num): return "0"
    return f"{num / 1000:.1f}K" if num >= 1000 else str(int(num))

# === LOAD DATA ===
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("HADP_WORK_LIST_MASTER.xlsx")
        column_mapping = {
            "अ. क्र.": "srNo",
            "तालुका": "taluka",
            "वर्ष": "year",
            "कामाचे नाव": "workName",
            "प्र.मा रक्कम": "amount",
            "यंत्रणा": "agency",
            "प्रकार (A/G)": "type"
        }
        missing = [col for col in column_mapping if col not in df.columns]
        if missing:
            st.error(translations["en"]["errorColumns"])
            return pd.DataFrame()
        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=["srNo", "amount"])
        df["srNo"] = df["srNo"].astype(int)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        return df
    except FileNotFoundError:
        st.error(translations["en"]["errorFile"])
        return pd.DataFrame()

# === LOAD LLM (Small & Fast) ===
@st.cache_resource
def load_model():
    st.info("🧠 Loading AI model (this takes 1-2 minutes on first run)...")
    try:
        pipe = pipeline(
            "text2text-generation",
            model="google/flan-t5-small",
            tokenizer="google/flan-t5-small",
            max_new_tokens=100,
            temperature=0.7,
            device=-1,  # CPU
        )
        st.success("✅ Model loaded!")
        return pipe
    except Exception as e:
        st.error(f"❌ Model load failed: {str(e)}")
        return None

# === CHATBOT FUNCTION ===
def get_chatbot_response(prompt, df, lang):
    try:
        # Load model
        pipe = load_model()
        if not pipe:
            return translations[lang]["chatbotError"]

        # Create simple context
        total = len(df)
        avg = df["amount"].mean()
        top_taluka = df.groupby("taluka")["amount"].sum().idxmax()
        years = f"{df['year'].min()}–{df['year'].max()}"

        context = f"{total} projects ({years}). Avg: ₹{avg/1000:.1f}K. Top: {top_taluka}."

        # Prepare prompt
        lang_name = "English" if lang == "en" else "Marathi"
        input_text = (
            f"Answer in {lang_name}. "
            f"Context: {context} "
            f"Question: {prompt}"
        )

        # Generate
        outputs = pipe(input_text)
        response = outputs[0]["generated_text"].strip()

        return response

    except Exception as e:
        return translations[lang]["chatbotError"]

# === MAIN APP ===
def main():
    df = load_data()
    if df.empty:
        return

    lang = st.sidebar.selectbox(
        translations["en"]["language"],
        options=["en", "mr"],
        format_func=lambda x: language_names[x]
    )
    t = translations[lang]

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
        top = df.groupby("taluka")["amount"].sum().idxmax()
        fact = f"Top spending taluka: {top}."
        if lang == "mr":
            fact = "सर्वाधिक खर्च असलेला तालुका: " + top
        st.markdown(f'<div class="info-box">{t["interestingFact"]}: {fact}</div>', unsafe_allow_html=True)

    # Visualizations
    if not filtered_df.empty:
        st.subheader(t["costByTaluka"])
        fig1 = px.bar(df.groupby("taluka")["amount"].sum().reset_index(),
                      x="taluka", y="amount", labels={"amount": t["amount"], "taluka": t["taluka"]})
        fig1.update_layout(xaxis_tickangle=45, font=dict(family="Noto Sans Devanagari"))
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader(t["projectsByYear"])
        fig2 = px.line(df.groupby("year").size().reset_index(name="count"),
                       x="year", y="count", labels={"count": t["projectsByYear"], "year": t["year"]})
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader(t["projectTypeDist"])
        fig3 = px.pie(df["type"].value_counts().reset_index(), names="type", values="count")
        st.plotly_chart(fig3, use_container_width=True)

    # Table
    st.subheader(t["tableTitle"])
    disp_df = filtered_df.copy()
    disp_df["amount"] = disp_df["amount"].apply(abbreviate_number)
    disp_df.columns = [t[key] for key in ["srNo", "taluka", "year", "workName", "amount", "agency", "type"]]
    st.dataframe(disp_df, use_container_width=True)

    # Chatbot
    st.subheader(t["chatbotTitle"])
    st.caption("Try: 'Which taluka has highest spending?'")

    if "messages" not in st.session_state:
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

if __name__ == "__main__":
    main()
