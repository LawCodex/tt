# Trinidad and Tobago — Laws of Trinidad and Tobago (LawCodex)

Consolidated (revised) Acts of **Trinidad and Tobago** as plain Markdown, converted from the PDFs of the
**Digital Legislative Library** of the Ministry of the Attorney General and Legal Affairs
(Law Revision Commission) at <https://laws.gov.tt/ttdll-web/revision/list>.

Retrieved: 2026-10-13.

## Contents

| Directory | What | Files |
|---|---|---|
| `constitution/` | Constitution of the Republic of Trinidad and Tobago Act, Chap. 1:01 (Constitution in the Schedule) | 1 |
| `chapters/` | All other revised Acts (chapters) listed under "Revised Acts" | 532 |

Total: **533 chapters** — every entry of the library's "Revised Acts" list. For each chapter the most
recent consolidated version offered by the library was used: **updated to 31 December 2016** (490
chapters) or **31 December 2015** (43 chapters), as stated on each PDF and recorded in `last_amended`.

File names: `cap-PP-CC-<slug>.md` from the chapter number (e.g. Chap. 8:08 → `cap-08-08-absconding-debtors.md`).
Front matter: `title`, `identifier` (Chap. number), `original_act`, `date` (commencement as listed),
`last_amended` (consolidation date), `long_title`, `classification`, `source` (library entry),
`source_pdf`, `pages`, `retrieved`.

The chapter PDFs contain the Act followed by its subsidiary legislation, so the Markdown files include
the subsidiary legislation consolidated under each chapter. Marginal notes are rendered as *italic*
lines before the paragraph they sit beside; section numbers in **bold**. Running headers/footers
("LAWS OF TRINIDAD AND TOBAGO", "UNOFFICIAL VERSION", "UPDATED TO …", "L.R.O.") are removed.

## Not covered / caveats

- The PDFs are marked **"UNOFFICIAL VERSION"** by the publisher, and the library's consolidation stops at
  31 December 2016: Acts and amendments after that date are not reflected.
- Repealed, omitted and unproclaimed Acts, Federal laws, and the separate Legal Notices list are not
  included.
- Historical constitutions (1962, 1976) and constitutional appendices on the "Constitutions" page are not
  included (only the current Constitution Act, Chap. 1:01).
- Tables/forms are flattened to text; check the PDF for complex tables.

## Source and licence

Official legislative texts of the Republic of Trinidad and Tobago published by the Ministry of the
Attorney General and Legal Affairs for public access; no robots.txt restrictions or terms of use
prohibiting reuse were found. This repository is an unofficial conversion — refer to the official
publication for authoritative text.

## Regenerate

```
python3 scripts/tt_fetch.py     # pages /revision/list (100/page), fetches each entry and its newest PDF -> ../_raw/tt
python3 scripts/tt_convert.py   # pdftotext -bbox-layout -> Markdown (scripts/tt_pdfmd.py)
```

Requires poppler (`pdftotext`, `pdfinfo`) and `scripts/requirements.txt`. PDFs are verified (header,
`%%EOF`, `pdfinfo`, Content-Length) before conversion.
