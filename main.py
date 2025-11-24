import streamlit as st
import re

# მოდულები
from logic.auth import check_password
from logic.files import read_uploaded_files, extract_contact_info
from logic.ai import ask_ai
from logic.document import create_word_from_html

# 1. კონფიგურაცია
st.set_page_config(page_title="Tender AI Pro", page_icon="🚀")

# 2. პაროლი
if not check_password():
    st.stop()

# 3. ინტერფეისი
st.title("🚀 Tender AI - პროფესიონალი ასისტენტი")
st.write("ატვირთეთ ნებისმიერი ფაილი (ZIP, PDF, Excel, Word).")

# --- 🔥 ფუნქცია: HTML-ის იდეალური გასუფთავება ---
def extract_pure_html(text):
    # 1. ვშლით მარკდაუნის ჩარჩოებს (```html ... ```)
    text = re.sub(r"```[a-zA-Z]*", "", text).replace("```", "").strip()
    
    # 2. ვეძებთ სუფთა HTML-ს (პირველი ტეგიდან ბოლო ტეგამდე)
    # ეს იპოვის <h2>-ით დაწყებულ და </table>-ით დამთავრებულ ყველაფერს
    match = re.search(r"<h.*>.*</.*>", text, re.DOTALL)
    
    if match:
        return match.group(0) # ვაბრუნებთ მხოლოდ HTML ნაწილს
    else:
        return text # თუ ვერ იპოვა, ვაბრუნებთ როგორც არის
# ------------------------------------------------

uploaded_files = st.file_uploader("ფაილები", type=["pdf", "xlsx", "xls", "docx", "zip"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"✅ მიღებულია {len(uploaded_files)} ფაილი")
    
    combined_text = read_uploaded_files(uploaded_files)
    emails, phones = extract_contact_info(combined_text)
    
    with st.sidebar:
        st.header("🔍 ნაპოვნია")
        if emails: st.write("📧", ", ".join(emails))
        if phones: st.write("📱", ", ".join(phones))

    if st.button("✨ დაწერე დოკუმენტი (AI)"):
        with st.spinner("AI მუშაობს..."):
            try:
                raw_response = ask_ai(combined_text)
                
                # ვასუფთავებთ პასუხს
                html_response = extract_pure_html(raw_response)

                # ეკრანზე ჩვენება (HTML-ის ინტერპრეტაცია)
                st.markdown("### 📝 შედეგი:")
                st.markdown(html_response, unsafe_allow_html=True)
                
                # Word-ის შექმნა და გადმოწერა
                docx = create_word_from_html(html_response)
                st.download_button(
                    label="📥 გადმოწერა Word-ში",
                    data=docx,
                    file_name="Proposal.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ) 

            except Exception as e:
                st.error(f"შეცდომა: {e}")