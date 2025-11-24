from openai import OpenAI
import streamlit as st

def ask_ai(full_text):
    """აგზავნის ტექსტს AI-თან და იღებს პასუხს"""
    
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        return "⚠️ API Key არ არის მითითებული!"

    client = OpenAI(api_key=api_key)
    
    # --- განახლებული, მკაცრი პრომპტი ---
    system_prompt = """
    შენ ხარ გამოცდილი ტენდერების მენეჯერი.
    დაწერე ვრცელი ტექნიკური წინადადება (Methodology).
    
    ფორმატი: დააბრუნე მხოლოდ სუფთა HTML კოდი (<html> და <body> ტეგების გარეშე).
    
    მკაცრი მოთხოვნები:
    1. არ გამოიყენო CSS სტილები (style="..."). არანაირი ფერი!
    2. არ გამოიყენო ```html ჩარჩოები.
    3. სათაურებისთვის გამოიყენე <h2> და <h3>.
    4. სიებისთვის გამოიყენე <ul> და <li>.
    5. ცხრილებისთვის გამოიყენე მხოლოდ: <table border="1" width="100%">.
    
    სტრუქტურა:
    1. <h2>შესავალი და მზადყოფნა</h2> (ტექსტი)
    2. <h2>მომსახურების გაწევის გეგმა</h2> (სია <ul>)
    3. <h2>პერსონალი და რესურსები</h2> (აუცილებლად ცხრილი <table>)
    4. <h2>ხარისხის კონტროლი</h2> (ტექსტი)
    5. <h2>დასკვნა</h2>
    """
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"დოკუმენტაცია:\n\n{full_text[:25000]}"} 
        ]
    )
    return response.choices[0].message.content