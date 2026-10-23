import pytest
from app.documents.extractor import DocumentExtractor
from app.documents.retrieval import DocumentRetriever
from app.core.exceptions import DocumentProcessingError


def test_txt_extraction():
    content = b"This is a test document explaining the architecture of JARVIS personal assistant."
    full_text, sections = DocumentExtractor.extract_text("test_doc.txt", content)
    assert "architecture of JARVIS" in full_text
    assert len(sections) == 1


def test_csv_extraction():
    content = b"Name,Role,Status\nJARVIS,Core AI,Active\nVision,Sensor,Standby"
    full_text, sections = DocumentExtractor.extract_text("data.csv", content)
    assert "JARVIS | Core AI | Active" in full_text


def test_unsupported_file_extension():
    with pytest.raises(DocumentProcessingError):
        DocumentExtractor.extract_text("malicious.exe", b"binary content")


def test_empty_file_rejection():
    with pytest.raises(DocumentProcessingError):
        DocumentExtractor.extract_text("empty.txt", b"")
