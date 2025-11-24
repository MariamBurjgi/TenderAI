import streamlit as st
import streamlit as st
import pdfplumber
from docx import Document
import io
import re
from openai import OpenAI

def check_password():
    """აბრუნებს True-ს თუ პაროლი სწორია, სხვა შემთხვევაში False."""
    
    # თუ პაროლი ჯერ არ შეუყვანიათ ან არასწორია
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        # პაროლის შესაყვანი ველი
        password_input = st.text_input("შეიყვანეთ წვდომის კოდი", type="password")
        
        if st.button("შესვლა"):
            # ვამოწმებთ სეიფში შენახულ პაროლთან
            if password_input == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun() # გვერდს გადატვირთავს და შეუშვებს
            else:
                st.error("❌ პაროლი არასწორია!")
        return False
    return True

# თუ პაროლი არასწორია, კოდი აქ ჩერდება და ქვემოთ აღარ მიდის
if not check_password():
    st.stop()


# --- სეიფის გახსნა ---
if "OPENAI_API_KEY" in st.secrets:
    API_KEY = st.secrets["OPENAI_API_KEY"]
else:
    API_KEY = ""

# --- ფუნქციები ---
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
    if not API_KEY:
        return "⚠️ API Key არ არის მითითებული!"
    
    client = OpenAI(api_key=API_KEY)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "შენ ხარ ტენდერების ექსპერტი. შეაჯამე მოცემული დოკუმენტაცია."},
            {"role": "user", "content": f"აი ყველა ფაილის გაერთიანებული ტექსტი:\n\n{full_text[:15000]}"} 
        ]
    )
    return response.choices[0].message.content

# --- ვიზუალი ---
st.set_page_config(page_title="Tender AI", page_icon="📂")
st.title("📂 Tender AI - მრავალი ფაილის ანალიზი")
st.write("მონიშნეთ და გადმოყარეთ ყველა PDF ფაილი ერთად!")

# 🔄 ცვლილება 1: accept_multiple_files=True (ბევრი ფაილის მიღება)
uploaded_files = st.file_uploader(
    "ატვირთეთ ფაილები (PDF)", 
    type="pdf", 
    accept_multiple_files=True 
)

# თუ თუნდაც 1 ფაილი მაინც არის ატვირთული
if uploaded_files:
    st.success(f"✅ ატვირთულია {len(uploaded_files)} ფაილი!")
    
    combined_text = "" # აქ შევაგროვებთ ყველა ფაილის ტექსტს ერთად
    
    # 🔄 ცვლილება 2: ციკლი (Loop), რომელიც სათითაოდ კითხულობს ფაილებს
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            file_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    file_text += text + "\n"
            
            # თითოეული ფაილის ტექსტს ვაწებებთ საერთო "ქვაბში"
            combined_text += f"\n\n--- ფაილი: {file.name} ---\n{file_text}"

    # კონტაქტების პოვნა
    emails, phones = extract_contact_info(combined_text)
    
    with st.sidebar:
        st.header("📊 ნაპოვნია:")
        if emails: st.write("📧", ", ".join(emails))
        if phones: st.write("📱", ", ".join(phones))

    with st.expander("ნახე ყველა ფაილის გაერთიანებული ტექსტი"):
        st.text(combined_text)
    
    if st.button("გააანალიზე ყველა ფაილი (AI)"):
        if not API_KEY:
            st.error("API Key აკლია!")
        else:
            with st.spinner("AI კითხულობს ყველა ფაილს..."):
                try:
                    analysis = ask_ai(combined_text)
                    st.markdown("### 🤖 შემაჯამებელი ანალიზი:")
                    st.write(analysis)
                    
                    docx = create_word_docx(analysis)
                    st.download_button("📥 გადმოწერა Word-ში", docx, "summary.docx")
                except Exception as e:
                    st.error(f"შეცდომა: {e}")