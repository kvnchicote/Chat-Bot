"""Pruebas offline con dobles de Chroma y Gemini, sin claves ni Internet."""
import json
import pytest
import sys
import types

@pytest.fixture(autouse=True)
def stub_google_types(monkeypatch):
    """Simula solamente la configuración de Gemini en pruebas sin Internet."""
    genai_module = types.ModuleType("google.genai")
    genai_module.types = types.SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)
from ragbot.qa import StrictPdfQA
from ragbot.config import NO_ANSWER

HIT = {'text': 'Un plazo fijo es una inversión en la que se deposita dinero durante un período acordado.', 'page': 1, 'filename': 'ejemplo.pdf', 'similarity': 0.85}

class FakeKB:
    def retrieve(self, question, top_k=6):
        return [HIT]

class FakeResponse:
    def __init__(self, data):
        self.text = json.dumps(data)

class FakeModels:
    def __init__(self, data):
        self.data = data
    def generate_content(self, **kwargs):
        return FakeResponse(self.data)

class FakeClient:
    def __init__(self, data):
        self.models = FakeModels(data)


def test_answer_uses_exact_pdf_quote(monkeypatch):
    monkeypatch.setenv('MIN_SIMILARITY', '0.36')
    qa = StrictPdfQA(FakeKB(), client=FakeClient({'fragmento': 0, 'cita': HIT['text']}), model='fake')
    answer = qa.answer('¿Qué es un plazo fijo?')
    assert HIT['text'] in answer
    assert 'página 1' in answer


def test_rejects_hallucinated_answer(monkeypatch):
    monkeypatch.setenv('MIN_SIMILARITY', '0.36')
    qa = StrictPdfQA(FakeKB(), client=FakeClient({'fragmento': 0, 'cita': 'Las criptomonedas tienen un valor respaldado por el banco central.'}), model='fake')
    assert qa.answer('¿Qué es una criptomoneda?') == NO_ANSWER


def test_explicit_abstention(monkeypatch):
    monkeypatch.setenv('MIN_SIMILARITY', '0.36')
    qa = StrictPdfQA(FakeKB(), client=FakeClient({'fragmento': -1, 'cita': ''}), model='fake')
    assert qa.answer('¿Cuánto cuesta un viaje a Marte?') == NO_ANSWER


def test_low_similarity_rejects_without_asking_ai(monkeypatch):
    monkeypatch.setenv('MIN_SIMILARITY', '0.90')
    qa = StrictPdfQA(FakeKB(), client=FakeClient({'fragmento': 0, 'cita': HIT['text']}), model='fake')
    assert qa.answer('¿Qué es un plazo fijo?') == NO_ANSWER
