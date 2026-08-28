"""Create the complete OpsAssist AI GitHub execution and source code guide."""

from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT.parent / "output" / "pdf" / "OpsAssist_AI_Complete_GitHub_Execution_Guide.pdf"
)
SHOTS = ROOT / "screenshots"

NAVY = colors.HexColor("#090B12")
INK = colors.HexColor("#171A25")
MUTED = colors.HexColor("#656D7E")
LINE = colors.HexColor("#DDE1EA")
VIOLET = colors.HexColor("#7148E8")
CYAN = colors.HexColor("#079BB8")
GREEN = colors.HexColor("#187D59")
AMBER = colors.HexColor("#9B650A")

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(
    TTFont("DV-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
)
pdfmetrics.registerFont(
    TTFont("DV-Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
)


class GuideDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title="OpsAssist AI Complete GitHub Execution Guide",
            author="Aahana Ahir",
        )
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height, id="body"
        )
        self.addPageTemplates(
            PageTemplate(id="guide", frames=frame, onPage=self.draw_page)
        )

    def draw_page(self, canvas, doc):
        canvas.saveState()
        if doc.page == 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        else:
            canvas.setStrokeColor(LINE)
            canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
            canvas.setFont("DV", 7.4)
            canvas.setFillColor(MUTED)
            canvas.drawString(
                18 * mm, 9.5 * mm, "OPSASSIST AI | COMPLETE GITHUB EXECUTION GUIDE"
            )
            canvas.drawRightString(A4[0] - 18 * mm, 9.5 * mm, f"PAGE {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"H1", "H2"}:
            level = 0 if flowable.style.name == "H1" else 1
            key = f"heading-{self.seq.nextf('heading')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(
                flowable.getPlainText(), key, level=level, closed=False
            )


STYLES = {
    "cover_kicker": ParagraphStyle(
        "CoverKicker",
        fontName="DV-Mono",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#86E8F5"),
        spaceAfter=14,
    ),
    "cover_title": ParagraphStyle(
        "CoverTitle",
        fontName="DV-Bold",
        fontSize=32,
        leading=39,
        textColor=colors.white,
        spaceAfter=12,
    ),
    "cover_sub": ParagraphStyle(
        "CoverSub",
        fontName="DV",
        fontSize=14,
        leading=21,
        textColor=colors.HexColor("#BBC1D0"),
        spaceAfter=15,
    ),
    "cover_meta": ParagraphStyle(
        "CoverMeta",
        fontName="DV-Mono",
        fontSize=8.7,
        leading=15,
        textColor=colors.HexColor("#8891A5"),
    ),
    "H1": ParagraphStyle(
        "H1",
        fontName="DV-Bold",
        fontSize=21,
        leading=26,
        textColor=INK,
        spaceBefore=4,
        spaceAfter=11,
        keepWithNext=True,
    ),
    "H2": ParagraphStyle(
        "H2",
        fontName="DV-Bold",
        fontSize=14,
        leading=18,
        textColor=VIOLET,
        spaceBefore=11,
        spaceAfter=7,
        keepWithNext=True,
    ),
    "body": ParagraphStyle(
        "Body", fontName="DV", fontSize=9.1, leading=14, textColor=INK, spaceAfter=6
    ),
    "small": ParagraphStyle(
        "Small", fontName="DV", fontSize=7.6, leading=11, textColor=MUTED, spaceAfter=4
    ),
    "bullet": ParagraphStyle(
        "Bullet",
        fontName="DV",
        fontSize=9,
        leading=13.6,
        textColor=INK,
        leftIndent=13,
        firstLineIndent=-7,
        spaceAfter=4,
    ),
    "step": ParagraphStyle(
        "Step",
        fontName="DV",
        fontSize=9.1,
        leading=14,
        textColor=INK,
        leftIndent=16,
        firstLineIndent=-16,
        spaceAfter=7,
    ),
    "code": ParagraphStyle(
        "Code",
        fontName="DV-Mono",
        fontSize=6.4,
        leading=8.2,
        textColor=colors.HexColor("#222633"),
        backColor=colors.HexColor("#F4F6F9"),
        borderColor=LINE,
        borderWidth=0.5,
        borderPadding=8,
        spaceBefore=3,
        spaceAfter=8,
    ),
    "code_light": ParagraphStyle(
        "CodeLight",
        fontName="DV-Mono",
        fontSize=6.0,
        leading=7.6,
        textColor=colors.HexColor("#222633"),
        backColor=colors.HexColor("#F4F6F9"),
        borderColor=LINE,
        borderWidth=0.5,
        borderPadding=7,
        spaceBefore=3,
        spaceAfter=7,
    ),
    "caption": ParagraphStyle(
        "Caption",
        fontName="DV",
        fontSize=7.4,
        leading=10,
        textColor=MUTED,
        alignment=1,
        spaceBefore=4,
        spaceAfter=9,
    ),
    "path": ParagraphStyle(
        "Path",
        fontName="DV-Mono",
        fontSize=8.5,
        leading=12,
        textColor=CYAN,
        spaceAfter=5,
    ),
}


