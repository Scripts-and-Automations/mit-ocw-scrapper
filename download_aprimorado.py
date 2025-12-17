#!/usr/bin/env python3
"""
Downloader aprimorado para MIT OCW:
- tenta baixar PDFs das lecture-notes
- se der erro em HTTP, converte para HTTPS e retenta
"""

import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, TooManyRedirects

# Cursos a processar (aqui só 18-712, mas você pode adicionar mais slugs)
COURSES = [
    "18-712-introduction-to-representation-theory-fall-2010",
]

# Seções e possíveis caminhos onde as lecture-notes podem estar
SECTION_PATHS = {
    "lecture_notes": [
        "pages/lecture-notes",
        "resources/lecture-notes",
    ],
}

def extract_slug(course_id):
    """Extrai o slug do curso de uma URL ou slug puro."""
    if course_id.startswith("http"):
        parts = urlparse(course_id).path.strip("/").split("/")
        idx = parts.index("courses")
        return parts[idx+1]
    return course_id

def get_soup(url):
    """Faz GET e devolve um BeautifulSoup, ou None em caso de erro."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except (TooManyRedirects, RequestException):
        return None

def find_pdfs_in_page(url):
    """Retorna lista de links absolutos para todos os <a href='*.pdf'> da página."""
    soup = get_soup(url)
    if not soup:
        return []
    out = []
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"].strip()
        out.append(urljoin(url, href))
    return out

def download_file(pdf_url, dest_folder):
    """
    Baixa um PDF.
    Se falhar em HTTP, converte para HTTPS e retenta.
    """
    fn = os.path.basename(pdf_url)
    dst = os.path.join(dest_folder, fn)
    if os.path.exists(dst):
        print(f"  - {fn} já existe, pulando.")
        return

    def fetch(url):
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.content

    try:
        data = fetch(pdf_url)
    except Exception:
        if pdf_url.lower().startswith("http://"):
            secure = "https://" + pdf_url[len("http://"):]
            print(f"    tentando HTTPS para {fn}...", end=" ")
            try:
                data = fetch(secure)
                print("OK")
            except Exception:
                print("falhou")
                return
        else:
            print(f"    falha ao baixar {fn}")
            return

    with open(dst, "wb") as f:
        f.write(data)
    print(f"  + salvo {fn}")

def download_course(course_id):
    slug = extract_slug(course_id)
    base = f"https://ocw.mit.edu/courses/{slug}"
    print(f"\n=== Curso {slug} ===")

    for section, paths in SECTION_PATHS.items():
        pdfs = []
        for sub in paths:
            url = f"{base}/{sub}/"
            print(f"  tentando {section} em {sub}/ ...", end=" ")
            found = find_pdfs_in_page(url)
            if found:
                print(f"OK ({len(found)} PDFs)")
                pdfs = found
                break
            else:
                print("nenhum PDF aqui.")

        if not pdfs:
            print(f"  ➡️ seção {section} não encontrada.")
            continue

        out_dir = os.path.join("downloads", slug, section)
        os.makedirs(out_dir, exist_ok=True)
        for pdf in pdfs:
            download_file(pdf, out_dir)

def main():
    for cid in COURSES:
        download_course(cid)

if __name__ == "__main__":
    main()