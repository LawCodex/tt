#!/usr/bin/env python3
"""Convert downloaded Laws of Trinidad and Tobago PDFs (_raw/tt) to Markdown."""
import datetime, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tt_pdfmd as pm

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RAW = os.path.abspath(os.path.join(ROOT, "..", "_raw", "tt"))
BASE = "https://laws.gov.tt"
JUNK = [r"^UNOFFICIAL VERSION$", r"^UPDATED TO \d+\w* \w+ \d{4}$", r"^L\.R\.O\.?(\s+\d+/\d+)?$",
        r"^LAWS OF TRINIDAD AND TOBAGO$", r"^MINISTRY OF THE ATTORNEY GENERAL AND LEGAL AFFAIRS",
        r"www\.legalaffairs\.gov\.tt"]


def slugify(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80].strip("-")


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def front(d):
    out = ["---"]
    for k, v in d.items():
        if v is None or v == "":
            continue
        out.append(f"{k}: {v if isinstance(v, (int, float)) or k in ('date', 'last_amended', 'retrieved', 'type', 'jurisdiction', 'language', 'status') else q(v)}")
    out.append("---")
    return "\n".join(out) + "\n\n"


def pdate(s):
    for fmt in ("%a, %d %b %Y", "%d %b %Y"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date().isoformat()
        except Exception:
            pass
    return None


def main():
    retrieved = datetime.date.today().isoformat()
    for d in ("chapters", "constitution"):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    report = {"converted": [], "gaps": []}
    for mf in sorted(os.listdir(os.path.join(RAW, "meta"))):
        m = json.load(open(os.path.join(RAW, "meta", mf)))
        cid = m["currentid"]
        title = m["title"]
        src = f"{BASE}/ttdll-web/revision/list?offset=0&q=&currentid={cid}"
        pdf = os.path.join(RAW, "pdf", cid + ".pdf")
        if not m.get("pdf_ok") or not os.path.exists(pdf):
            report["gaps"].append({"title": title, "reason": "no downloadable PDF", "source": src})
            continue
        body, st = pm.pdf_to_md(pdf, extra_header_patterns=JUNK, anywhere_patterns=JUNK, tmpdir=RAW)
        if st["chars_per_page"] < 150:
            report["gaps"].append({"title": title, "reason": "PDF has no text layer (scan)", "source": src})
            continue
        cm = re.search(r"(\d+)[:.](\d+)", m.get("chapter_label", ""))
        cap = f"{int(cm.group(1))}:{cm.group(2)}" if cm else None
        is_const = cap == "1:01"
        full_title = title if title.lower().endswith(("act", "ordinance")) else title + " Act"
        fname = (f"cap-{int(cm.group(1)):02d}-{cm.group(2)}-" if cm else "") + slugify(title) + ".md"
        rel = ("constitution/" if is_const else "chapters/") + fname
        num = f"Act {m['Act Number']} of {m['Year']}" if m.get("Act Number") and m.get("Year") else None
        p1 = subprocess.run(["pdftotext", "-l", "2", pdf, "-"], capture_output=True, text=True).stdout
        vlabel = re.search(r"UPDATED TO (\d+)\w* (\w+) (\d{4})", p1, re.I)
        last = None
        if vlabel:
            try:
                last = datetime.datetime.strptime(f"{vlabel.group(1)} {vlabel.group(2).title()} {vlabel.group(3)}", "%d %B %Y").date().isoformat()
            except Exception:
                pass
        fm = {
            "title": full_title,
            "identifier": f"Chap. {cap}" if cap else None,
            "original_act": num,
            "type": "constitution" if is_const else "act",
            "jurisdiction": "tt", "language": "en",
            "date": pdate(m.get("Commencement Date", "")),
            "last_amended": last,
            "status": "in_force",
            "long_title": m.get("long_title"),
            "classification": m.get("Classification"),
            "note": m.get("chapter_label") if cm and "(" in m.get("chapter_label", "") else None,
            "source": src,
            "source_pdf": BASE + m["versions"][0]["href"],
            "pages": st["pages"],
            "retrieved": retrieved,
        }
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(front(fm) + f"# {full_title}\n\n" + body)
        report["converted"].append({"title": title, "file": rel, "quality": st["quality"]})
        print(rel, st["quality"], flush=True)
    json.dump(report, open(os.path.join(RAW, "convert_report.json"), "w"), indent=1)
    print(len(report["converted"]), "converted;", len(report["gaps"]), "gaps")


if __name__ == "__main__":
    main()