def para(value, style="body"):
    return Paragraph(value, STYLES[style])


def bullet(value):
    return Paragraph(f"&#8226;&nbsp;&nbsp;{value}", STYLES["bullet"])


def step(number, title, body):
    return Paragraph(f"<b>{number}. {title}</b><br/>{body}", STYLES["step"])


def code(value, light=False):
    return Preformatted(
        value.strip("\n"), STYLES["code_light" if light else "code"], maxLineLength=100
    )


def data_table(rows, widths, header=True, font_size=7.5):
    cell_style = ParagraphStyle(
        "Cell", fontName="DV", fontSize=font_size, leading=font_size + 3, textColor=INK
    )
    head_style = ParagraphStyle(
        "Head",
        fontName="DV-Bold",
        fontSize=font_size,
        leading=font_size + 3,
        textColor=colors.white,
    )
    data = [
        [
            Paragraph(str(value), head_style if header and r == 0 else cell_style)
            for value in row
        ]
        for r, row in enumerate(rows)
    ]
    result = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    for row in range(1 if header else 0, len(rows)):
        if row % 2 == 0:
            commands.append(
                ("BACKGROUND", (0, row), (-1, row), colors.HexColor("#F7F8FA"))
            )
    result.setStyle(TableStyle(commands))
    return result


def callout(title, body, tone="violet"):
    tones = {
        "violet": (colors.HexColor("#F1EDFF"), VIOLET),
        "cyan": (colors.HexColor("#EAF9FC"), CYAN),
        "green": (colors.HexColor("#EAF8F2"), GREEN),
        "amber": (colors.HexColor("#FFF6E6"), AMBER),
    }
    background, accent = tones[tone]
    block = Table([[para(f"<b>{title}</b><br/>{body}")]], colWidths=[166 * mm])
    block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, accent),
                ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return block


def shot(path, caption):
    return [Image(str(path), width=166 * mm, height=109 * mm), para(caption, "caption")]


def cover():
    return [
        Spacer(1, 38 * mm),
        para("PORTFOLIO ENGINEERING PLAYBOOK", "cover_kicker"),
        para("OpsAssist AI", "cover_title"),
        para(
            "Complete GitHub Execution Guide<br/>and Full Source Code Appendix",
            "cover_sub",
        ),
        Spacer(1, 9 * mm),
        para(
            "Evidence-backed incident diagnosis and controlled remediation", "cover_sub"
        ),
        Spacer(1, 35 * mm),
        para(
            "Aahana Ahir | B.Tech Computer Science and Engineering<br/>VIT Bhopal University | Expected graduation: 2027<br/>aahanaahir10@gmail.com | linkedin.com/in/aahanaahir02",
            "cover_meta",
        ),
        Spacer(1, 27 * mm),
        para(
            "EXECUTION MODE: SIMULATED PROTOTYPE<br/>VALIDATION: 8 TESTS PASSED | 95% COVERAGE | REACT BUILD VERIFIED",
            "cover_meta",
        ),
        PageBreak(),
    ]


