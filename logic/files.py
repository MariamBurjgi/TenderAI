import pdfplumber
import pandas as pd
from docx import Document
import io
import re
import zipfile
import streamlit as st

def extract_contact_info(text):
    """პოულობს მეილებს და ტელეფონებს"""
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phones = re.findall(r'\b5\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}\b', text)
    return set(emails), set(phones)

def process_single_file(file_bytes, file_name):
    """კითხულობს ერთ ფაილს (PDF/Word/Excel)"""
    text_content = ""
    try:
        if file_name.endswith(".pdf"):
            with pdfplumber.open(file_bytes) as pdf:
                for page in pdf.pages:
                    txt = page.extract_text()
                    if txt: text_content += txt + "\n"
        
        elif file_name.endswith(".docx"):
            doc = Document(file_bytes)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        
        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            df = pd.read_excel(file_bytes)
            df = df.fillna("") 
            text_content = df.to_string(index=False)
            
    except Exception as e:
        return f"\n[შეცდომა ფაილის კითხვისას: {e}]\n"
    
    return f"\n\n--- ფაილი: {file_name} ---\n{text_content}"

def read_uploaded_files(uploaded_files):
    """ამუშავებს ყველა ატვირთულ ფაილს (მათ შორის ZIP-ს)"""
    combined_text = ""
    
    for file in uploaded_files:
        if file.name.endswith(".zip"):
            with zipfile.ZipFile(file) as z:
                for sub in z.namelist():
                    if not sub.startswith("__") and not sub.endswith("/"):
                        with z.open(sub) as f:
                            combined_text += process_single_file(io.BytesIO(f.read()), sub)
        else:
            combined_text += process_single_file(file, file.name)
            
    return combined_text