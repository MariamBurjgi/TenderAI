import streamlit as st

def check_password():
    """ამოწმებს პაროლს და ბლოკავს წვდომას თუ არასწორია"""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.title("🔒 სისტემაში შესვლა")
        pwd = st.text_input("შეიყვანეთ პაროლი", type="password")
        
        if st.button("შესვლა"):
            # პაროლის შემოწმება სეიფიდან (secrets.toml)
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ პაროლი არასწორია")
        return False
    return True