def guide_pages():
    story = []
    story += [
        para("How to use this guide", "H1"),
        para(
            "This PDF accompanies the downloadable OpsAssist AI repository. Follow the numbered sections to run the project, verify the safety workflow, create the GitHub repository, capture evidence, and present it to international recruiters. The source appendix shows every human-authored file and its exact destination."
        ),
        callout(
            "Truthful portfolio boundary",
            "This is a tested simulated prototype. It demonstrates Python, FastAPI, React, SQL, FAISS retrieval, typed planning, approval policies, auditability, Docker, CI, and testing. It does not claim production deployment or real infrastructure execution.",
            "amber",
        ),
        para("Contents", "H2"),
    ]
    for item in [
        "1. Recruiter evidence path",
        "2. Software prerequisites",
        "3. Exact repository structure",
        "4. Local and Docker execution",
        "5. Approval-gated demo workflow",
        "6. GitHub upload and settings",
        "7. Screenshots and five-minute demo",
        "8. Architecture and safety design",
        "9. Validation and troubleshooting",
        "10. Resume and interview use",
        "11. Full source code appendix",
    ]:
        story.append(para(item))
    story.append(PageBreak())

    story += [
        para("1. Recruiter evidence path", "H1"),
        para("Build one continuous chain of proof:"),
        code(
            "OpsAssist AI -> GitHub -> README -> architecture -> code -> screenshots -> demo",
            light=True,
        ),
        para(
            "A recruiter should understand the problem in 30 seconds, inspect the system design in two minutes, and run the repository without contacting you."
        ),
        data_table(
            [
                ["Click", "Evidence", "Claim supported"],
                [
                    "README",
                    "Problem, scope, setup, boundaries",
                    "Technical communication",
                ],
                [
                    "Architecture",
                    "Components, data flow, trust boundaries",
                    "Backend and system design",
                ],
                [
                    "Code",
                    "FastAPI, SQLAlchemy, Pydantic, FAISS, React",
                    "Python, APIs, AI/RAG, full stack",
                ],
                [
                    "Screenshots",
                    "Incident, evidence, policy, approval, audit",
                    "The project runs",
                ],
                [
                    "Tests and CI",
                    "Safety-path tests and production build",
                    "Software quality",
                ],
                ["Demo", "Reproducible five-minute scenario", "Can explain decisions"],
            ],
            [26 * mm, 73 * mm, 67 * mm],
        ),
    ]
    story += shot(
        SHOTS / "01-command-center.png",
        "Figure 1. Command center generated from the deterministic simulated payment timeout scenario.",
    )
    story += shot(
        SHOTS / "02-verified-execution.png",
        "Figure 2. Verified test, coverage, frontend build, policy block, approval, simulator state, and audit evidence.",
    )

    story += [
        PageBreak(),
        para("2. Software prerequisites", "H1"),
        data_table(
            [
                ["Tool", "Recommended", "Check command", "Purpose"],
                ["Git", "2.40+", "git --version", "Version control and GitHub"],
                ["Python", "3.12+", "python --version", "Backend and tests"],
                ["Node.js", "22+", "node --version", "React development"],
                ["npm", "10+", "npm --version", "Frontend packages"],
                [
                    "Docker Desktop",
                    "Current stable",
                    "docker --version",
                    "PostgreSQL demo route",
                ],
                ["VS Code", "Current stable", "code --version", "Editor; optional"],
            ],
            [28 * mm, 27 * mm, 46 * mm, 65 * mm],
        ),
        para(
            "Install software only from official sources. Never upload `.env`, API keys, virtual environments, node_modules, database files, or caches."
        ),
        para("Choose a route", "H2"),
        data_table(
            [
                ["Route", "Best use", "Database", "Start"],
                ["Local", "Learning and code changes", "SQLite", "Two terminals"],
                [
                    "Docker Compose",
                    "Consistent recruiter demo",
                    "PostgreSQL",
                    "docker compose up --build",
                ],
            ],
            [30 * mm, 57 * mm, 32 * mm, 47 * mm],
        ),
    ]

    story += [
        PageBreak(),
        para("3. Exact repository structure", "H1"),
        step(
            1,
            "Extract the delivered ZIP",
            "Extract `OpsAssist_AI_GitHub_Repository.zip`. The top folder must be `opsassist-ai`. Upload the contents, not the ZIP itself, to GitHub.",
        ),
        step(
            2,
            "Open the folder",
            "In VS Code choose File -> Open Folder and select `opsassist-ai`. README.md, backend, frontend, docs, screenshots, tools, and docker-compose.yml must appear at the root.",
        ),
        step(
            3,
            "Verify placement",
            "Run `find . -maxdepth 3 -type f | sort`, or PowerShell `Get-ChildItem -Recurse -File`.",
        ),
        code(
            """opsassist-ai/
|-- .github/workflows/ci.yml
|-- backend/app/
|   |-- data/runbooks/
|   |-- config.py, database.py, models.py
|   |-- schemas.py, engine.py, seed.py, main.py
|-- backend/tests/
|-- frontend/src/main.tsx
|-- frontend/src/styles.css
|-- docs/
|-- screenshots/
|-- tools/
|-- docker-compose.yml
`-- README.md""",
            light=True,
        ),
        callout(
            "Keep the internal paths",
            "Python imports expect backend/app, Vite expects frontend/src, and README image links expect screenshots. Rename only the remote repository if needed.",
            "cyan",
        ),
    ]

    story += [
        PageBreak(),
        para("4. Local and Docker execution", "H1"),
        para("macOS or Linux setup", "H2"),
        code("""cd opsassist-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend && npm install && cd .."""),
        para("Windows PowerShell setup", "H2"),
        code("""cd opsassist-ai
py -3.12 -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r backend\\requirements.txt
cd frontend
npm install
cd .."""),
        callout(
            "PowerShell activation",
            "If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. Do not change the machine-wide policy.",
            "amber",
        ),
        para("Terminal 1 - backend", "H2"),
        code("""source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --port 8000"""),
        para(
            "Open `http://localhost:8000/health`. Expected values: healthy, faiss.IndexFlatIP, and simulated."
        ),
        para("Terminal 2 - frontend", "H2"),
        code("""cd opsassist-ai/frontend
npm run dev"""),
        para("Open `http://localhost:5173`."),
        para("Docker route", "H2"),
        code("""cd opsassist-ai
docker compose up --build"""),
        para(
            "Open the dashboard at `http://localhost:8080` and FastAPI documentation at `http://localhost:8000/docs`. Docker uses PostgreSQL; local development uses SQLite."
        ),
    ]

    story += [
        PageBreak(),
        para("5. Approval-gated demo workflow", "H1"),
        step(
            1,
            "Reset the scenario",
            "Click Reset scenario or POST `/api/v1/demo/reset`. Three DB_TIMEOUT events are grouped into one critical payment incident.",
        ),
        step(
            2,
            "Inspect evidence",
            "Confirm stable `RB-PAY-001` evidence IDs, FAISS retrieval, and confidence 0.88.",
        ),
        step(
            3,
            "Prove the block",
            "Execute before approval. HTTP 409 `Human approval is required` is correct.",
        ),
        step(
            4,
            "Approve",
            "Store the approver identity, decision, reason, and timestamp.",
        ),
        step(
            5,
            "Execute safely",
            "The simulator returns before and after state. No Kubernetes, AWS, or production system is contacted.",
        ),
        step(
            6,
            "Inspect audit",
            "Confirm incident.created, event.grouped, incident.analyzed, approval.decided, and remediation.executed.",
        ),
        para("Command-line reproduction", "H2"),
        code("""curl -X POST http://localhost:8000/api/v1/demo/reset
curl http://localhost:8000/api/v1/incidents
curl http://localhost:8000/api/v1/approvals

# Must return HTTP 409 before approval:
curl -X POST http://localhost:8000/api/v1/incidents/INCIDENT_ID/execute

curl -X POST http://localhost:8000/api/v1/approvals/APPROVAL_ID/decision \\
  -H "Content-Type: application/json" \\
  -d '{"decision":"approved","decided_by":"on-call.engineer@example.com","reason":"Evidence and safeguards verified."}'

curl -X POST http://localhost:8000/api/v1/incidents/INCIDENT_ID/execute
curl "http://localhost:8000/api/v1/audit?incident_id=INCIDENT_ID"""),
        callout(
            "Runtime IDs",
            "Copy the current incident and approval UUIDs from the list endpoints. Do not hard-code example IDs.",
            "cyan",
        ),
    ]

    story += [
        PageBreak(),
        para("6. GitHub upload and settings", "H1"),
        step(
            1,
            "Create the remote",
            "GitHub -> New repository. Name: `opsassist-ai`. Set Public. Do not initialize a README, license, or gitignore.",
        ),
        step(2, "Initialize Git", "Run the commands below from the repository root."),
        code("""git init
git branch -M main
git add .
git status
git commit -m "feat: build evidence-backed incident response prototype"
git remote add origin https://github.com/YOUR_USERNAME/opsassist-ai.git
git push -u origin main"""),
        step(
            3,
            "Check the staged set",
            "Before commit, verify that `.env`, `.venv`, node_modules, dist, databases, and caches are absent.",
        ),
        step(
            4,
            "Verify CI",
            "The Actions tab must show green backend and frontend jobs. Backend coverage must remain at least 85%.",
        ),
        para("Repository settings", "H2"),
        data_table(
            [
                ["Setting", "Recommended value"],
                [
                    "Description",
                    "Evidence-backed incident diagnosis and controlled remediation",
                ],
                [
                    "Topics",
                    "fastapi, react, typescript, faiss, rag, postgresql, docker, incident-response, ai-safety, python",
                ],
                ["Website", "Add only after a real deployment exists"],
                ["Default branch", "main"],
                ["Social preview", "01-command-center.png"],
                ["Profile", "Pin in the first three repositories"],
            ],
            [47 * mm, 119 * mm],
        ),
        callout(
            "Replace YOUR_USERNAME",
            "Change the placeholder clone URL only after your GitHub repository exists. Do not invent a link on your resume.",
            "amber",
        ),
    ]

    story += [
        PageBreak(),
        para("7. Screenshots and five-minute demo", "H1"),
        data_table(
            [
                ["Filename", "Capture", "Proof"],
                [
                    "01-command-center.png",
                    "Dashboard before approval",
                    "Simulated label, incident, evidence, policy",
                ],
                [
                    "02-verified-execution.png",
                    "Terminal evidence",
                    "Tests, coverage, build, 409 then 200",
                ],
                ["03-api-docs.png", "FastAPI /docs", "Endpoints and schemas"],
                [
                    "04-approved-plan.png",
                    "After approval",
                    "Named approver and safe execute button",
                ],
                [
                    "05-resolved-audit.png",
                    "After execution",
                    "Verified state and audit entry",
                ],
            ],
            [44 * mm, 49 * mm, 73 * mm],
        ),
        para(
            "Capture at 1440 x 900 or higher, 100% zoom, with no unrelated tabs, personal bookmarks, private URLs, keys, or real logs. Keep the simulated disclosure visible."
        ),
        para("Five-minute narration", "H2"),
        data_table(
            [
                ["Time", "Show", "Explain"],
                ["0:00-0:30", "README", "Problem and truthful simulator boundary"],
                ["0:30-1:20", "Incident", "Three events grouped inside 15 minutes"],
                ["1:20-2:10", "Evidence", "Stable FAISS runbook evidence IDs"],
                ["2:10-3:10", "Policy", "Sensitive action blocked until approval"],
                ["3:10-4:00", "Execution", "Observed state and audit"],
                ["4:00-5:00", "Tests/code", "FastAPI, React, DB, Docker, CI"],
            ],
            [24 * mm, 49 * mm, 93 * mm],
        ),
    ]

    story += [
        PageBreak(),
        para("8. Architecture and safety design", "H1"),
        data_table(
            [
                ["Layer", "Responsibility"],
                ["Telemetry", "Normalized service events"],
                ["FastAPI", "Pydantic validation and REST boundary"],
                [
                    "Correlation",
                    "Environment + service + error code + 15-minute window",
                ],
                ["SQL state", "Incidents, events, approvals, audit"],
                ["FAISS", "Ranked runbook chunks with stable evidence IDs"],
                ["Diagnosis", "Root cause, confidence, typed action plan"],
                ["Policy", "Allow-list, threshold, and risk"],
                ["Approval", "Identity, decision, reason, timestamp"],
                ["Simulator", "Before and after state; observed verification"],
                ["Audit", "Complete decision sequence"],
            ],
            [38 * mm, 128 * mm],
        ),
        para("Typed action contract", "H2"),
        code("""{
  "action_type": "restart_connection_pool_workers",
  "target": "payment-api",
  "risk": "sensitive",
  "parameters": {"strategy": "rolling", "max_unavailable": 1},
  "evidence_ids": ["RB-PAY-001#verification"]
}"""),
        para(
            "The diagnosis is deterministic so the demo works without a paid key and remains reproducible. A future LLM adapter can propose the same typed schema; policy and execution remain deterministic."
        ),
        para("Production gaps", "H2"),
        bullet("OAuth, RBAC, tenant isolation, rate limiting, and secret management"),
        bullet("Alembic migrations and distributed event correlation"),
        bullet("Tamper-evident external audit storage and policy versioning"),
        bullet(
            "Reviewed, sandboxed infrastructure adapters with short-lived credentials"
        ),
        bullet("Human-labeled benchmark for retrieval and diagnosis"),
    ]

    story += [
        PageBreak(),
        para("9. Validation and troubleshooting", "H1"),
        code("""cd backend
pytest -q --cov=app --cov-report=term-missing

cd ../frontend
npm run build"""),
        data_table(
            [
                ["Check", "Verified result"],
                ["Backend tests", "8 passed"],
                ["Statement coverage", "95%"],
                ["Retrieval", "faiss.IndexFlatIP"],
                ["Before approval", "HTTP 409"],
                ["After approval", "HTTP 200 verified"],
                ["Observed health", "healthy"],
                ["Frontend", "Vite build successful"],
            ],
            [72 * mm, 94 * mm],
        ),
        para("Common fixes", "H2"),
        data_table(
            [
                ["Symptom", "Cause", "Fix"],
                ["ModuleNotFoundError: app", "Wrong directory", "Run from backend"],
                [
                    "Port 8000 in use",
                    "Another process",
                    "Stop it or change backend and proxy ports",
                ],
                [
                    "API unavailable",
                    "Backend stopped",
                    "Check /health and vite.config.ts",
                ],
                [
                    "FAISS install fails",
                    "Unsupported runtime",
                    "Use 64-bit Python 3.12",
                ],
                [
                    "PowerShell blocks activation",
                    "Execution policy",
                    "Set CurrentUser RemoteSigned",
                ],
                [
                    "Execute returns 409",
                    "No approval",
                    "Approve the pending request first",
                ],
                [
                    "CI coverage fails",
                    "Untested changes",
                    "Add tests; do not hide the gap",
                ],
            ],
            [43 * mm, 48 * mm, 75 * mm],
            font_size=7.1,
        ),
    ]

    story += [
        PageBreak(),
        para("10. Resume and interview use", "H1"),
        callout(
            "Recommended resume bullets",
            "<b>OpsAssist AI - Evidence-Backed Incident Diagnosis Platform</b><br/>Built a FastAPI and React incident-operations prototype that groups telemetry, retrieves approved runbook evidence using FAISS, generates Pydantic-validated action plans, and enforces human approval for sensitive remediation.<br/><br/>Implemented SQLAlchemy persistence, PostgreSQL/SQLite modes, Docker Compose, queryable audit trails, and a least-privilege simulator; validated the safety workflow with integration tests and 95% statement coverage.",
            "green",
        ),
        para("30-second explanation", "H2"),
        para(
            "OpsAssist AI addresses a risk in AI incident tools: a plausible recommendation is not enough unless the system can show evidence and control execution. My prototype groups operational events, retrieves approved runbook sections with FAISS, creates a typed plan, applies deterministic policy, and blocks sensitive remediation until a named human approves. Execution is intentionally simulated and confirms only observed state."
        ),
        para("Likely questions", "H2"),
        data_table(
            [
                ["Question", "Answer direction"],
                [
                    "Why FAISS?",
                    "Fast local similarity search and inspectable service-filtered evidence.",
                ],
                [
                    "Is it RAG?",
                    "Yes, retrieval augments diagnosis; the delivered diagnosis is deterministic and an LLM adapter is future work.",
                ],
                [
                    "Why approval?",
                    "Operational actions have asymmetric risk; approval is an explicit control point.",
                ],
                [
                    "Is audit immutable?",
                    "No. It is queryable relational state; production needs append-only external integrity.",
                ],
                [
                    "Why two databases?",
                    "SQLite removes setup friction; PostgreSQL shows the production-style path.",
                ],
                [
                    "What next?",
                    "RBAC, migrations, OpenTelemetry, benchmark, sandboxed adapters.",
                ],
            ],
            [45 * mm, 121 * mm],
        ),
        callout(
            "Do not exaggerate",
            "Say `built and tested a simulated prototype`, not `deployed an autonomous production platform`.",
            "amber",
        ),
    ]

    story += [
        PageBreak(),
        para("11. Full source code appendix", "H1"),
        para(
            "Every human-authored repository file is reproduced below with its exact destination. Auto-generated package-lock, dist, cache, database, and virtual-environment files are excluded. The ZIP repository remains the copy/paste source of truth."
        ),
        callout(
            "Appendix format",
            "Each file starts on a new page. Paths are relative to the `opsassist-ai` root. The PDF text remains searchable and copyable.",
            "cyan",
        ),
    ]
    return story


