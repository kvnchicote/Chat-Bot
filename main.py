"""Punto de entrada para PyCharm: indexar, preguntar o iniciar el bot."""
import argparse
import logging
from pathlib import Path
from ragbot.config import ROOT


def main():
    parser = argparse.ArgumentParser(description='Chatbot RAG PDF → Telegram (PyCharm)')
    sub = parser.add_subparsers(dest='command', required=True)
    idx = sub.add_parser('indexar', help='Extrae e indexa un PDF (reemplaza al anterior)')
    idx.add_argument('pdf', type=Path, help='Ruta del PDF, ej.: documentos/ejemplo.pdf')
    ask = sub.add_parser('preguntar', help='Consulta desde consola, sin Telegram')
    ask.add_argument('pregunta', nargs='+', help='Pregunta sobre el documento')
    sub.add_parser('bot', help='Inicia Telegram y espera mensajes')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
    from ragbot.pdf_index import PdfKnowledgeBase
    kb = PdfKnowledgeBase()
    if args.command == 'indexar':
        info = kb.ingest(args.pdf)
        print(f'✅ PDF indexado: {info["filename"]} | {info["pages"]} páginas | {info["chunks"]} fragmentos')
    elif args.command == 'preguntar':
        from ragbot.qa import StrictPdfQA
        print(StrictPdfQA(kb).answer(' '.join(args.pregunta)))
    else:
        if not kb.status()['ready']:
            raise RuntimeError('Primero indexá un PDF: python main.py indexar documentos/ejemplo.pdf')
        from ragbot.qa import StrictPdfQA
        from ragbot.telegram_app import create_app
        print(f'✅ Bot activo | PDF: {kb.status()["filename"]} | Detener: Ctrl+C')
        create_app(StrictPdfQA(kb), kb).run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
