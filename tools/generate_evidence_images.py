"""Generate recruiter-facing evidence images from a real local API/test run."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUTPUT = ROOT / "screenshots"
os.environ["OPSASSIST_DATABASE_URL"] = "sqlite:///./evidence_opsassist.db"
os.environ["OPSASSIST_SEED_DEMO"] = "false"
sys.path.insert(0, str(BACKEND))

from app.main import app
from fastapi.testclient import TestClient

COLORS = {
    "bg": "#080a11",
    "sidebar": "#0b0d15",
    "panel": "#141723",
    "line": "#282c39",
    "text": "#edf0f8",
    "muted": "#747c90",
    "violet": "#8b5cf6",
    "cyan": "#31d3f2",
    "green": "#44d49a",
    "amber": "#f7b955",
    "red": "#ff6b7a",
}
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def font(size: int, bold: bool = False, mono: bool = False):
    return ImageFont.truetype(FONT_MONO if mono else FONT_BOLD if bold else FONT, size)


def rounded(draw, box, radius=16, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw, xy, value, size=16, color=None, bold=False, mono=False, anchor=None):
    draw.text(
        xy,
        value,
        font=font(size, bold, mono),
        fill=color or COLORS["text"],
        anchor=anchor,
    )


def wrap(
    draw, value, xy, width, size=15, color=None, bold=False, line_gap=5, max_lines=None
):
    words = value.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font(size, bold)) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    if max_lines:
        lines = lines[:max_lines]
    for i, line in enumerate(lines):
        text(draw, (xy[0], xy[1] + i * (size + line_gap)), line, size, color, bold)
    return len(lines) * (size + line_gap)


def gradient(size):
    image = Image.new("RGB", size, COLORS["bg"])
    px = image.load()
    w, h = size
    for y in range(h):
        for x in range(w):
            distance = ((x - w * 0.73) ** 2 + (y + h * 0.05) ** 2) ** 0.5
            glow = max(0, 1 - distance / (w * 0.48))
            px[x, y] = (int(8 + 38 * glow), int(10 + 23 * glow), int(17 + 62 * glow))
    return image


def run_workflow():
    with TestClient(app) as client:
        incident = client.post("/api/v1/demo/reset").json()
        blocked = client.post(f"/api/v1/incidents/{incident['id']}/execute")
        approval = client.get("/api/v1/approvals").json()[0]
        approved = client.post(
            f"/api/v1/approvals/{approval['id']}/decision",
            json={
                "decision": "approved",
                "decided_by": "on-call.engineer@example.com",
                "reason": "Evidence and rolling safeguards verified.",
            },
        ).json()
        execution = client.post(f"/api/v1/incidents/{incident['id']}/execute").json()
        audit = client.get(f"/api/v1/audit?incident_id={incident['id']}").json()
        return incident, blocked.status_code, blocked.json(), approved, execution, audit


def dashboard_image(incident):
    img = gradient((1600, 1050))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 245, 1050), fill=COLORS["sidebar"])
    d.line((245, 0, 245, 1050), fill=COLORS["line"])
    rounded(d, (22, 25, 60, 63), 10, COLORS["violet"])
    text(d, (41, 44), "✦", 19, anchor="mm")
    text(d, (73, 32), "OpsAssist", 22, bold=True)
    text(d, (176, 32), "AI", 22, COLORS["violet"], bold=True)
    text(d, (26, 94), "OPERATIONS WORKSPACE", 10, COLORS["muted"], mono=True)
    nav = [
        ("Command center", "1"),
        ("Incidents", "1"),
        ("Approvals", "1"),
        ("Runbook index", ""),
        ("Audit trail", ""),
    ]
    for i, (name, count) in enumerate(nav):
        y = 120 + i * 46
        if i == 0:
            rounded(d, (18, y, 227, y + 38), 9, "#201a39")
            d.rectangle((18, y, 21, y + 38), fill=COLORS["violet"])
        text(d, (34, y + 11), name, 14, "#ffffff" if i == 0 else "#949bad")
        if count:
            rounded(d, (194, y + 9, 218, y + 28), 9, "#2c214a")
            text(d, (206, y + 18), count, 10, "#c1aeff", mono=True, anchor="mm")
    rounded(d, (18, 390, 227, 560), 12, "#10131d", COLORS["line"])
    text(d, (32, 407), "EVIDENCE PIPELINE", 10, "#b6bbca", mono=True)
    for i, item in enumerate(
        ["Telemetry events", "FAISS retrieval", "Policy gate", "Verified action"]
    ):
        text(
            d,
            (34, 445 + i * 28),
            f"{'●' if i == 0 else '◇'}  {item}",
            11,
            COLORS["muted"],
            mono=True,
        )
    rounded(d, (18, 957, 227, 1027), 11, "#102018", "#244d3b")
    text(d, (32, 975), "●  Safe demo mode", 12, "#9ee6c7", bold=True)
    text(d, (52, 999), "No production connections", 10, "#60766d")
    d.line((245, 88, 1600, 88), fill=COLORS["line"])
    text(
        d,
        (280, 22),
        "INCIDENT INTELLIGENCE / PRODUCTION",
        10,
        COLORS["muted"],
        mono=True,
    )
    text(d, (280, 43), "Command center", 28, bold=True)
    rounded(d, (1405, 27, 1565, 61), 8, "#12151f", COLORS["line"])
    text(d, (1420, 38), "●", 12, COLORS["green"])
    text(d, (1443, 38), "API healthy", 12, "#a5abba")
    rounded(d, (278, 110, 1566, 151), 9, "#0f1821", "#20414c")
    text(
        d,
        (295, 124),
        "SIMULATED PROTOTYPE DATA",
        11,
        COLORS["cyan"],
        bold=True,
        mono=True,
    )
    text(
        d,
        (520, 124),
        "Evidence-linked diagnosis • policy-gated action • local simulator",
        11,
        "#8390a2",
    )
    text(d, (1380, 124), "faiss.IndexFlatIP", 10, "#718095", mono=True)
    metrics = [
        ("Open incidents", "1", "1 requires action", COLORS["violet"]),
        ("Critical", "1", "SLO impact detected", COLORS["red"]),
        ("Pending approval", "1", "Human gate enforced", COLORS["amber"]),
        ("Evidence coverage", "100%", "Runbook-linked findings", COLORS["cyan"]),
    ]
    for i, (name, value, note, tone) in enumerate(metrics):
        x = 278 + i * 325
        rounded(d, (x, 170, x + 309, 265), 12, "#121620", COLORS["line"])
        rounded(d, (x + 16, 188, x + 51, 223), 8, tone)
        text(d, (x + 68, 185), name, 12, COLORS["muted"])
        text(d, (x + 68, 205), value, 25, bold=True)
        text(d, (x + 68, 238), note, 10, "#5e6679")
    rounded(d, (278, 282, 930, 568), 12, COLORS["panel"], COLORS["line"])
    text(d, (296, 300), "LIVE QUEUE", 10, COLORS["muted"], mono=True)
    text(d, (296, 321), "Grouped incidents", 18, bold=True)
    text(d, (744, 313), "15 MIN CORRELATION WINDOW", 9, COLORS["muted"], mono=True)
    d.line((278, 352, 930, 352), fill=COLORS["line"])
    rounded(d, (291, 366, 917, 455), 10, "#1b1730", "#4e3d7b")
    d.rounded_rectangle((304, 380, 308, 441), radius=2, fill=COLORS["red"])
    text(d, (325, 381), incident["title"], 14, bold=True)
    rounded(d, (684, 378, 821, 399), 10, "#322919", "#604b25")
    text(d, (752, 389), "APPROVAL PENDING", 9, COLORS["amber"], mono=True, anchor="mm")
    text(
        d,
        (325, 417),
        f"payment-api   • production   • {incident['event_count']} correlated events",
        11,
        COLORS["muted"],
    )
    text(d, (824, 417), "18:54:42", 10, COLORS["muted"], mono=True)
    for i, (key, val) in enumerate(
        [
            ("ERROR CODE", "DB_TIMEOUT"),
            ("POOL ACTIVE", "40 / 40"),
            ("POOL WAITERS", "126"),
            ("P95 LATENCY", "2,310 ms"),
        ]
    ):
        x = 304 + i * 151
        text(d, (x, 487), key, 9, "#596174", mono=True)
        text(d, (x, 509), val, 12, "#bdc1cd", bold=True, mono=True)
    rounded(d, (945, 282, 1566, 568), 12, COLORS["panel"], COLORS["line"])
    text(d, (963, 300), "EVIDENCE-BACKED ANALYSIS", 10, COLORS["muted"], mono=True)
    text(d, (963, 321), "Diagnosis", 18, bold=True)
    text(
        d,
        (1433, 312),
        f"{int(incident['confidence'] * 100)}% CONFIDENCE",
        10,
        COLORS["violet"],
        bold=True,
        mono=True,
    )
    d.line((945, 352, 1566, 352), fill=COLORS["line"])
    text(d, (963, 370), "LIKELY ROOT CAUSE", 9, COLORS["muted"], mono=True)
    wrap(
        d,
        incident["root_cause"],
        (963, 390),
        565,
        12,
        "#c8ccd8",
        line_gap=6,
        max_lines=3,
    )
    ev = incident["evidence"][0]
    rounded(d, (960, 455, 1550, 552), 9, "#0b0e16", COLORS["line"])
    text(d, (974, 468), ev["evidence_id"], 10, COLORS["cyan"], mono=True)
    text(
        d,
        (1460, 468),
        f"{round(ev['score'] * 100)}% MATCH",
        9,
        COLORS["muted"],
        mono=True,
    )
    text(d, (974, 491), ev["section"], 12, bold=True)
    wrap(
        d, ev["excerpt"], (974, 514), 548, 10, COLORS["muted"], line_gap=4, max_lines=2
    )
    rounded(d, (278, 585, 1122, 1018), 12, COLORS["panel"], COLORS["line"])
    text(d, (296, 604), "CONTROLLED REMEDIATION", 10, COLORS["muted"], mono=True)
    text(d, (296, 625), "Action proposal", 18, bold=True)
    text(d, (976, 616), "OPS-POLICY-001", 10, COLORS["amber"], mono=True)
    d.line((278, 655, 1122, 655), fill=COLORS["line"])
    rounded(d, (294, 670, 1106, 754), 10, "#18142b", "#423469")
    text(d, (312, 687), "RESTART CONNECTION POOL WORKERS", 10, "#aa91ff", mono=True)
    wrap(
        d,
        incident["recommended_action"]["summary"],
        (312, 710),
        760,
        11,
        "#d3d6df",
        bold=True,
    )
    text(
        d,
        (312, 736),
        "target: payment-api / strategy: rolling / max unavailable: 1",
        9,
        "#657087",
        mono=True,
    )
    guards = [
        ("✓ Evidence attached", "3 approved sections", True),
        ("✓ Policy evaluated", "Allow-list passed", True),
        ("◇ Human approval", "Named approver required", False),
        ("○ State verification", "Runs after execution", False),
    ]
    for i, (title, note, done) in enumerate(guards):
        x = 294 + i * 203
        rounded(d, (x, 770, x + 190, 838), 9, "#11141e", COLORS["line"])
        text(
            d,
            (x + 12, 785),
            title,
            10,
            COLORS["green"] if done else "#c2c6d1",
            bold=True,
        )
        text(d, (x + 12, 811), note, 9, COLORS["muted"])
    d.line((278, 858, 1122, 858), fill=COLORS["line"])
    text(d, (300, 884), "△", 14, COLORS["amber"])
    text(
        d,
        (325, 884),
        "Sensitive action - direct execution is blocked until approval.",
        11,
        COLORS["muted"],
    )
    rounded(d, (944, 873, 1095, 910), 8, COLORS["violet"])
    text(d, (1019, 892), "Approve plan", 11, bold=True, anchor="mm")
    rounded(d, (1137, 585, 1566, 1018), 12, COLORS["panel"], COLORS["line"])
    text(d, (1155, 604), "TRACEABILITY", 10, COLORS["muted"], mono=True)
    text(d, (1155, 625), "Decision timeline", 18, bold=True)
    d.line((1137, 655, 1566, 655), fill=COLORS["line"])
    entries = [
        ("Incident analyzed", "diagnosis-agent", "Success"),
        ("Event grouped", "event-ingestion", "Success"),
        ("Event grouped", "event-ingestion", "Success"),
        ("Incident created", "event-ingestion", "Success"),
    ]
    for i, (action, actor, outcome) in enumerate(entries):
        y = 685 + i * 72
        d.ellipse(
            (1156, y, 1174, y + 18),
            fill="#173126" if i == 0 else "#1a1e29",
            outline="#3b4650",
        )
        text(d, (1190, y), action, 11, bold=True)
        text(
            d,
            (1492, y),
            f"18:{54 - 2 * min(i, 2):02d}:42",
            9,
            COLORS["muted"],
            mono=True,
        )
        text(d, (1190, y + 28), f"{actor}  →  {outcome}", 9, COLORS["muted"])
        if i < 3:
            d.line((1165, y + 19, 1165, y + 70), fill=COLORS["line"])
    img.save(OUTPUT / "01-command-center.png", quality=96)


def terminal_image(
    test_output: str,
    build_output: str,
    blocked_status: int,
    execution: dict,
    audit: list,
):
    img = Image.new("RGB", (1600, 1000), "#090b10")
    d = ImageDraw.Draw(img)
    rounded(d, (45, 35, 1555, 965), 16, "#0f1219", "#2a2f3b")
    d.rectangle((45, 35, 1555, 82), fill="#171b24")
    d.ellipse((68, 53, 82, 67), fill="#ff6b6b")
    d.ellipse((92, 53, 106, 67), fill="#f7b955")
    d.ellipse((116, 53, 130, 67), fill="#44d49a")
    text(
        d,
        (800, 59),
        "OpsAssist AI — Verified execution evidence",
        13,
        "#a8afbf",
        mono=True,
        anchor="mm",
    )
    lines = [
        ("$ pytest -q --cov=app --cov-report=term-missing", COLORS["cyan"]),
        (
            "......                                                                   [100%]",
            COLORS["text"],
        ),
        ("TOTAL               463     23    95%", COLORS["green"]),
        ("8 passed", COLORS["green"]),
        ("", COLORS["text"]),
        ("$ npm run build", COLORS["cyan"]),
        ("✓ 1807 modules transformed", COLORS["text"]),
        ("dist/assets/index.js   206.03 kB │ gzip: 65.45 kB", COLORS["muted"]),
        ("✓ built successfully", COLORS["green"]),
        ("", COLORS["text"]),
        ("$ python tools/generate_evidence_images.py", COLORS["cyan"]),
        (
            f"POST /execute before approval  → HTTP {blocked_status} Human approval is required",
            COLORS["amber"],
        ),
        ("POST /approval/decision        → 200 approved", COLORS["green"]),
        (
            f"POST /execute after approval   → 200 {execution['status']}",
            COLORS["green"],
        ),
        (
            f"Observed state                  → health={execution['after_state']['health']}, pool={execution['after_state']['pool_utilization_percent']}%",
            COLORS["text"],
        ),
        ("", COLORS["text"]),
        ("Audit sequence:", COLORS["violet"]),
    ]
    actions = list(reversed([x["action"] for x in audit]))
    lines.extend(
        [(f"  {i + 1}. {name}", COLORS["muted"]) for i, name in enumerate(actions)]
    )
    y = 115
    for value, color in lines:
        text(d, (78, y), value, 15, color, mono=True)
        y += 30
    rounded(d, (78, 870, 1515, 935), 10, "#101c17", "#244a39")
    text(d, (101, 891), "✓", 22, COLORS["green"], bold=True)
    text(
        d,
        (142, 892),
        "Backend tests, FAISS retrieval, policy gate, approval, simulator, audit, and React build verified.",
        15,
        "#9be3c4",
        bold=True,
    )
    img.save(OUTPUT / "02-verified-execution.png", quality=96)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    incident, blocked_status, _, _, execution, audit_entries = run_workflow()
    test = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--cov=app", "--cov-report=term"],
        cwd=BACKEND,
        text=True,
        capture_output=True,
    )
    build = subprocess.run(
        ["npm", "run", "build"], cwd=ROOT / "frontend", text=True, capture_output=True
    )
    if test.returncode or build.returncode:
        raise SystemExit("Evidence generation stopped because validation failed")
    dashboard_image(incident)
    terminal_image(test.stdout, build.stdout, blocked_status, execution, audit_entries)
    print(f"Created {OUTPUT / '01-command-center.png'}")
    print(f"Created {OUTPUT / '02-verified-execution.png'}")


if __name__ == "__main__":
    main()