SOURCE_ORDER = [
    ".gitignore",
    ".env.example",
    "ruff.toml",
    "Makefile",
    "docker-compose.yml",
    "LICENSE",
    ".github/workflows/ci.yml",
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "docs/architecture.md",
    "docs/api.md",
    "docs/demo-script.md",
    "backend/requirements.txt",
    "backend/requirements-dev.txt",
    "backend/Dockerfile",
    "backend/app/__init__.py",
    "backend/app/config.py",
    "backend/app/database.py",
    "backend/app/models.py",
    "backend/app/schemas.py",
    "backend/app/engine.py",
    "backend/app/seed.py",
    "backend/app/main.py",
    "backend/app/data/runbooks/payments-database.md",
    "backend/app/data/runbooks/checkout-dependencies.md",
    "backend/app/data/runbooks/catalog-memory.md",
    "backend/app/data/runbooks/general-triage.md",
    "backend/tests/conftest.py",
    "backend/tests/test_api.py",
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/tsconfig.app.json",
    "frontend/tsconfig.node.json",
    "frontend/vite.config.ts",
    "frontend/index.html",
    "frontend/Dockerfile",
    "frontend/nginx.conf",
    "frontend/src/vite-env.d.ts",
    "frontend/src/main.tsx",
    "frontend/src/styles.css",
    "tools/requirements.txt",
    "tools/generate_evidence_images.py",
]


def append_sources(story):
    for index, relative in enumerate(SOURCE_ORDER, start=1):
        path = ROOT / relative
        content = path.read_text(encoding="utf-8")
        story.extend(
            [
                PageBreak(),
                para(f"Code file {index:02d}", "H2"),
                para(relative, "path"),
                para(
                    f"Destination: <b>opsassist-ai/{html.escape(relative)}</b>", "small"
                ),
                code(content, light=True),
            ]
        )


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story = cover() + guide_pages()
    append_sources(story)
    GuideDoc(str(OUTPUT)).build(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
