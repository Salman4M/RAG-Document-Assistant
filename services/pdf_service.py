import io
import pypdf # for plain text
import pdfplumber # for tables



def extract_content_by_page(file_bytes: bytes) -> list[dict]:
    pages = []
    pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, (pypdf_page,plumber_page) in enumerate(
            zip(pdf_reader.pages,pdf.pages), start=1
        ):
            #plain text via pypdf
            text= pypdf_page.extract_text() or ""

            #tables via pdfplumber > convert to markdown
            tables_markdown = ""
            tables = plumber_page.extract_tables()
            for table in tables:
                #convert tables to markdown
                tables_markdown += _table_to_markdown(table) + "\n\n"

            combined = text.strip()
            if tables_markdown:
            #merges plain text and markdown tables into one string
            #double newline separates them cleanly
                combined += "\n\n" + tables_markdown.strip()
            #only pages that have content
            if combined.strip():
                pages.append(
                    {
                        "text":combined,
                        "page_number":page_num
                    }
                )
    
    return pages

def _table_to_markdown(table: list[list]) -> str:
    if not table or not table[0]:
        return ""

    rows = []
    header = [str(cell or "") for cell in table[0]]
    rows.append("| " + " | ".join(header) + " |")
    rows.append("| " + " | ".join("---" * len(header)) + " |")

    for row in table[1:]:
        cells = [str(cell or "") for cell in row]
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)

def chunk_text(pages: list[dict], chunk_size: int = 1000, overlap: int = 200)->list[dict]:
    chunks = []
    for page in pages:
        text = page["text"]
        page_number = page["page_number"]
        chunk_index = 0
        start = 0
        #till page ends
        while start < len(text):
            end = start + chunk_size
            chunk  = text[start:end]

            if chunk.strip():
                chunk.append({
                    "text":chunk,
                    "page_number":page_number,
                    "chunk_index":chunk_index
                })
                chunk_index+=1
            
            start+=chunk_size - overlap

    return chunks