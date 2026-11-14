from io import BytesIO
from pypdf import PdfReader

def get_pdf_page_count(file_data):
    pdf_file = BytesIO(file_data)
    reader = PdfReader(pdf_file)

    if reader.is_encrypted:
        raise ValueError("encrypted_pdf")

    return len(reader.pages)