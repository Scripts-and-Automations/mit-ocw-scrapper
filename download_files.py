#!/usr/bin/env python3
import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, TooManyRedirects

#COURSES = [
#    "18-175-theory-of-probability-spring-2014",
#    "18-712-introduction-to-representation-theory-fall-2010",
#    "18-745-lie-groups-and-lie-algebras-i-fall-2020",
#    "18-755-introduction-to-lie-groups-fall-2004",
#    "18-757-representations-of-lie-groups-fall-2023",
#    "18-769-topics-in-lie-theory-tensor-categories-spring-2009"
#]

COURSES = [
    "3-012-fundamentals-of-materials-science-fall-2005",
    "5-61-physical-chemistry-fall-2007",
    "5-61-physical-chemistry-fall-2017",
    "5-62-physical-chemistry-ii-spring-2008",
    "12-842-climate-physics-and-chemistry-fall-2008",
    "16-225-computational-mechanics-of-materials-fall-2003"
]
# Agora o dicionário tem tanto lecture_notes quanto assignments
SECTION_PATHS = {
    "assignments": [
        "pages/assignments",
        "pages/problem-sets",
        "resources/problem-sets",
        "pages/exams"
    ],
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

def find_pdfs_in_page(url):
    """
    Retorna lista de URLs de PDF encontradas em 'url', seja:
    1) <a href="...*.pdf">
    2) links de texto 'PDF' (nas pages/assignments), seguindo-os e
       extraindo o botão 'Download File' que realmente aponta para .pdf
    """
    soup = get_soup(url)
    if not soup:
        return []

    pdf_urls = []

    # 1) procura todos os anchors que já apontam para .pdf
    for a in soup.select("a[href$='.pdf']"):
        href = a["href"].strip()
        pdf_urls.append(urljoin(url, href))

    if pdf_urls:
        return pdf_urls

    # 2) se não achar nenhum .pdf direto, tenta links cujo texto contenha "PDF"
    for a in soup.find_all("a", string=lambda t: t and "pdf" in t.lower()):
        href = a.get("href")
        if not href:
            continue
        page2 = urljoin(url, href)
        sub = get_soup(page2)
        if not sub:
            continue
        # neste subsite deve haver o botão real <a href="...pdf">Download File</a>
        for b in sub.select("a[href$='.pdf']"):
            pdf_urls.append(urljoin(page2, b["href"]))

    return pdf_urls

def download_file(pdf_url, dest_folder):
    fn = os.path.basename(pdf_url)
    dst = os.path.join(dest_folder, fn)
    if os.path.exists(dst):
        print(f"  - {fn} já existe, pulando.")
        return

    def fetch(u):
        r = requests.get(u, timeout=20)
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
    print(f"\n=== Processando curso {slug} ===")

    for section, paths in SECTION_PATHS.items():
        pdfs = []
        for p in paths:
            url = f"{base}/{p}/"
            print(f"  tentando seção “{section}” em {p}/ ...", end=" ")
            found = find_pdfs_in_page(url)
            if found:
                print(f"OK ({len(found)} PDFs)")
                pdfs = found
                break
            else:
                print("nenhum PDF aqui.")
        if not pdfs:
            print(f"  [!] nenhuma PDF para seção “{section}”")
            continue

        out_dir = os.path.join("downloads", slug, section)
        os.makedirs(out_dir, exist_ok=True)
        for pdf in pdfs:
            download_file(pdf, out_dir)

if __name__ == "__main__":
    for c in COURSES:
        download_course(c)
