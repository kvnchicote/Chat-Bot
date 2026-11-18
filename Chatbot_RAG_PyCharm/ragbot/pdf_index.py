"""Cargar PDF, fragmentar por página, generar embeddings y persistirlos en Chroma."""
import hashlib
from pathlib import Path
import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL


class PdfKnowledgeBase:
    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(DB_DIR))
        self.embedder = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

    def _collection(self):
        return self.client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={'hnsw:space': 'cosine'}
        )

    def status(self) -> dict:
        col = self.client.get_collection(COLLECTION_NAME) if COLLECTION_NAME in [c.name for c in self.client.list_collections()] else None
        if col is None or col.count() == 0:
            return {'ready': False, 'chunks': 0, 'filename': None}
        sample = col.get(limit=1, include=['metadatas'])
        return {'ready': True, 'chunks': col.count(), 'filename': sample['metadatas'][0]['filename']}

    def ingest(self, filepath: Path) -> dict:
        filepath = Path(filepath).resolve()
        if not filepath.is_file() or filepath.suffix.lower() != '.pdf':
            raise ValueError('Debés proporcionar un archivo .pdf existente.')
        reader = PdfReader(str(filepath))
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=850, chunk_overlap=130, separators=['\n\n', '\n', '. ', ' ', '']
        )
        records = []
        for page_num, page in enumerate(reader.pages, start=1):
            txt = (page.extract_text() or '').strip()
            if not txt:
                continue
            for part in splitter.split_text(txt):
                if part.strip():
                    records.append((page_num, part.strip()))
        if not records:
            raise RuntimeError('El PDF no tiene texto extraíble. Si es escaneado, primero necesita OCR.')
        # Calculamos todo ANTES de reemplazar la colección, para no borrar datos si algo falla.
        vectors = self.embedder.encode([t for _, t in records], normalize_embeddings=True, batch_size=24).tolist()
        pdf_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
        # Un solo PDF activo: al indexar otro, se elimina el anterior.
        if self.status()["ready"]:
            self.client.delete_collection(COLLECTION_NAME)
        col = self._collection()
        for start in range(0, len(records), 100):
            batch = records[start:start + 100]
            col.upsert(
                ids=[f'{pdf_hash[:12]}_{start + j}' for j in range(len(batch))],
                documents=[t for _, t in batch],
                metadatas=[{'filename': filepath.name, 'page': page, 'sha256': pdf_hash} for page, _ in batch],
                embeddings=vectors[start:start + 100],
            )
        return {'ready': True, 'chunks': len(records), 'filename': filepath.name, 'pages': len(reader.pages)}

    def retrieve(self, question: str, top_k: int = 6) -> list[dict]:
        status = self.status()
        if not status['ready']:
            return []
        vec = self.embedder.encode([question], normalize_embeddings=True).tolist()[0]
        col = self.client.get_collection(COLLECTION_NAME)
        res = col.query(query_embeddings=[vec], n_results=min(top_k, status['chunks']),
                        include=['documents', 'metadatas', 'distances'])
        return [
            {'text': text, 'page': int(meta['page']), 'filename': meta['filename'],
             'similarity': max(-1.0, min(1.0, 1.0 - float(distance)))}
            for text, meta, distance in zip(res['documents'][0], res['metadatas'][0], res['distances'][0])
        ]
