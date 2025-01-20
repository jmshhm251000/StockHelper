from bs4 import BeautifulSoup
from requests import Response


def clean_text(text: str) -> str:
    cleaned_text = text.replace("\n", " ").strip()

    return cleaned_text


def clean_data(html: Response):
    soup = BeautifulSoup(html.text, "html.parser")
    texts = []

    document_type = soup.find("ix:nonnumeric", {"name": "dei:DocumentType"})
    print(document_type.text)