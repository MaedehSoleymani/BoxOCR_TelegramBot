from io import BytesIO
from pypdf import PdfReader

def get_pdf_page_count(file_data):
    pdf_file = BytesIO(file_data)
    reader = PdfReader(pdf_file)
    if reader.is_encrypted:
        raise ValueError("encrypted_pdf")
    return len(reader.pages)

async def process_file(file_data, file_type):
    """
    اتصال به API اصلی BoxOCR در این قسمت انجام می‌شود.
    فعلاً پردازش OCR پیاده‌سازی نشده است.
    """
    raise NotImplementedError("OCR API is not connected yet.")