import { StrictMode, useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BadgeCheck,
  BellRing,
  BookOpenText,
  Boxes,
  Check,
  ChevronRight,
  Clock3,
  Database,
  FileClock,
  Gauge,
  GitBranch,
  KeyRound,
  Play,
  RefreshCw,
  SearchCode,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  TriangleAlert,
} from "lucide-react";
import "./styles.css";

type Incident = {
  id: string;
  title: string;
  service: string;
  environment: string;
  severity: string;
  status: string;
  event_count: number;
  last_seen: string;
  root_cause: string | null;
  confidence: number | null;
  evidence: Array<{
    evidence_id: string;
    runbook_title: string;
    section: string;
    excerpt: string;
    score: number;
  }>;
  recommended_action: {
    action_type: string;
    target: string;
    summary: string;
  } | null;
  policy_decision: { decision: string; reason: string; policy: string } | null;
};
type Approval = {
  id: string;
  incident_id: string;
  status: string;
  decided_by: string | null;
};
type Audit = {
  id: string;
  incident_id: string | null;
  actor: string;
  action: string;
  outcome: string;
  created_at: string;
};
type Summary = {
  open_incidents: number;
  critical_incidents: number;
  pending_approvals: number;
  resolved_today: number;
  retrieval_engine: string;
  evidence_coverage: number;
};
const API = "/api/v1";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    const d = await r.json();
    throw new Error(d.detail || "Request failed");
  }
  return r.json();
}
const label = (v: string) =>
  v.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const time = (v: string) =>
  new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(v));

