import streamlit as st
import pdfplumber
import pandas as pd
from docx import Document
import io
import re
import zipfile
from openai import OpenAI

# --- 1. გვერდის კონფიგურაცია ---
st.set_page_config(page_title="Tender AI", page_icon="📂")

# --- 2. უსაფრთხოება: პაროლის შემოწმება ---
def check_password():
    """აბრუნებს True-ს თუ პაროლი სწორია."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.title("🔒 შესვლა სისტემაში")
        password_input = st.text_input("შეიყვანეთ წვდომის კოდი", type="password")
        if st.button("შესვლა"):
            # პაროლი მოაქვს სეიფიდან (secrets.toml)
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ პაროლი არასწორია!")
        return False
    return True

if not check_password():
    st.stop() # თუ პაროლი არასწორია, კოდი აქ ჩერდება

# --- 3. API Key-ს წამოღება სეიფიდან ---
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    API_KEY = ""

# --- 4. დამხმარე ფუნქციები ---

def extract_contact_info(text):
    # ელ-ფოსტა
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    # ტელეფონი (მარტივი ფორმატი)
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
    if not API_KEY:
        return "⚠️ API Key არ არის მითითებული!"
    
    client = OpenAI(api_key=API_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "შენ ხარ ტენდერების ექსპერტი. გააანალიზე PDF (ტექნიკური დავალება) და Excel (ფასები) ერთად."},
            {"role": "user", "content": f"აი ფაილების ტექსტი:\n\n{full_text[:20000]}"} 
        ]
    )
    return response.choices[0].message.content

# --- 5. მთავარი ინტერფეისი ---

st.title("📂 Tender AI - Pro Version")
st.write("ატვირთეთ PDF (დავალება) და Excel (ხარჯთაღრიცხვა) ერთად.")

# ატვირთვა (PDF + Excel)
uploaded_files = st.file_uploader(
    "აირჩიეთ ფაილები", 
    type=["pdf", "xlsx", "xls", "docx", "zip"], 
    accept_multiple_files=True 
)

if uploaded_files:
    st.success(f"✅ ატვირთულია {len(uploaded_files)} ფაილი!")
    
    combined_text = ""
    
    # ფაილების დამუშავება
    for file in uploaded_files:
        
        # ---> PDF <---
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                file_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        file_text += text + "\n"
            combined_text += f"\n\n--- PDF ფაილი: {file.name} ---\n{file_text}"
            
        # ---> EXCEL <---
        elif file.name.endswith(".xlsx") or file.name.endswith(".xls"):
            try:
                df = pd.read_excel(file)
                # ცხრილის ჩვენება საიტზე
                with st.expander(f"📊 ნახე Excel ცხრილი: {file.name}"):
                    st.dataframe(df)
        # ---> WORD (.docx) ნაწილი <---
        elif file.name.endswith(".docx"):
            try:
                doc = Document(file)
                docx_text = ""
                for para in doc.paragraphs:
                    docx_text += para.text + "\n"
                combined_text += f"\n\n--- Word ფაილი: {file.name} ---\n{docx_text}"
            except Exception as e:
                st.error(f"Word-ის შეცდომა: {e}")

        # ---> ZIP (არქივი) ნაწილი <---
        elif file.name.endswith(".zip"):
            try:
                with zipfile.ZipFile(file) as z:
                    for sub_file_name in z.namelist():
                        # სისტემურ ფაილებს (უცნაური სახელებით) არ ვეხებით
                        if not sub_file_name.startswith("__") and not sub_file_name.endswith("/"):
                            
                            # ვხსნით ფაილს არქივიდან
                            with z.open(sub_file_name) as f:
                                file_bytes = io.BytesIO(f.read()) # მეხსიერებაში ვტვირთავთ
                                
                                # შიგნით ვამოწმებთ, რა ტიპია
                                inner_text = ""
                                
                                # 1. თუ შიგნით PDF-ია
                                if sub_file_name.endswith(".pdf"):
                                    with pdfplumber.open(file_bytes) as pdf:
                                        for page in pdf.pages:
                                            txt = page.extract_text()
                                            if txt: inner_text += txt + "\n"
                                
                                # 2. თუ შიგნით Word-ია
                                elif sub_file_name.endswith(".docx"):
                                    doc = Document(file_bytes)
                                    for para in doc.paragraphs:
                                        inner_text += para.text + "\n"
                                
                                # 3. თუ შიგნით Excel-ია
                                elif sub_file_name.endswith(".xlsx"):
                                    df = pd.read_excel(file_bytes)
                                    inner_text = df.to_string(index=False)
                                
                                if inner_text:
                                    combined_text += f"\n\n--- ZIP-ში ნაპოვნი ფაილი: {sub_file_name} ---\n{inner_text}"
            except Exception as e:
                st.error(f"ZIP-ის გახსნის შეცდომა: {e}")         
                
                # ტექსტად ქცევა AI-სთვის
                excel_text = df.to_string(index=False)
                combined_text += f"\n\n--- Excel ფაილი: {file.name} ---\n{excel_text}"
            except Exception as e:
                st.error(f"Excel-ის შეცდომა: {e}")

    # კონტაქტების პოვნა და ჩვენება
    emails, phones = extract_contact_info(combined_text)
    with st.sidebar:
        st.header("🔍 ნაპოვნი ინფორმაცია")
        if emails: 
            st.markdown("**📧 ელ-ფოსტები:**")
            for e in emails: st.code(e)
        if phones: 
            st.markdown("**📱 ტელეფონები:**")
            for p in phones: st.write(p)

    # ტექსტის ნახვა
    with st.expander("ნახე AI-სთვის გაგზავნილი სრული ტექსტი"):
        st.text(combined_text)
    
    # ანალიზის ღილაკი
    if st.button("✨ გააანალიზე ყველა ფაილი (AI)"):
        if not API_KEY:
            st.error("API Key ვერ მოიძებნა სეიფში!")
        else:
            with st.spinner("AI ამუშავებს მონაცემებს (PDF + Excel)..."):
                try:
                    analysis = ask_ai(combined_text)
                    st.markdown("### 🤖 ანალიზის შედეგი:")
                    st.write(analysis)
                    
                    docx = create_word_docx(analysis)
                    st.download_button("📥 შედეგის გადმოწერა (.docx)", docx, "tender_analizi.docx")
                except Exception as e:
                    st.error(f"AI შეცდომა: {e}")