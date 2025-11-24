import streamlit as st
import pdfplumber
import pandas as pd
from docx import Document
import io
import re
import zipfile
from openai import OpenAI

# --- 1. კონფიგურაცია და უსაფრთხოება ---
st.set_page_config(page_title="Tender AI Pro", page_icon="📂")

if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    API_KEY = ""

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        st.title("🔒 შესვლა სისტემაში")
        pwd = st.text_input("პაროლი", type="password")
        if st.button("შესვლა"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("პაროლი არასწორია")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. დამხმარე ფუნქციები ---

def extract_contact_info(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phones = re.findall(r'\b5\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}\b', text)
    return set(emails), set(phones)

def create_word_docx(text_content):
    doc = Document()
    doc.add_heading('AI სატენდერო ანალიზი', 0)
    doc.add_paragraph(text_content)
    bio = io.BytesIO()
    doc.save(bio)
    return bio

def ask_ai(full_text):
    if not API_KEY: return "⚠️ API Key არ არის!"
    client = OpenAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "შენ ხარ ტენდერების ექსპერტი. გააანალიზე ყველა მიწოდებული ფაილი (PDF, Word, Excel) ერთად."},
            {"role": "user", "content": f"აი მასალები:\n\n{full_text[:25000]}"} 
        ]
    )
    return response.choices[0].message.content

# --- 3. ფაილების წამკითხავი ფუნქცია (უნივერსალური) ---
def process_file(file_bytes, file_name):
    """ეს ფუნქცია იღებს ფაილს და აბრუნებს ტექსტს, ტიპის მიხედვით"""
    text_content = ""
    
    try:
        # --> PDF
        if file_name.endswith(".pdf"):
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt: text_content += txt + "\n"
        
        # --> WORD (.docx)
        elif file_name.endswith(".docx"):
            doc = Document(file_bytes)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        
        # --> EXCEL
        elif file_name.endswith(".xlsx") or file.name.endswith(".xls"):
            df = pd.read_excel(file_bytes)
            text_content = df.to_string(index=False)
            
    except Exception as e:
        return f"\n[შეცდომა {file_name}-ის კითხვისას: {e}]\n"

    return f"\n\n--- ფაილი: {file_name} ---\n{text_content}"

# --- 4. მთავარი ინტერფეისი ---
st.title("📂 Tender AI - ყველა ფორმატი")
st.write("ატვირთეთ: PDF, Word, Excel ან ZIP არქივი.")

uploaded_files = st.file_uploader(
    "ფაილები", 
    type=["pdf", "xlsx", "xls", "docx", "zip"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ მიღებულია {len(uploaded_files)} ფაილი")
    combined_text = ""
    
    for file in uploaded_files:
        # თუ ZIP ფაილია - ვხსნით და შიგნით ვიხედებით
        if file.name.endswith(".zip"):
            with zipfile.ZipFile(file) as z:
                for sub_file_name in z.namelist():
                    # ვფილტრავთ სისტემურ ფაილებს (Mac-ის __MACOSX და ა.შ.)
                    if not sub_file_name.startswith("__") and not sub_file_name.endswith("/"):
                        with z.open(sub_file_name) as f:
                            # ფაილს ვკითხულობთ ბაიტებად
                            file_bytes = io.BytesIO(f.read())
                            # ვაგზავნით დასამუშავებლად
                            combined_text += process_file(file_bytes, sub_file_name)
        
        # თუ ჩვეულებრივი ფაილია
        else:
            combined_text += process_file(file, file.name)

    # შედეგების გამოტანა
    emails, phones = extract_contact_info(combined_text)
    with st.sidebar:
        st.header("🔍 ნაპოვნია")
        if emails: st.write("📧", ", ".join(emails))
        if phones: st.write("📱", ", ".join(phones))

    with st.expander("ნახე სრული ტექსტი"):
        st.text(combined_text)
    
    if st.button("✨ გააანალიზე ყველაფერი (AI)"):
        if not API_KEY:
            st.error("API Key არ არის!")
        else:
            with st.spinner("AI აანალიზებს ZIP-ს, Word-ს, PDF-ს და Excel-ს..."):
                try:
                    res = ask_ai(combined_text)
                    st.markdown("### 🤖 ანალიზი:")
                    st.write(res)
                    docx = create_word_docx(res)
                    st.download_button("📥 გადმოწერა", docx, "analysis.docx")
                except Exception as e:
                    st.error(f"შეცდომა: {e}")