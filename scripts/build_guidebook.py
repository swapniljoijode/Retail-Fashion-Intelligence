"""
Generate the Theory Companion v2 guidebook as a Word (.docx) document.

Usage (from project root):
    uv run python scripts/build_guidebook.py

Output:
    docs/Theory_Companion_v2_Guidebook.docx

The document is a plain-English, replicate-from-scratch guide to the
Fashion Retail Intelligence Platform: tools, phase-by-phase build,
manual-replication notes, non-negotiable theory, and an interview Q&A.
Diagrams are rendered as monospace box-and-arrow art so they display
without any external rendering engine.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD = RGBColor(0xC7, 0x8A, 0x1E)
NAVY = RGBColor(0x1F, 0x29, 0x37)
SLATE = RGBColor(0x47, 0x55, 0x69)
CODE_BG = "F4F4F0"
HEADER_BG = "1F2937"
ROW_BG = "F7F7F9"


# ── Low-level helpers ─────────────────────────────────────────────────────────
def _shade(cell, hex_color: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def _no_space(paragraph) -> None:
    paragraph.paragraph_format.space_before = Pt(0)
    paragraph.paragraph_format.space_after = Pt(0)


def title_page(doc: Document) -> None:
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Fashion Retail Intelligence Platform")
    r.bold = True
    r.font.size = Pt(26)
    r.font.color.rgb = NAVY

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Theory Companion v2 — The Complete Guidebook")
    r.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = GOLD

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(
        "A start-to-finish guide that anyone — technical or not — can follow:\n"
        "what was built, why each tool was chosen, how to rebuild it by hand,\n"
        "and the theory that matters in interviews."
    )
    r.italic = True
    r.font.size = Pt(11)
    r.font.color.rgb = SLATE

    for _ in range(8):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Swapnil Joijode  ·  Data Engineering Portfolio")
    r.font.size = Pt(10)
    r.font.color.rgb = SLATE
    doc.add_page_break()


def h1(doc: Document, text: str) -> None:
    doc.add_page_break()
    p = doc.add_heading(text, level=1)
    for run in p.runs:
        run.font.color.rgb = NAVY


def h2(doc: Document, text: str) -> None:
    p = doc.add_heading(text, level=2)
    for run in p.runs:
        run.font.color.rgb = NAVY


def marker(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = GOLD


def body(doc: Document, text: str) -> None:
    """Add a paragraph; **bold** spans are honoured."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    parts = text.split("**")
    for i, part in enumerate(parts):
        run = p.add_run(part)
        run.font.size = Pt(11)
        if i % 2 == 1:
            run.bold = True


def bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        parts = item.split("**")
        for i, part in enumerate(parts):
            run = p.add_run(part)
            run.font.size = Pt(11)
            if i % 2 == 1:
                run.bold = True


