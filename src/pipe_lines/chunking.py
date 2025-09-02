from pypdf import PdfReader


# def parse_pdf(filepath: str, source_name: str, year: int = None, lang: str = "en"):
#     """PDF 파일을 페이지 단위로 파싱해서 JSON 객체 리스트 반환"""
#     docs = []
#     try:
#         doc = fitz.open(filepath)
#     except Exception as e:
#         print(f"❌ Failed to open {filepath}: {e}")
#         return docs

#     for page_num, page in enumerate(doc, start=1):
#         text = page.get_text("text").strip()
#         if not text:
#             continue

#         docs.append({
#             "text": text,
#             "page": page_num,
#             "source": os.path.basename(filepath),
#             "name": source_name,
#             "year": year,
#             "lang": lang
#         })
#     return docs

