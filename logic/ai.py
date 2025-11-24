from openai import OpenAI
import streamlit as st

def ask_ai(full_text):
    """აგზავნის ტექსტს AI-თან და იღებს პასუხს"""
    
    # გასაღების შემოწმება
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        return "⚠️ API Key არ არის მითითებული!"

    client = OpenAI(api_key=api_key)
    
    # პროფესიონალური პრომპტი
    system_prompt = """
    შენ ხარ გამოცდილი ტენდერების მენეჯერი.
    დაწერე ვრცელი, სტრუქტურირებული ტექნიკური წინადადება (Methodology).
    
    ფორმატი: HTML (მხოლოდ body ნაწილი).
    
    გამოიყენე:
    - <h2> ლურჯი სათაურები
    - <table border="1"> მონაცემებისთვის
    - <ul> სიები
    
    სტრუქტურა:
    1. შესავალი და მზადყოფნა.
    2. მომსახურების გაწევის გეგმა.
    3. პერსონალი და რესურსები (ცხრილით).
    4. ხარისხის კონტროლი.
    5. დასკვნა.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"დოკუმენტაცია:\n\n{full_text[:25000]}"} 
        ]
    )
    return response.choices[0].message.content