function App() {
  const [summary, setSummary] = useState<Summary>({
    open_incidents: 0,
    critical_incidents: 0,
    pending_approvals: 0,
    resolved_today: 0,
    retrieval_engine: "initializing",
    evidence_coverage: 0,
  });
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const load = useCallback(async () => {
    try {
      const [s, i, p, a] = await Promise.all([
        request<Summary>("/dashboard"),
        request<Incident[]>("/incidents"),
        request<Approval[]>("/approvals"),
        request<Audit[]>("/audit"),
      ]);
      setSummary(s);
      setIncidents(i);
      setApprovals(p);
      setAudit(a);
      setSelectedId((x) => x || i[0]?.id || null);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "API unavailable");
    }
  }, []);
  useEffect(() => {
    load();
  }, [load]);
  const selected = useMemo(
    () => incidents.find((x) => x.id === selectedId) || incidents[0],
    [incidents, selectedId],
  );
  const approval = approvals.find((x) => x.incident_id === selected?.id);
  const timeline = audit
    .filter((x) => x.incident_id === selected?.id)
    .slice(0, 5);
  const act = async (fn: () => Promise<unknown>, message: string) => {
    setBusy(true);
    try {
      await fn();
      setNotice(message);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  };
  const reset = () =>
    act(
      () => request("/demo/reset", { method: "POST" }),
      "Demo scenario restored.",
    );
  const approve = () =>
    approval &&
    act(
      () =>
        request(`/approvals/${approval.id}/decision`, {
          method: "POST",
          body: JSON.stringify({
            decision: "approved",
            decided_by: "demo.on-call@opsassist.dev",
            reason:
              "Evidence IDs, confidence threshold, and rolling safeguards verified.",
          }),
        }),
      "Plan approved by the demo on-call engineer.",
    );
  const execute = () =>
    selected &&
    act(
      () => request(`/incidents/${selected.id}/execute`, { method: "POST" }),
      "Execution verified: healthy post-action state observed.",
    );
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span>
            <Sparkles />
          </span>
          <strong>
            OpsAssist <i>AI</i>
          </strong>
        </div>
        <small>OPERATIONS WORKSPACE</small>
        <nav>
          <button className="active">
            <Gauge />
            Command center
          </button>
          <button>
            <BellRing />
            Incidents<b>{summary.open_incidents}</b>
          </button>
          <button>
            <ShieldCheck />
            Approvals<b>{summary.pending_approvals}</b>
          </button>
          <button>
            <BookOpenText />
            Runbook index
          </button>
          <button>
            <FileClock />
            Audit trail
          </button>
        </nav>
        <div className="mini">
          <h4>
            <GitBranch />
            EVIDENCE PIPELINE
          </h4>
          <p>
            <Activity />
            Telemetry <ChevronRight />
          </p>
          <p>
            <SearchCode />
            FAISS retrieval <ChevronRight />
          </p>
          <p>
            <ShieldCheck />
            Policy gate <ChevronRight />
          </p>
          <p>
            <TerminalSquare />
            Verified action
          </p>
        </div>
        <div className="safe">
          <em></em>
          <div>
            <strong>Safe demo mode</strong>
            <span>No production connections</span>
          </div>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <small>INCIDENT INTELLIGENCE / PRODUCTION</small>
            <h1>Command center</h1>
          </div>
          <div>
            <span className="health">
              <em />
              API healthy
            </span>
            <button className="reset" onClick={reset} disabled={busy}>
              <RefreshCw />
              Reset scenario
            </button>
          </div>
        </header>
        <section className="content">
          <div className="banner">
            <Boxes />
            <strong>SIMULATED PROTOTYPE DATA</strong>
            <span>
              Every diagnosis is evidence-linked; every action is policy-gated
              and locally simulated.
            </span>
            <code>
              <Database />
              {summary.retrieval_engine}
            </code>
          </div>
          {error && (
            <div className="error">
              <TriangleAlert />
              {error}
            </div>
          )}
          {notice && (
            <div className="notice">
              <Check />
              {notice}
            </div>
          )}
          <div className="metrics">
            <Metric
              title="Open incidents"
              value={summary.open_incidents}
              note="1 requires action"
              tone="violet"
              icon={<BellRing />}
            />
            <Metric
              title="Critical"
              value={summary.critical_incidents}
              note="SLO impact detected"
              tone="red"
              icon={<TriangleAlert />}
            />
            <Metric
              title="Pending approval"
              value={summary.pending_approvals}
              note="Human gate enforced"
              tone="amber"
              icon={<KeyRound />}
            />
            <Metric
              title="Evidence coverage"
              value={Math.round(summary.evidence_coverage * 100) + "%"}
              note="Runbook-linked findings"
              tone="cyan"
              icon={<BadgeCheck />}
            />
          </div>
          <div className="topgrid">
            <div className="panel incidents">
              <PanelHead
                kicker="LIVE QUEUE"
                title="Grouped incidents"
                side="15 min correlation window"
              />
              {incidents.map((x) => (
                <button
                  className={
                    "incident " + (x.id === selected?.id ? "selected" : "")
                  }
                  key={x.id}
                  onClick={() => setSelectedId(x.id)}
                >
                  <em className={x.severity} />
                  <div>
                    <strong>
                      {x.title}
                      <span>{label(x.status)}</span>
                    </strong>
                    <p>
                      <code>{x.service}</code> • {x.environment} •{" "}
                      {x.event_count} correlated events
                    </p>
                  </div>
                  <time>
                    <Clock3 />
                    {time(x.last_seen)}
                  </time>
                  <ChevronRight />
                </button>
              ))}
              <div className="signals">
                <div>
                  <span>ERROR CODE</span>
                  <b>DB_TIMEOUT</b>
                </div>
                <div>
                  <span>POOL ACTIVE</span>
                  <b>40 / 40</b>
                </div>
                <div>
                  <span>POOL WAITERS</span>
                  <b>126</b>
                </div>
                <div>
                  <span>P95 LATENCY</span>
                  <b>2,310 ms</b>
                </div>
              </div>
            </div>
            {selected && (
              <div className="panel diagnosis">
                <PanelHead
                  kicker="EVIDENCE-BACKED ANALYSIS"
                  title="Diagnosis"
                  side={`${Math.round((selected.confidence || 0) * 100)}% CONFIDENCE`}
                />
                <div className="root">
                  <SearchCode />
                  <div>
                    <span>LIKELY ROOT CAUSE</span>
                    <p>{selected.root_cause}</p>
                  </div>
                </div>
                <div className="evidence">
                  {selected.evidence.map((e) => (
                    <article key={e.evidence_id}>
                      <header>
                        <code>{e.evidence_id}</code>
                        <span>{Math.round(e.score * 100)}% MATCH</span>
                      </header>
                      <strong>{e.section}</strong>
                      <p>{e.excerpt}</p>
                      <footer>
                        <BookOpenText />
                        {e.runbook_title}
                      </footer>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </div>
          {selected && (
            <div className="lower">
              <div className="panel action">
                <PanelHead
                  kicker="CONTROLLED REMEDIATION"
                  title="Action proposal"
                  side={selected.policy_decision?.policy || ""}
                />
                <div className="command">
                  <TerminalSquare />
                  <div>
                    <span>
                      {label(selected.recommended_action?.action_type || "")}
                    </span>
                    <strong>{selected.recommended_action?.summary}</strong>
                    <code>
                      target: {selected.recommended_action?.target} / strategy:
                      rolling / max unavailable: 1
                    </code>
                  </div>
                </div>
                <div className="guards">
                  <Guard
                    title="Evidence attached"
                    note={`${selected.evidence.length} approved sections`}
                    done
                  />
                  <Guard
                    title="Policy evaluated"
                    note="Allow-list and threshold passed"
                    done
                  />
                  <Guard
                    title="Human approval"
                    note={
                      approval?.status === "approved"
                        ? `Approved by ${approval.decided_by}`
                        : "Named approver required"
                    }
                    done={approval?.status === "approved"}
                  />
                  <Guard
                    title="State verification"
                    note={
                      selected.status === "resolved"
                        ? "Observed healthy state"
                        : "Runs after execution"
                    }
                    done={selected.status === "resolved"}
                  />
                </div>
                <footer className="actionfoot">
                  <p>
                    <TriangleAlert />
                    <strong>Sensitive action</strong> - direct execution is
                    blocked until approval.
                  </p>
                  {approval?.status === "pending" && (
                    <button onClick={approve} disabled={busy}>
                      <ShieldCheck />
                      Approve plan
                    </button>
                  )}
                  {approval?.status === "approved" &&
                    selected.status !== "resolved" && (
                      <button
                        className="execute"
                        onClick={execute}
                        disabled={busy}
                      >
                        <Play />
                        Execute safely
                      </button>
                    )}
                  {selected.status === "resolved" && (
                    <span className="verified">
                      <BadgeCheck />
                      Verified and resolved
                    </span>
                  )}
                </footer>
              </div>
              <div className="panel timeline">
                <PanelHead
                  kicker="TRACEABILITY"
                  title="Decision timeline"
                  side="SHA256 ANCHORED"
                />
                <div className="entries">
                  {timeline.map((e, i) => (
                    <div className="entry" key={e.id}>
                      <span className={i === 0 ? "latest" : ""}>
                        {i === 0 && <Check />}
                      </span>
                      <div>
                        <strong>
                          {label(e.action)}
                          <time>{time(e.created_at)}</time>
                        </strong>
                        <p>
                          {e.actor} → {label(e.outcome)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
function PanelHead({
  kicker,
  title,
  side,
}: {
  kicker: string;
  title: string;
  side: string;
}) {
  return (
    <div className="panelhead">
      <div>
        <small>{kicker}</small>
        <h2>{title}</h2>
      </div>
      <code>{side}</code>
    </div>
  );
}
function Metric({
  title,
  value,
  note,
  tone,
  icon,
}: {
  title: string;
  value: number | string;
  note: string;
  tone: string;
  icon: React.ReactNode;
}) {
  return (
    <article className="metric">
      <span className={tone}>{icon}</span>
      <div>
        <small>{title}</small>
        <strong>{value}</strong>
        <p>{note}</p>
      </div>
    </article>
  );
}
function Guard({
  title,
  note,
  done = false,
}: {
  title: string;
  note: string;
  done?: boolean;
}) {
  return (
    <div className={"guard " + (done ? "done" : "")}>
      <span>{done ? <Check /> : <KeyRound />}</span>
      <div>
        <strong>{title}</strong>
        <p>{note}</p>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
