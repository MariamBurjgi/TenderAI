import streamlit as st
import re

# მოდულები
from logic.auth import check_password
from logic.files import read_uploaded_files, extract_contact_info
from logic.ai import ask_ai
from logic.document import create_word_from_html

# 1. კონფიგურაცია
st.set_page_config(page_title="Tender AI Pro", page_icon="🚀")

# 2. პაროლის შემოწმება
if not check_password():
    st.stop()

# 3. მთავარი ინტერფეისი
st.title("🚀 Tender AI - პროფესიონალი ასისტენტი")
st.write("ატვირთეთ ნებისმიერი ფაილი (ZIP, PDF, Excel, Word).")

uploaded_files = st.file_uploader("ფაილები", type=["pdf", "xlsx", "xls", "docx", "zip"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"✅ მიღებულია {len(uploaded_files)} ფაილი")
    
    # ფაილების დამუშავება
    combined_text = read_uploaded_files(uploaded_files)

    # კონტაქტების პოვნა
    emails, phones = extract_contact_info(combined_text)
    
    with st.sidebar:
        st.header("🔍 ნაპოვნია")
        if emails: st.write("📧", ", ".join(emails))
        if phones: st.write("📱", ", ".join(phones))

    # AI ანალიზი და დოკუმენტის შექმნა
    if st.button("✨ დაწერე დოკუმენტი (AI)"):
        with st.spinner("AI მუშაობს..."):
            try:
                raw_response = ask_ai(combined_text)
                
                # --- ტექსტის გასუფთავება (Regex) ---
                # შლის ```html და მსგავს ჩარჩოებს
                html_response = re.sub(r"```[a-zA-Z]*", "", raw_response)
                html_response = html_response.replace("```", "").strip()
                # -----------------------------------

                # ეკრანზე ჩვენება
                st.markdown("### 📝 შედეგი:")
                st.markdown(html_response, unsafe_allow_html=True)
                
                # --- Word-ის შექმნა (ნედლი მასალით) ---
                # აქ ვატანთ ორ რამეს: 1. ლამაზ პასუხს, 2. ნედლ ტექსტს (combined_text)
                docx = create_word_from_html(html_response, combined_text)
                
                st.download_button(
                    label="📥 გადმოწერა Word-ში (სრული პაკეტი)",
                    data=docx,
                    file_name="Proposal_Full.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            except Exception as e:
                st.error(f"შეცდომა: {e}")