def code_box(doc: Document, text: str) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.autofit = True
    cell = table.cell(0, 0)
    _shade(cell, CODE_BG)
    cell.paragraphs[0].text = ""
    for idx, line in enumerate(text.split("\n")):
        para = cell.paragraphs[0] if idx == 0 else cell.add_paragraph()
        _no_space(para)
        run = para.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run.font.color.rgb = NAVY
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def data_table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, htext in enumerate(headers):
        _shade(hdr[i], HEADER_BG)
        para = hdr[i].paragraphs[0]
        para.text = ""
        run = para.add_run(htext)
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for ci, val in enumerate(row):
            if ri % 2 == 1:
                _shade(cells[ci], ROW_BG)
            para = cells[ci].paragraphs[0]
            para.text = ""
            parts = val.split("**")
            for i, part in enumerate(parts):
                run = para.add_run(part)
                run.font.size = Pt(9.5)
                if i % 2 == 1:
                    run.bold = True
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def qa(doc: Document, q: str, a: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run("Q:  " + q)
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = NAVY
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("A:  " + a)
    r.font.size = Pt(11)
    r.font.color.rgb = SLATE


# ── Build ─────────────────────────────────────────────────────────────────────
def build() -> Path:
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    title_page(doc)

    # ── How to read ────────────────────────────────────────────────────────────
    h1(doc, "How to read this guide")
    body(
        doc,
        "This document has five parts. Read them in order the first time; jump "
        "around afterwards. Throughout, the bold label **By Hand** marks where "
        "we explain how to do manually what the code does automatically.",
    )
    data_table(
        doc,
        ["Part", "What it gives you"],
        [
            [
                "0 — The Big Picture",
                "A plain-English tour of the whole system using a real-world analogy",
            ],
            ["1 — The Toolbox", "Every tool, explained simply, and why it was picked"],
            [
                "2 — The Build, Phase by Phase",
                "For each phase: the goal, what the automation does, how to do it by hand, and the non-negotiable theory",
            ],
            [
                "3 — The 'Why' Behind Decisions",
                "Corporate reasoning: why Docker, why dbt, why not do it manually",
            ],
            [
                "4 — The Interview",
                "Logical, technical, theoretical, and practical questions with model answers",
            ],
        ],
    )

    # ════════════════════════════ PART 0 ════════════════════════════
    h1(doc, "Part 0 — The Big Picture")

    h2(doc, "The factory analogy")
    body(
        doc,
        "Imagine a factory that turns raw cotton into finished, packaged clothing "
        "on store shelves. Our data platform works exactly the same way, but with "
        "*information* instead of cotton.",
    )
    code_box(
        doc,
        "Raw data files  -->  Bronze        -->  Silver          -->  Gold          -->  Dashboard\n"
        "(raw cotton)         (goods-in)         (cleaning floor)      (assembly)         (shop window)",
    )
    bullets(
        doc,
        [
            "**Raw cotton** is messy and full of impurities — like raw data with typos, missing values, and wrong formats.",
            "The **goods-in warehouse (Bronze)** accepts everything exactly as it arrives and never throws anything away. It is the permanent record of 'what we received.'",
            "The **cleaning floor (Silver)** removes impurities — standardises, de-duplicates, fixes types.",
            "**Assembly (Gold)** turns clean materials into finished products a business person can use — answers like 'which region is under-stocked?'",
            "The **shop window (Dashboard)** displays the finished goods to the business user.",
        ],
    )
    body(
        doc,
        "Every other tool exists to **move material between these stations, "
        "schedule the work, check quality, and keep the lights on for free.**",
    )

    h2(doc, "The one-sentence summary")
    body(
        doc,
        "Synthetic shopping data is generated in Python, stored cheaply in the "
        "cloud, loaded untouched into a warehouse, cleaned and reshaped by dbt into "
        "business-ready tables, tested at every step, scheduled to run on its own, "
        "packaged so it runs identically on any computer, and finally shown on a "
        "public website — all at zero ongoing cost.",
    )

    h2(doc, "The full system, one diagram")
    code_box(
        doc,
        "[1. GENERATE]   Python + Faker + NumPy   (fake but realistic shop data)\n"
        "                       |\n"
        "                       v\n"
        "[2. STORE]      Cloudflare R2   (cheap cloud file storage)\n"
        "                       |\n"
        "            +----------+-----------+\n"
        "            v                      v\n"
        "[3. WAREHOUSE]  Snowflake (trial)    DuckDB (free, local)\n"
        "            |                      |\n"
        "            +----------+-----------+\n"
        "                       v\n"
        "[4. TRANSFORM]  dbt   (Bronze -> Silver -> Gold  +  190 tests)\n"
        "                       |\n"
        "                       v\n"
        "[5. SERVE]      JSON snapshot  -->  Next.js dashboard on Vercel\n"
        "\n"
        "Runs everything:  Airflow (local demo)   |   GitHub Actions (production proof)\n"
        "Quality & docs:   Elementary (health)    |   MkDocs (docs)   |   Tracker (progress)",
    )

    # ════════════════════════════ PART 1 ════════════════════════════
    h1(doc, "Part 1 — The Toolbox")
    body(
        doc,
        "Before walking through the build, here is every tool in plain language — "
        "like meeting the staff before watching them work.",
    )

    h2(doc, "The languages and runners")
    data_table(
        doc,
        ["Tool", "What it is, in one breath", "Why we used it"],
        [
            [
                "Python",
                "The general-purpose language that glues everything together.",
                "Industry standard for data work; huge library ecosystem.",
            ],
            [
                "uv",
                "Installs Python's add-on libraries fast and records exact versions.",
                "Guarantees every computer runs the identical set of libraries.",
            ],
            [
                "SQL",
                "The language for asking questions of tables of data.",
                "The native language of every database and warehouse.",
            ],
            [
                "Bash / PowerShell",
                "The command line — typing instructions instead of clicking.",
                "Lets us automate steps so no human has to click through menus.",
            ],
            [
                "Make",
                "A to-do list runner: 'make seed' runs a saved recipe.",
                "One short word replaces a long, error-prone command.",
            ],
        ],
    )

    h2(doc, "The data tools")
    data_table(
        doc,
        ["Tool", "Plain English", "Why chosen"],
        [
            [
                "Faker",
                "Invents realistic fake names, addresses, dates.",
                "We have no real customer data; we need believable substitutes.",
            ],
            [
                "NumPy / pandas",
                "Spreadsheet-like number-crunching engines for Python.",
                "Fast at generating and shaping millions of rows.",
            ],
            [
                "pyarrow / Parquet",
                "A file format that stores tables compressed, column-by-column.",
                "10x smaller and faster to query than CSV.",
            ],
            [
                "DuckDB",
                "A complete analytics database in a single file. Free forever.",
                "Runs the entire warehouse for free, with no servers.",
            ],
            [
                "Snowflake",
                "A powerful cloud warehouse used by large firms. 30-day trial.",
                "Demonstrates the enterprise vocabulary interviewers ask about.",
            ],
            [
                "dbt",
                "Organises SQL transforms, runs them in order, tests results.",
                "Turns loose SQL scripts into a tested, documented system.",
            ],
        ],
    )

    h2(doc, "Storage, scheduling, and packaging")
    data_table(
        doc,
        ["Tool", "Plain English", "Why chosen"],
        [
            [
                "Cloudflare R2",
                "A giant shared cloud folder for files.",
                "Free forever, and free to download from (most clouds charge).",
            ],
            [
                "Airflow",
                "A scheduler that runs steps in order, retries failures, shows a dashboard.",
                "The industry-standard way to schedule data pipelines.",
            ],
            [
                "astronomer-cosmos",
                "Makes Airflow show each dbt step as its own box.",
                "Visibility: see exactly which transformation failed.",
            ],
            [
                "Docker",
                "Packages an app with its whole environment into a sealed box.",
                "Eliminates 'it worked on my computer but not the server.'",
            ],
            [
                "GitHub Actions",
                "Robots that test and run code on every change.",
                "Free automation; catches mistakes before they spread.",
            ],
        ],
    )

    h2(doc, "Quality and presentation")
    data_table(
        doc,
        ["Tool", "Plain English", "Why chosen"],
        [
            [
                "ruff / black / sqlfluff",
                "Automatic spell-checkers and formatters for code.",
                "Consistent, professional code with zero manual effort.",
            ],
            [
                "pytest",
                "Runs hundreds of small 'does this still work?' checks.",
                "Confidence that a change didn't secretly break something.",
            ],
            [
                "Elementary",
                "A health monitor for data — flags sudden row-count drops.",
                "Catches silent data problems normal tests miss.",
            ],
            [
                "Next.js + Recharts",
                "A website framework + a charting library.",
                "Builds the interactive dashboard the business sees.",
            ],
            [
                "Vercel",
                "Hosts websites free and updates them automatically.",
                "Free public hosting for the dashboard.",
            ],
            [
                "MkDocs",
                "Turns plain-text documents into a searchable website.",
                "Free, professional documentation site.",
            ],
            [
                "Git / GitHub",
                "A time machine + collaboration hub for code.",
                "The universal system of record for software.",
            ],
        ],
    )

    # ════════════════════════════ PART 2 ════════════════════════════
    h1(doc, "Part 2 — The Build, Phase by Phase")
    body(
        doc,
        "Each phase follows the same shape: **Goal**, **What the automation does**, "
        "**By Hand**, **Theory worth noting**, and a **Visual**.",
    )

    # ---- Phase 0 ----
    h2(doc, "Phase 0 — Foundation")
    marker(doc, "Goal")
    body(
        doc,
        "Set up a clean, professional workshop before building anything — so quality is automatic and every contributor's setup is identical.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "pyproject.toml",
                "Lists every Python library needed, with version rules. The single source of truth for dependencies.",
            ],
            [
                "uv.lock",
                "Records the exact version of every library. Locks the environment so all machines match.",
            ],
            [
                ".pre-commit-config.yaml",
                "Runs spell-checkers (ruff, black, sqlfluff) automatically before every save. Bad code can't get in.",
            ],
            [
                "Makefile",
                "A recipe book: 'make setup' builds the environment, 'make test' runs checks.",
            ],
            [
                ".env / .env.example",
                "Where secret passwords live (.env, never shared) and a safe template (.env.example, shared).",
            ],
            [
                "docs/charter.md",
                "The written rules: naming conventions, scope, out-of-scope.",
            ],
        ],
    )
    code_box(doc, "make setup     # = uv sync --all-extras  +  pre-commit install")
    marker(doc, "By Hand")
    body(
        doc,
        "Without these tools a new teammate would install each library one by one (and get different versions), remember to run a formatter before every commit (and forget), and type long commands from memory. The foundation replaces human discipline with automation.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Why a lockfile is non-negotiable.** Without it, two people installing 'the latest pandas' a week apart get different versions and different bugs. The lockfile freezes versions so every machine is identical — the #1 cause of 'works on my machine' bugs.",
            "**Shift-left quality.** A typo caught in your editor costs 5 seconds; the same typo in production costs hours. Pre-commit hooks catch issues as early ('left') as possible.",
            "**12-Factor config in the environment.** Passwords and settings live in environment variables, never hard-coded. The same code runs everywhere; only the environment changes.",
            "**Monorepo.** Everything lives in one Git repository, so a change touching three areas is one reviewable commit, not three coordinated ones.",
        ],
    )
    marker(doc, "Visual")
    code_box(
        doc,
        "git commit\n"
        "    |\n"
        "    v\n"
        "+------------------------------+\n"
        "|  Pre-commit hooks            |\n"
        "|   - ruff      (lint Python)  |\n"
        "|   - black     (format Python)|\n"
        "|   - sqlfluff  (lint SQL)     |\n"
        "+------------------------------+\n"
        "    |\n"
        "    v\n"
        " All pass? --- no ---> Commit BLOCKED (fix and retry)\n"
        "    |\n"
        "   yes\n"
        "    v\n"
        " Commit SAVED",
    )

    # ---- Phase 1 ----
    h2(doc, "Phase 1 — The Blueprint (Dimensional Model)")
    marker(doc, "Goal")
    body(
        doc,
        "Design the shape of the data before generating a single row — like drawing architectural plans before laying bricks. Decide what we measure and how every number is calculated.",
    )
    marker(doc, "What the automation does")
    body(
        doc,
        "This phase is design, not code. The deliverables are documents: **dimensional_model.md** (the tables and how they relate — the star schema) and **metric_dictionary.md** (every business number with one exact formula).",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "This IS the manual, human part — it needs business judgement. You sit with stakeholders and agree: 'What does a sale mean? When is a customer new? How do we count a return?'",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Star schema.** A central fact table (events — sales, returns) surrounded by dimension tables (context — products, stores, dates). Facts hold numbers; dimensions hold the descriptions you filter and group by.",
            "**Fact vs Dimension — the simplest test.** If you'd SUM it, it's a fact (revenue, units). If you'd GROUP BY it, it's a dimension (region, category).",
            "**Grain.** The most important decision: 'what does one row mean?' One row per order line? Per day? Getting this wrong corrupts every number built on top.",
            "**Slowly Changing Dimension (SCD Type 2).** A product's price changes over time. Type 2 keeps a new row per version with 'valid from/to' dates, so a sale is always matched to the price on the day it happened.",
            "**Conformed dimensions.** 'Date' and 'Product' mean the same thing across every report — one shared definition reused everywhere, so Sales and Marketing never disagree.",
        ],
    )
    marker(doc, "Visual — the star schema")
    code_box(
        doc,
        "        dim_date      dim_product     dim_store\n"
        "             \\            |             /\n"
        "              \\           |            /\n"
        "               +---->  fact_sales  <--+\n"
        "              /           |            \\\n"
        "             /            |             \\\n"
        "        dim_customer  dim_channel   dim_promotion\n"
        "\n"
        "  facts = numbers you SUM    |    dimensions = things you GROUP BY",
    )

    # ---- Phase 2 ----
    h2(doc, "Phase 2 — Making the Raw Material (Synthetic Data)")
    marker(doc, "Goal")
    body(
        doc,
        "Generate realistic, intentionally imperfect shopping data — because real data is never clean, and the cleaning layer needs something real to clean.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "taxonomy.py",
                "Hand-written 'fashion knowledge': categories, price ranges, seasonal patterns.",
            ],
            [
                "generators/dimensions.py",
                "Builds the six dimension tables (products, stores, customers...).",
            ],
            [
                "generators/facts.py",
                "Builds the five fact tables with realistic behaviour: weekend spikes, seasonal curves.",
            ],
            [
                "dirtiness.py",
                "Deliberately adds flaws: missing values, typos, numbers stored as text, duplicate rows.",
            ],
            ["writer.py", "Saves everything as compressed Parquet files."],
            ["main.py", "The conductor: dimensions -> facts -> dirtiness -> write."],
        ],
    )
    code_box(doc, "python -m data_generation.main --volume small --seed 42")
    body(
        doc,
        "The flaws are precisely specified — e.g. 5% of customer regions blanked, 8% of product categories given inconsistent capitalisation, 3% of sales quantities stored as text instead of numbers.",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "You'd type thousands of rows of fake sales into a spreadsheet — impossible at scale, and impossible to make reproducible. The generator does it in seconds and, thanks to the seed, produces the exact same data every time.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Reproducible randomness (the 'seed').** Computers make random numbers from a starting value (a seed). Same seed -> same sequence -> identical data every run. This is why tests can check for exact values. Seed 42 is used throughout.",
            "**Why intentional dirtiness?** It lets you say precisely: 'My silver layer fixes 5% null regions, fixes inconsistent casing, and recovers quantities stored as text.' Documented cleaning is senior-level; vague cleaning is not.",
            "**Parquet vs CSV.** CSV is plain text — simple but bulky and slow. Parquet stores data by column, compressed, and reads only the columns a query needs. Dramatically faster for analytics.",
            "**Referential integrity.** Every sale must reference a product that exists. The generator builds dimensions first, then draws fact keys from them — guaranteeing no orphan sales.",
        ],
    )
    marker(doc, "Visual — generation order")
    code_box(
        doc,
        "taxonomy.py         generate           generate facts        inject            write\n"
        "(fashion      -->   6 dimensions  -->  (using dimension -->  controlled  -->   Parquet\n"
        " knowledge)                             keys)                 flaws             files",
    )

    # ---- Phase 3 ----
    h2(doc, "Phase 3 — Goods-In (Raw Storage & Bronze)")
    marker(doc, "Goal")
    body(
        doc,
        "Move the raw files to the cloud, then load them — completely untouched — into the warehouse's 'goods-in' area (Bronze). Bronze is the permanent, never-edited record of what arrived.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "upload_r2.py",
                "Uploads the Parquet files to Cloudflare R2 using boto3 (the standard cloud-storage library).",
            ],
            [
                "bronze_load.py",
                "Loads Parquet into DuckDB's bronze schema. Adds 'where did this come from?' columns: source file + load time.",
            ],
            [
                "snowflake_bronze.sql",
                "The Snowflake equivalent: creates an external stage (a pointer to R2), then COPY INTO bronze tables.",
            ],
            [
                "run_snowflake_bronze.py",
                "Runs the Snowflake SQL automatically using key-pair login (no password prompts).",
            ],
        ],
    )
    marker(doc, "By Hand")
    body(
        doc,
        "In R2 you'd log into Cloudflare and drag-drop files into a bucket. In Snowflake you'd open the web console and type SQL — CREATE STAGE, CREATE TABLE, COPY INTO — then run SELECT COUNT(*) on each table to confirm the row counts. The scripts do exactly this, unattended and repeatably. (We actually hit Snowflake's web-console bug on long scripts and switched to running the SQL via Python — a real example of why automation beats clicking.)",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Why Bronze is immutable.** It's your insurance policy. If the cleaning logic has a bug, you fix the logic and replay from Bronze. If you'd overwritten Bronze, the original truth is gone forever.",
            "**Schema-on-read vs schema-on-write.** Traditional databases reject bad data at the door (schema-on-write). Bronze accepts everything as-is and worries about types later (schema-on-read) — which is why the text-corrupted quantity column is stored as text rather than dropped.",
            "**External stage + COPY INTO (Snowflake).** A stage is a pointer to cloud files, not a copy. COPY INTO bulk-loads in parallel and remembers which files it already loaded, so re-runs don't duplicate.",
            "**Lineage columns.** Every Bronze row records which file it came from and when it loaded. When something looks wrong months later, you can trace it to its source.",
            "**Object vs block storage.** R2 is object storage — perfect for whole files read start-to-finish (like Parquet) and far cheaper than the block storage databases use for fast random edits.",
        ],
    )
    marker(doc, "Visual — two warehouses, one source")
    code_box(
        doc,
        "                Parquet files\n"
        "                /            \\\n"
        "               v              v\n"
        "        Cloudflare R2     DuckDB bronze  (free, always on)\n"
        "               |\n"
        "      external stage / COPY INTO\n"
        "               v\n"
        "        Snowflake bronze  (trial)",
    )

    # ---- Phase 4 ----
    h2(doc, "Phase 4 — The Cleaning & Assembly Floor (dbt)")
    marker(doc, "Goal")
    body(
        doc,
        "Transform raw Bronze into clean Silver, then business-ready Gold — with tests and documentation at every step. This is the heart of the project.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["Layer", "Folder", "What it does"],
        [
            [
                "Silver (staging)",
                "models/staging/",
                "One cleaning view per source: fix types, standardise casing, remove duplicates.",
            ],
            [
                "Intermediate",
                "models/intermediate/",
                "Resolves SCD2 history — which product version applies to each sale.",
            ],
            [
                "Gold (marts)",
                "models/marts/",
                "The final star-schema tables the business uses.",
            ],
        ],
    )
    code_box(doc, "dbt build --target duckdb     # = run all models + run all tests")
    marker(doc, "By Hand")
    body(
        doc,
        "Without dbt you'd write loose SQL scripts and run them in the correct order yourself — clean_products, then resolve_history, then build_sales — holding the dependencies in your head. You'd hand-write COUNT(*) checks for every table and update a Word doc when a column changed. dbt automates the ordering, testing, and documentation.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Why dbt instead of plain SQL?** Plain SQL can do the casting, de-dup, and star schema. dbt adds: automatic dependency ordering (it reads ref() and builds the graph), built-in testing, generated docs with a visual lineage map, and one codebase that runs on both DuckDB and Snowflake. It turns SQL from scripts into software.",
            "**Materializations — view vs table.** A view is a saved query that re-runs each time (always fresh, no storage). A table is pre-computed and stored (fast to read, frozen until the next run). Staging = views; Gold = tables.",
            "**ref() and source().** Models reference each other with {{ ref('...') }} instead of hard-coded names. This is how dbt knows the build order and how the same code runs on different warehouses.",
            "**The four built-in tests.** unique (no duplicate keys), not_null (required fields filled), accepted_values (status is one of a known list), relationships (every foreign key exists in its dimension). Plus dbt-expectations for ranges ('price is never negative').",
            "**Contracts.** A promise that a table will always have exactly these columns and types. A change that breaks the promise fails the build, protecting everything downstream.",
            "**The SCD2 join.** A sale on 15 March matches the price valid on 15 March: match the product AND sale_date >= valid_from AND (sale_date <= valid_to OR valid_to IS NULL). Unmatched rows get a '-1 unknown' placeholder so they're never silently dropped.",
        ],
    )
    marker(doc, "Visual — the dbt flow")
    code_box(
        doc,
        "BRONZE (raw)          SILVER (staging views)      INTERMEDIATE        GOLD (mart tables)\n"
        "11 source tables -->  11 cleaning models     -->  SCD2 history   -->  6 dims + 5 facts\n"
        "                      cast, dedup, standardise    resolver                 |\n"
        "                                                                           v\n"
        "                                                             190 tests (unique, not_null,\n"
        "                                                             relationships, ranges)",
    )

    # ---- Phase 5 ----
    h2(doc, "Phase 5 — The Conductor (Airflow + Cosmos)")
    marker(doc, "Goal")
    body(
        doc,
        "Make the whole pipeline run on its own, in the right order, on a schedule — and show a dashboard of what ran, what failed, and let you retry just the broken step.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "orchestration/dags/fashion_retail_pipeline.py",
                "The 'DAG' — the recipe of steps and their order.",
            ],
            [
                "docker/airflow/docker-compose.yml",
                "Starts Airflow locally (web UI + scheduler + database).",
            ],
            [
                "docker/airflow/Dockerfile",
                "Builds the Airflow image with dbt and our code inside.",
            ],
        ],
    )
    code_box(
        doc,
        "generate_data -> load_bronze -> install_dbt_deps -> [dbt via Cosmos]\n   -> export_snapshot -> check_credentials -> upload_r2",
    )
    body(
        doc,
        "Cosmos is the clever part: instead of one big 'run dbt' box, it shows each model and test as its own box. If one model fails, you see precisely which one and retry just that.",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "You'd run each command yourself, in order, waiting for each. If step 3 failed at 2am, nobody would know until morning, and you'd restart from scratch. Airflow runs it unattended, retries failures automatically, and records everything.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**What a DAG is.** 'Directed Acyclic Graph' — a flowchart of steps that only flows forward and never loops. It captures dependencies: step B can't start until step A succeeds.",
            "**Why Airflow beats cron.** Cron just fires a command and forgets. Airflow tracks success/failure per step, retries intelligently, shows logs per step, supports backfills, and enforces dependencies.",
            "**Idempotency — the non-negotiable rule.** Every step must produce the same result whether it runs once or five times. The bronze load uses --reset so retries never create duplicates. Without idempotency, a retry after a half-failure corrupts data.",
            "**Why Cosmos beats one big dbt task.** One box that says 'dbt failed' tells you nothing. Fifty boxes where one is red tells you exactly what broke and lets you retry only that.",
            "**The reality check.** Always-on Airflow costs money to host. So Airflow here is the local demonstration, and GitHub Actions is the free production proof. Knowing this trade-off is itself an interview point.",
        ],
    )
    marker(doc, "Visual — the pipeline Airflow runs")
    code_box(
        doc,
        "generate_data -> load_bronze -> install_dbt_deps -> [dbt: each model a box]\n"
        "    -> export_snapshot -> credentials? --yes--> upload_r2\n"
        "                                       --no---> skip gracefully",
    )

    # ---- Phase 6 ----
    h2(doc, "Phase 6 — The Sealed Box (Docker & Testing)")
    marker(doc, "Goal")
    body(
        doc,
        "Package the whole application — code plus its exact environment — into a sealed 'container' so it runs identically on any machine: your laptop, a colleague's, or the cloud.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "docker/app/Dockerfile",
                "The recipe to build the sealed box: Python 3.11, install uv, install libraries, copy code, pre-cache dbt packages.",
            ],
            [
                "docker/docker-compose.yml",
                "Defines and wires together multiple boxes (the app, Airflow, a database).",
            ],
            [
                "tests/",
                "86 unit tests (small checks) + 13 integration smoke tests (one full pipeline run).",
            ],
        ],
    )
    code_box(
        doc,
        "docker compose build\ndocker compose run --rm app make test-all     # all 99 tests inside the box",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "You'd write a long setup document — 'install Python 3.11, then these 40 libraries at these versions...' — and pray everyone follows it identically. Docker replaces that document with an executable recipe that builds the exact environment every time.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Container vs Virtual Machine.** A VM carries an entire fake computer (slow, gigabytes). A container shares the host's core and packages only the app and its libraries (fast, megabytes). Same isolation, a fraction of the cost.",
            "**Image vs Container.** The image is the recipe (built once); a container is a running instance of it (started many times). Like a cookie-cutter vs a cookie.",
            "**Layer caching — why order matters.** Docker reuses unchanged layers. We install libraries before copying source code. So when code changes (often) but libraries don't (rare), Docker reuses the cached library layer and rebuilds in seconds.",
            "**The testing pyramid.** Many fast unit tests, fewer integration tests, a few end-to-end smoke tests. Wide at the bottom, narrow at the top.",
            "**Environment parity.** The same container runs locally and in CI. 'Works on my machine' becomes 'works in the box, everywhere.'",
        ],
    )
    marker(doc, "Visual — layer caching")
    code_box(
        doc,
        "Layer 1: Python 3.11          [rarely changes]    <- cached\n"
        "Layer 2: install uv           [rarely changes]    <- cached\n"
        "Layer 3: install libraries    [changes w/ deps]   <- usually cached\n"
        "Layer 4: copy source code     [changes always]    <- rebuilt\n"
        "   =>  Final image\n"
        "\n"
        "(Put the often-changing layer LAST so most rebuilds stay fast.)",
    )

    # ---- Phase 7 ----
    h2(doc, "Phase 7 — The Robots (CI/CD)")
    marker(doc, "Goal")
    body(
        doc,
        "Have robots automatically test every change, block broken code from the main project, and run the full pipeline on a schedule — all for free.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                ".github/workflows/ci.yml",
                "On every change: lint -> test -> build the Docker box. Any failure blocks the change.",
            ],
            [
                ".github/workflows/scheduled.yml",
                "Weekly: run the whole pipeline, export the snapshot, upload to R2, generate the health report.",
            ],
            [
                ".github/workflows/docs.yml",
                "On doc changes: rebuild and publish this documentation site + the dbt lineage map.",
            ],
            [
                ".github/workflows/tracker-sync.yml",
                "Keep the Project Tracker in sync with the task list.",
            ],
            [
                ".gitlab-ci.yml",
                "A mirror of the GitHub setup, kept as a portability demonstration.",
            ],
        ],
    )
    body(
        doc,
        "**Branch protection** is the enforcement: you cannot merge into the main branch unless all robot checks pass. (We saw this live — a direct push was rejected and forced through proper review.)",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "Before every merge a human would manually run the linters, run all 99 tests, build Docker, and only then approve — for every single change. Tedious and easily skipped under pressure. The robots do it consistently, in parallel, every time.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**CI vs CD.** Continuous Integration = automatically test every change so main always works. Continuous Delivery = every passing build is ready to ship. CI catches breakage early; CD makes releasing boring (good).",
            "**Why test on DuckDB in CI, not Snowflake.** Snowflake charges per second of compute. DuckDB is free and runs in seconds, catching 95% of bugs. Snowflake is reserved for the manual showcase build.",
            "**Merge gates + trunk-based development.** Developers work on short-lived branches and merge frequently into one main 'trunk.' The gate guarantees the trunk is always shippable.",
            "**Secrets management.** Passwords live in GitHub's encrypted Secrets store, injected at run time and masked in logs. Never in code.",
            "**The .yml file IS the automation.** Each YAML is a script the robots follow: 'on this trigger, run these steps on this machine.' Reading one top-to-bottom tells you exactly what happens and when.",
        ],
    )
    marker(doc, "Visual — the merge gate")
    code_box(
        doc,
        "Open Pull Request\n"
        "       |\n"
        "       v\n"
        "  CI robots:  lint | unit tests | integration tests | docker build\n"
        "       |\n"
        "       v\n"
        "  All green? --- no ---> Merge BLOCKED\n"
        "       |\n"
        "      yes\n"
        "       v\n"
        "  Merge ALLOWED",
    )

    # ---- Phase 8 ----
    h2(doc, "Phase 8 — The Shop Window (Dashboard)")
    marker(doc, "Goal")
    body(
        doc,
        "Show the finished, business-ready numbers on a fast, public website — one that keeps working even after the Snowflake trial ends.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "ingestion/export_snapshot.py",
                "Reads the Gold tables and writes small JSON summary files.",
            ],
            [
                "dashboard/public/data/*.json",
                "The summary files, committed into the project.",
            ],
            [
                "dashboard/app/*/page.tsx",
                "The five pages: Sales, Marketing, Category, Planning, Placement.",
            ],
            [
                "dashboard/components/charts/*.tsx",
                "The reusable chart building blocks (Recharts).",
            ],
            ["dashboard/lib/data.ts", "Reads the JSON files at build time."],
        ],
    )
    code_box(
        doc,
        "make export-snapshot     # Gold tables -> JSON\n# Vercel auto-builds the site whenever the JSON is committed",
    )
    marker(doc, "By Hand")
    body(
        doc,
        "You'd export each Gold table to a spreadsheet, build charts manually, and email screenshots — stale the moment you send them. The dashboard rebuilds automatically and is always one commit behind the latest data.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**The decoupling masterstroke.** The dashboard reads static JSON files, not the live warehouse. So when the 30-day Snowflake trial expires, the dashboard keeps working forever. This is the whole reason the project is 'zero cost permanently.'",
            "**Static vs dynamic serving.** A dynamic site queries a database on every visit (costs money, can break). A static site is pre-built into files served instantly. For a weekly-updated dashboard, static is perfect.",
            "**Server vs Client Components (the bug we hit).** Some code runs on the server at build time (can read files); some runs in the browser (handles clicks). You cannot pass a function from server to browser — only plain data. We fixed this by passing a text label (format='currency') instead of a function. A real, instructive bug.",
            "**Dashboard information hierarchy.** Big-picture numbers (KPIs) at the top, supporting charts below, detail tables at the bottom. Every element answers a specific business question. No clutter.",
        ],
    )
    marker(doc, "Visual — decoupled serving")
    code_box(
        doc,
        "Gold tables  --export once-->  JSON snapshot  --commit-->  Vercel static site  -->  Browser\n"
        "(DuckDB / Snowflake)           files\n"
        "\n"
        "Snowflake trial expires  --X-->  (no effect on the dashboard)",
    )

    # ---- Phase 9 ----
    h2(doc, "Phase 9 — Polish (Observability, Images, Docs)")
    marker(doc, "Goal")
    body(
        doc,
        "Add the senior-level finishing touches: continuous data-health monitoring, real product imagery, and published documentation.",
    )
    marker(doc, "What the automation does")
    data_table(
        doc,
        ["File", "What it does"],
        [
            [
                "packages.yml (Elementary)",
                "Adds Elementary; it records the health of every dbt run automatically.",
            ],
            [
                "scheduled.yml (edr step)",
                "Generates the HTML health report each week as a downloadable artifact.",
            ],
            [
                "ingestion/fetch_product_images.py",
                "Fetches one real photo per category from Pexels, uploads to R2, writes images.json.",
            ],
            ["mkdocs.yml + docs/*.md", "This documentation site."],
            ["docs.yml", "Publishes the docs + dbt lineage map to GitHub Pages."],
        ],
    )
    marker(doc, "By Hand")
    body(
        doc,
        "You'd eyeball row counts after each run to spot anomalies (error-prone), download product photos one by one, and maintain docs in a Word file that drifts out of date. Each script replaces a tedious, forgettable chore.",
    )
    marker(doc, "Theory worth noting")
    bullets(
        doc,
        [
            "**Data testing vs data observability.** Testing asks 'is this run correct?' (pass/fail at run time). Observability asks 'is the pattern over time healthy?' — e.g. a table that always had 50,000 rows suddenly has zero. A not_null test can pass while the table silently empties; observability catches it.",
            "**Freshness and anomaly detection.** Freshness = 'has new data arrived recently?' Anomaly detection = 'is today's row count wildly different from usual?' Both catch silent failures — the dangerous kind that throw no errors.",
            "**The calibration period.** Elementary needs ~14 runs to learn 'normal' before it can flag 'abnormal.' Early reports show history but no alerts yet — expected, not a bug.",
            "**Image licensing matters.** We use Pexels (free for any use, no attribution required) — never scraping random sites, a copyright risk on a public portfolio. Photographer credit is stored as good practice.",
        ],
    )
    marker(doc, "Visual — observability over time")
    code_box(
        doc,
        "Run 1: 50k   Run 2: 51k   Run 3: 49k   =>  Elementary learns 'normal ~50k'\n"
        "                                                      |\n"
        "                                                      v\n"
        "                                          Run 4: 0 rows  =>  ANOMALY!\n"
        "                                          (tests still pass, but something is wrong)",
    )

    # ════════════════════════════ PART 3 ════════════════════════════
    h1(doc, "Part 3 — The 'Why' Behind the Decisions")
    body(
        doc,
        "This section answers the question an interviewer loves: 'You could have done this more simply. Why didn't you?'",
    )

    h2(doc, "Why Docker? What actually ran in it?")
    body(
        doc,
        "**The problem it solves:** 'It works on my machine.' A pipeline needs a specific Python version, specific libraries, dbt, and system tools like git. Installing all that correctly on every machine is fragile.",
    )
    bullets(
        doc,
        [
            "**The app container** — data generation, ingestion, dbt, and the test suite. This is what CI builds and what guarantees the pipeline runs identically locally and in the cloud.",
            "**The Airflow containers** — the scheduler, the web UI, and a PostgreSQL database for Airflow's own bookkeeping, all wired together by Docker Compose.",
            "**Future:** the same image could deploy to any cloud container service (AWS ECS, Google Cloud Run, Kubernetes) without changing a line — that's the portability payoff.",
        ],
    )

    h2(doc, "Why dbt? Couldn't plain SQL do it all?")
    body(
        doc,
        "Yes — plain SQL can do every transformation. dbt was chosen for what it adds around the SQL:",
    )
    data_table(
        doc,
        ["Without dbt", "With dbt"],
        [
            [
                "You run scripts in the right order manually",
                "dbt reads ref() and orders them automatically",
            ],
            [
                "You hand-write COUNT(*) checks",
                "190 declarative tests run with one command",
            ],
            [
                "Docs drift out of date in a Word file",
                "Docs + a visual lineage map generate from the code",
            ],
            ["One script per warehouse", "One codebase, swap the connection"],
            [
                "No history of what a model looked like",
                "Full Git history of every transformation",
            ],
        ],
    )
    body(
        doc,
        "**The honest summary:** dbt turns SQL from scripts a person runs into software a team maintains. For a one-off query, plain SQL is fine. For a pipeline that must be tested, documented, and re-run forever, dbt earns its place. It handled type casting, de-duplication, category standardisation, SCD2 resolution, the entire star schema, 190 tests, contracts, and documentation.",
    )

    h2(doc, "Why two warehouses (Snowflake AND DuckDB)?")
    bullets(
        doc,
        [
            "**Snowflake** is what big companies use — it carries the vocabulary interviewers test (stages, micro-partitions, COPY INTO). But it's only free for 30 days.",
            "**DuckDB** is free forever and runs locally with zero setup.",
            "Writing the dbt models to run on both gives enterprise credibility AND permanent zero-cost operation. The dashboard reads an exported snapshot, so it survives the trial's end. This dual-track design is the project's defining decision.",
        ],
    )

    h2(doc, "Why Cloudflare R2 instead of Amazon S3?")
    body(
        doc,
        "Both are cloud file storage with the same interface. But S3 charges every time you download data (egress fees) and its free tier expires after 12 months. R2 has no egress fees and a permanent free tier. Because R2 is S3-compatible, the same boto3 code works unchanged.",
    )

    h2(doc, "Why generate fake data instead of using a real dataset?")
    body(
        doc,
        "Three reasons: (1) no privacy or licensing risk, (2) total control over volume and the specific flaws to clean, and (3) reproducibility via the seed. A transparent generator you can explain line-by-line is far more defensible than a downloaded dataset you didn't create.",
    )

    h2(doc, "Why automate via terminal/bash instead of clicking?")
    body(
        doc,
        "Every manual click can be forgotten, done in the wrong order, or done differently by different people. Scripting each step makes the process repeatable, reviewable, and reversible. The only human steps left are decisions (the data model) and verifications (confirming a result looks right) — exactly where human judgement adds value and automation doesn't.",
    )

    # ════════════════════════════ PART 4 ════════════════════════════
    h1(doc, "Part 4 — The Interview")
    body(
        doc,
        "Model questions and answers, grouped by type — simulating a real data-engineering interview about this project.",
    )

    h2(doc, "Logical / reasoning questions")
    qa(
        doc,
        "If the silver cleaning layer has a bug, how do you recover without re-generating data?",
        "Because Bronze is immutable, I fix the silver SQL and re-run dbt — it rebuilds Silver and Gold from the untouched Bronze. I never lose the original data, so recovery is a re-run, not a re-ingestion. This is the entire reason Bronze is never edited.",
    )
    qa(
        doc,
        "A sale references a product that doesn't exist in the dimension. What happens, and is that good or bad?",
        "The SCD2 join fails to match, so the product key falls back to a -1 'unknown' placeholder rather than NULL. This is deliberate: the sale still appears in totals (revenue isn't silently lost), and the -1 makes orphans easy to count and investigate. Dropping the row would hide a real problem.",
    )
    qa(
        doc,
        "Your weekly row count drops from 50,000 to 5,000 but every test passes. How would you catch this?",
        "Tests check correctness within a run — uniqueness, nulls, ranges — and 5,000 valid rows pass all of them. Catching the drop needs observability: Elementary tracks row counts across runs and flags the volume anomaly. This is the core difference between testing and observability.",
    )

    h2(doc, "Technical questions")
    qa(
        doc,
        "Walk me through what happens when you run 'dbt build'.",
        "dbt parses every model, reads the ref() and source() calls to build a dependency graph, then executes in order: staging views first, then the intermediate ephemeral SCD2 resolver, then the gold tables. After each model builds, its tests run. If a model or test fails, downstream models are skipped. The same command works on DuckDB or Snowflake by changing --target.",
    )
    qa(
        doc,
        "Why is staging materialized as views but gold as tables?",
        "Staging views are cheap — no storage, always reflect the latest Bronze, and they're only read during a build. Gold tables are pre-computed and stored because the dashboard reads them repeatedly and needs speed; recomputing join-heavy marts on every read would be wasteful.",
    )
    qa(
        doc,
        "How does key-pair authentication to Snowflake work, and why use it over a password?",
        "I generate an RSA key pair, register the public key on the Snowflake user, and keep the private key locally. dbt signs each connection with the private key; Snowflake verifies with the public key. No password travels over the wire and — critically — it doesn't trigger the MFA prompt, which is essential for automated pipelines that can't stop to ask a human.",
    )
    qa(
        doc,
        "Explain Docker layer caching and how you exploited it.",
        "Each Dockerfile instruction creates a cached layer reused if it and everything above it is unchanged. I copy pyproject.toml and uv.lock and install dependencies before copying source code. Dependencies change rarely, source constantly — so most rebuilds reuse the dependency layer and finish in seconds.",
    )

    h2(doc, "Theory questions")
    qa(
        doc,
        "What is an SCD Type 2, and why did you need it?",
        "It tracks the history of a dimension attribute by inserting a new row per change, each tagged with a valid-from/valid-to range. I needed it for product price and customer segment: a sale must be valued at the price on its sale date, not today's price. Overwriting (Type 1) would retroactively corrupt historical margins.",
    )
    qa(
        doc,
        "Schema-on-read vs schema-on-write — which does Bronze use and why?",
        "Schema-on-write enforces types at load time and rejects bad data. Schema-on-read stores data as-is and applies types when queried. Bronze uses schema-on-read so it can preserve the intentionally corrupted column (quantities stored as text) instead of dropping those rows — the silver layer recovers them later.",
    )
    qa(
        doc,
        "Why is idempotency essential in a pipeline?",
        "Pipelines fail and get retried. If a step isn't idempotent, a retry after a partial failure can double-load data or corrupt state. My bronze load wipes-and-reloads (--reset), dbt rebuilds deterministically, and the snapshot fully overwrites — so running once or ten times yields identical state.",
    )
    qa(
        doc,
        "Star schema vs snowflake schema — when would you choose each?",
        "A star schema keeps dimensions flat for fewer joins and simpler, faster queries — my choice here. A snowflake schema normalises dimensions into sub-tables, saving storage when dimensions are huge but adding join complexity. For analytics where query speed and clarity win, star is the default.",
    )

    h2(doc, "Practical / situational questions")
    qa(
        doc,
        "The Snowflake trial expires tomorrow. What breaks?",
        "Nothing the public sees. The dashboard reads static JSON exported from Gold, and the whole pipeline still runs on DuckDB for free. I lose the Snowflake showcase environment, but the platform keeps operating — that decoupling was designed in from the start.",
    )
    qa(
        doc,
        "You need to add a new 'loyalty tier' metric. Walk me through the change.",
        "First I define it in the metric dictionary with an exact formula. Then I add the logic to the relevant gold mart model, add tests in the schema YAML, run dbt build on DuckDB to verify, open a pull request, and let CI run lint and tests. After the merge gate passes and I merge, the scheduled pipeline picks it up and the dashboard snapshot includes it on the next run.",
    )
    qa(
        doc,
        "CI passes locally but fails in GitHub Actions. How do you debug?",
        "I check for environment differences first — usually something present locally but not on the clean CI machine. Common causes I actually hit: a linter rule (ambiguous variable name, f-string without placeholders), a formatter difference, or a path/encoding issue (Windows vs Linux). The fix is to reproduce CI locally by running the exact lint/test commands in the Docker container, then fix and push.",
    )
    qa(
        doc,
        "How would you take this from weekly batch to near-real-time?",
        "Several levers: switch gold marts to incremental materialization so only new rows process; move from a weekly schedule to event-driven triggers; replace the static JSON snapshot with a queryable edge database (Cloudflare D1 or Neon) plus time-based revalidation; and add streaming ingestion into Bronze. The medallion structure itself doesn't change — only the cadence and serving layer do.",
    )

    # ── Closing ─────────────────────────────────────────────────────────────────
    h1(doc, "Closing note")
    body(
        doc,
        "This platform was built the way production systems are built: design first, "
        "automate everything, test at every layer, keep costs at zero, and document "
        "so anyone can follow. Every tool earns its place by solving a specific, "
        "explainable problem — and every automated step maps to a manual one a person "
        "could do by hand, just slower and less reliably.",
    )
    body(
        doc,
        "If you can explain **why** each choice was made — not just **what** was built — "
        "you understand this project at the level interviews reward.",
    )

    out = Path("docs") / "Theory_Companion_v2_Guidebook.docx"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return out


if __name__ == "__main__":
    path = build()
    print(f"Guidebook written to {path}")
