from docx import Document
from htmldocx import HtmlToDocx
import io

def create_word_from_html(html_content):
    """აქცევს HTML პასუხს Word დოკუმენტად"""
    doc = Document()
    new_parser = HtmlToDocx()
    
    # სათაური
    doc.add_heading('ტექნიკური წინადადება', 0)
    
    # HTML-ის გადაყვანა Word-ში
    new_parser.add_html_to_document(html_content, doc)
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio