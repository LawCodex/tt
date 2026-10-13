#!/usr/bin/env python3
"""Fetch the revised Laws of Trinidad and Tobago from the Digital Legislative
Library (laws.gov.tt/ttdll-web), Ministry of the Attorney General and Legal Affairs.

1. Pages through /revision/list (100 per page) to enumerate revised Acts (chapters).
2. For each, fetches the detail view (?currentid=) and downloads the most recent
   consolidated version PDF (first entry of the "Versions" list).
3. Downloads the Constitution PDF from the Constitutional Instruments page.
Raw files go to _raw/tt/.
"""
import json, os, re, subprocess, sys, time
import requests
from bs4 import BeautifulSoup

BASE = "https://laws.gov.tt"
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_raw", "tt")
DELAY = 1.0
s = requests.Session()
s.headers["User-Agent"] = UA


def get(url, **kw):
    for i in range(5):
        try:
            r = s.get(url, timeout=180, **kw)
            if r.status_code in (200, 404):
                return r
        except requests.RequestException as e:
            print("  retry", url, e, file=sys.stderr)
        time.sleep(5 * (i + 1))
    raise RuntimeError("failed " + url)


def pdf_ok(path, expected_len=None):
    if not os.path.exists(path):
        return False
    size = os.path.getsize(path)
    if expected_len and size != expected_len:
        return False
    with open(path, "rb") as f:
        head = f.read(5)
        f.seek(max(0, size - 2048))
        tail = f.read()
    if head != b"%PDF-" or b"%%EOF" not in tail:
        return False
    return subprocess.run(["pdfinfo", path], capture_output=True).returncode == 0


def download(url, path):
    if pdf_ok(path):
        return True
    r = get(url)
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        return False
    cl = r.headers.get("content-length")
    if cl and int(cl) != len(r.content):
        return False
    open(path, "wb").write(r.content)
    time.sleep(DELAY)
    return pdf_ok(path)


def enumerate_items():
    items, seen, off = [], set(), 0
    while True:
        soup = BeautifulSoup(get(f"{BASE}/ttdll-web/revision/list", params={"offset": off, "max": 100}).text, "lxml")
        new = 0
        for a in soup.select("li.list-group-item a[href*=currentid]"):
            m = re.search(r"[?&]q=(&|&amp;)?currentid=(\d+)", a["href"]) or re.search(r"q=&currentid=(\d+)", a["href"])
            if "q=&" not in a["href"].replace("&amp;", "&"):
                continue  # "frequently visited" shortcuts carry a search term
            cid = re.search(r"currentid=(\d+)", a["href"]).group(1)
            if cid in seen:
                continue
            seen.add(cid)
            new += 1
            st = a.find("strong")
            sm = [x.get_text(" ", strip=True) for x in a.find_all("small")]
            items.append({"currentid": cid, "title": st.get_text(" ", strip=True) if st else "",
                          "chapter_label": " ".join(x for x in sm if x)})
        print("offset", off, "new", new, flush=True)
        if new < 100:  # last page (offsets past the end return HTTP 500)
            break
        off += 100
        time.sleep(DELAY)
    return items


def detail(cid):
    html = get(f"{BASE}/ttdll-web/revision/list", params={"offset": 0, "max": 1, "q": "", "currentid": cid}).text
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n")
    meta = {}
    for key in ["Year", "Act Number", "Commencement Date", "Classification"]:
        m = re.search(r"\n\s*" + key + r"\s*-\s*([^\n]*)", text)
        if m:
            meta[key] = m.group(1).strip()
    # versions: download links in order; label text near each
    vers = []
    for a in soup.find_all("a", href=re.compile(r"/revision/download/\d+")):
        href = a["href"]
        if vers and vers[-1]["href"] == href:
            continue
        lab = a.get_text(" ", strip=True)
        vers.append({"href": href, "label": re.sub(r"\s+", " ", lab)})
    meta["versions"] = vers
    # long title: first paragraph after heading
    m = re.search(r"\n\s*(An Act[^\n]*)", text)
    if m:
        meta["long_title"] = m.group(1).strip()
    h = soup.find(string=re.compile(r"Chap\.\s*\d+:\d+"))
    return meta


def main():
    os.makedirs(os.path.join(RAW, "pdf"), exist_ok=True)
    os.makedirs(os.path.join(RAW, "meta"), exist_ok=True)
    lp = os.path.join(RAW, "list.json")
    if os.path.exists(lp):
        items = json.load(open(lp))
    else:
        items = enumerate_items()
        json.dump(items, open(lp, "w"), indent=1)
    print(len(items), "items", flush=True)
    # constitution
    for name in ["Constitution.pdf"]:
        ok = download(f"{BASE}/pdf/{name}", os.path.join(RAW, "constitution.pdf"))
        print("constitution", ok)
    for n, it in enumerate(items):
        cid = it["currentid"]
        mpath = os.path.join(RAW, "meta", cid + ".json")
        ppath = os.path.join(RAW, "pdf", cid + ".pdf")
        if os.path.exists(mpath):
            meta = json.load(open(mpath))
        else:
            meta = dict(it)
            meta.update(detail(cid))
            time.sleep(DELAY)
        if meta["versions"] and not meta.get("pdf_ok"):
            meta["pdf_ok"] = download(BASE + meta["versions"][0]["href"], ppath)
        json.dump(meta, open(mpath, "w"), indent=1)
        print(n, cid, it["title"], meta.get("pdf_ok"), flush=True)


if __name__ == "__main__":
    main()
