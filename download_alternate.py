#!/usr/bin/env python3
import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, TooManyRedirects

COURSES = [
    "18-712-introduction-to-representation-theory-fall-2010"
]

SECTION_PATHS = {
    "lecture_notes":       ["pages/lecture-notes", "resources/lecture-notes"]
    #"assignments":         ["pages/assignments", "pages/lists/problem-sets"]
}

def extract_slug(course_id):
    if course_id.startswith("http"):
        parts = urlparse(course_id).path.strip("/").split("/")
        idx = parts.index("courses")
        return parts[idx+1]
    return course_id

def get_soup(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except (TooManyRedirects, RequestException):
        return None

def find_pdf_buttons(detail_soup, base_url):
    """
    Procura o botão 'Download File' na página de detalhe e retorna o URL absoluto.
    """
    # 1) botão com texto exato
    btn = detail_soup.find("a", string=lambda t: t and "download file" in t.lower())
    # 2) ou <a class="button download"> etc
    if not btn:
        btn = detail_soup.select_one("a.button.download, a.download")
    if btn and btn.has_attr("href"):
        return urljoin(base_url, btn["href"])
    return None

def collect_lecture_pdfs(page_url):
    """Busca links .pdf diretos em note pages."""
    soup = get_soup(page_url)
    if not soup:
        return []
    return [urljoin(page_url, a["href"])
            for a in soup.select("a[href$='.pdf']")]

def collect_assignment_pdfs(page_url, slug):
    """
    1) coleta TODOS os links da listagem (cada link leva a uma detail page);
    2) em cada detail page, extrai o botão Download File.
    """
    soup = get_soup(page_url)
    if not soup:
        return []

    detail_links = []
    # encontra todos <a> cujos href contenha /courses/<slug>/ e não terminem em .pdf
    for a in soup.select("a[href]"):
        href = a["href"]
        full = urljoin(page_url, href)
        if f"/courses/{slug}/" in full and not full.lower().endswith(".pdf"):
            detail_links.append(full)
    # dedup
    detail_links = list(dict.fromkeys(detail_links))

    pdfs = []
    for dl in detail_links:
        dsoup = get_soup(dl)
        if not dsoup:
            continue
        pdf = find_pdf_buttons(dsoup, dl)
        if pdf:
            pdfs.append(pdf)
    return pdfs

def download_course(course_id):
    slug = extract_slug(course_id)
    base = f"https://ocw.mit.edu/courses/{slug}"
    print(f"\n=== Curso {slug} ===")

    for section, paths in SECTION_PATHS.items():
        collected = []
        for sub in paths:
            url = f"{base}/{sub}/"
            print(f"  tentando {section} em {sub}/ ...", end=" ")
            if section == "lecture_notes":
                found = collect_lecture_pdfs(url)
            else:
                found = collect_assignment_pdfs(url, slug)
            if found:
                print(f"OK ({len(found)} PDFs)")
                collected = found
                break
            else:
                print("nenhum PDF aqui.")
        if not collected:
            print(f"  seção {section} não encontrada.")
            continue

        out_dir = os.path.join("downloads", slug, section)
        os.makedirs(out_dir, exist_ok=True)
        for pdf in collected:
            fn = os.path.basename(pdf)
            dst = os.path.join(out_dir, fn)
            if os.path.exists(dst):
                continue
            try:
                r = requests.get(pdf, timeout=20)
                r.raise_for_status()
                with open(dst, "wb") as f:
                    f.write(r.content)
                print(f"    baixado {section}/{fn}")
            except RequestException:
                print(f"    falha ao baixar {pdf}")

if __name__ == "__main__":
    for cid in COURSES:
        download_course(cid)
