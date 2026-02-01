from PyPDF2 import PdfReader
from docx import Document
from pathlib import Path


def read_pdf(file_path: Path) -> str:
    text = ""
    reader = PdfReader(str(file_path))
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text


def read_docx(file_path: Path) -> str:
    doc = Document(str(file_path))
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return "\n".join(text)


def read_cv(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return read_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return read_docx(file_path)
    else:
        raise ValueError("Unsupported file type")
