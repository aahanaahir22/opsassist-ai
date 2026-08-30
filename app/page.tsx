"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Html, Line, OrbitControls, Stars } from "@react-three/drei";
import { AnimatePresence, motion } from "framer-motion";
import * as THREE from "three";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Binary,
  BookOpen,
  Bot,
  Boxes,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleDot,
  Clock3,
  CloudCog,
  Code2,
  Download,
  Eye,
  FileSearch,
  FileText,
  Gauge,
  GitBranch,
  GitBranch as Github,
  Keyboard,
  LockKeyhole,
  Network,
  Pause,
  Play,
  Radar,
  RefreshCcw,
  RotateCcw,
  Search,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  TestTube2,
  Upload,
  Volume2,
  VolumeX,
  WandSparkles,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { toast } from "sonner";
import {
  OpsAssistApi,
  type Hypothesis as ApiHypothesis,
  type Simulation as ApiSimulation,
} from "@/lib/opsassist-api";
import { useOpsAssistAuth } from "@/app/auth-provider";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "@/components/ui/sonner";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ServiceStatus = "healthy" | "degraded" | "critical";
type ServiceNode = {
  id: string;
  name: string;
  short: string;
  position: [number, number, number];
};

const services: ServiceNode[] = [
  { id: "gateway", name: "API Gateway", short: "GW", position: [-4.5, 1.2, 0] },
  {
    id: "auth",
    name: "Authentication",
    short: "AU",
    position: [-2.4, 2.5, -0.5],
  },
  {
    id: "checkout",
    name: "Checkout Service",
    short: "CO",
    position: [-1.6, 0, 0.5],
  },
  {
    id: "payment",
    name: "Payment Service",
    short: "PY",
    position: [1.1, 1.5, 0],
  },
  {
    id: "inventory",
    name: "Inventory Service",
    short: "IN",
    position: [1.1, -1.4, -0.5],
  },
  {
    id: "postgres",
    name: "PostgreSQL",
    short: "DB",
    position: [4.2, 1.5, 0.2],
  },
  { id: "redis", name: "Redis", short: "RD", position: [3.8, -1.4, 0] },
  {
    id: "queue",
    name: "Message Queue",
    short: "MQ",
    position: [-1.3, -2.5, -0.7],
  },
  {
    id: "notify",
    name: "Notification",
    short: "NT",
    position: [-4, -1.7, -0.2],
  },
  {
    id: "provider",
    name: "Payment Provider",
    short: "EX",
    position: [4.7, 0, -1],
  },
];

const edges = [
  ["gateway", "auth"],
  ["gateway", "checkout"],
  ["checkout", "payment"],
  ["checkout", "inventory"],
  ["checkout", "postgres"],
  ["checkout", "redis"],
  ["payment", "postgres"],
  ["payment", "provider"],
  ["inventory", "postgres"],
  ["checkout", "queue"],
  ["queue", "notify"],
];

const timeline = [
  {
    time: "09:42:00",
    title: "Healthy baseline",
    detail: "Checkout p95 stable at 186 ms.",
    phase: 0,
  },
  {
    time: "09:42:14",
    title: "Change point detected",
    detail: "Latency crossed the rolling 3σ baseline.",
    phase: 1,
  },
  {
    time: "09:42:31",
    title: "Signals correlated",
    detail: "27 alerts collapsed into INC-2026-0847.",
    phase: 2,
  },
  {
    time: "09:43:08",
    title: "Evidence converged",
    detail: "Checkout pool occupancy reached 98% after deploy dpl_7f2.",
    phase: 3,
  },
  {
    time: "09:44:02",
    title: "Action simulated",
    detail: "Rollback + controlled restart predicted 91% recovery.",
    phase: 4,
  },
  {
    time: "09:45:19",
    title: "Action approved",
    detail: "Sensitive action signed by incident commander.",
    phase: 5,
  },
  {
    time: "09:46:40",
    title: "Recovery verified",
    detail: "p95 latency 204 ms; error rate 0.8% for 3 windows.",
    phase: 6,
  },
];

const metrics = [
  { t: "09:40", latency: 182, errors: 0.4, pool: 58 },
  { t: "09:41", latency: 190, errors: 0.7, pool: 63 },
  { t: "09:42", latency: 318, errors: 2.4, pool: 79 },
  { t: "09:43", latency: 892, errors: 8.8, pool: 98 },
  { t: "09:44", latency: 1240, errors: 13.2, pool: 100 },
  { t: "09:45", latency: 624, errors: 6.1, pool: 74 },
  { t: "09:46", latency: 204, errors: 0.8, pool: 61 },
];

const hypotheses = [
  {
    name: "Database pool exhaustion",
    score: 92,
    state: "leading",
    evidence: 7,
  },
  {
    name: "External provider outage",
    score: 38,
    state: "contradicted",
    evidence: 3,
  },
  {
    name: "Redis cache failure",
    score: 21,
    state: "contradicted",
    evidence: 2,
  },
  { name: "Unexpected traffic spike", score: 17, state: "weak", evidence: 2 },
];

const evidenceItems = [
  {
    id: "EV-104",
    type: "Metric",
    label: "Pool occupancy 98%",
    source: "postgres.pool.used",
    time: "09:43:01",
    reliability: 99,
    stance: "Supports",
    excerpt: "active=98, idle=0, max=100",
    why: "Saturation begins before downstream timeouts.",
  },
  {
    id: "EV-108",
    type: "Deploy",
    label: "Checkout deploy dpl_7f2",
    source: "deployment-events",
    time: "09:38:44",
    reliability: 100,
    stance: "Supports",
    excerpt: "checkout:v2.18.0 → v2.19.0",
    why: "The anomaly follows the only relevant system change.",
  },
  {
    id: "EV-113",
    type: "Trace",
    label: "DB acquire wait 711 ms",
    source: "trace/8baf1",
    time: "09:43:06",
    reliability: 96,
    stance: "Supports",
    excerpt: "db.pool.acquire 711ms; payment.call 82ms",
    why: "The trace localizes latency before the provider call.",
  },
  {
    id: "EV-119",
    type: "Log",
    label: "Timeout acquiring connection",
    source: "checkout-pod-7c9",
    time: "09:43:12",
    reliability: 94,
    stance: "Supports",
    excerpt: "sqlalchemy.exc.TimeoutError: QueuePool limit reached",
    why: "Direct application evidence matches the pool hypothesis.",
  },
  {
    id: "EV-124",
    type: "Provider",
    label: "External API nominal",
    source: "provider-health",
    time: "09:43:18",
    reliability: 91,
    stance: "Contradicts",
    excerpt: "status=200 p95=84ms availability=99.99%",
    why: "Weakens the external-provider outage hypothesis.",
  },
  {
    id: "EV-131",
    type: "Runbook",
    label: "Pool exhaustion procedure",
    source: "RB-DB-017 §4.2",
    time: "version 3.4",
    reliability: 88,
    stance: "Supports",
    excerpt:
      "Correlate pool wait time with post-deployment connection retention.",
    why: "The verified procedure matches the observed pattern.",
  },
];

const agents = [
  {
    name: "Signal Analyst",
    icon: Radar,
    task: "Change point confirmed",
    confidence: 96,
    ref: "EV-104",
  },
  {
    name: "Log Investigator",
    icon: TerminalSquare,
    task: "Pool timeout signature",
    confidence: 94,
    ref: "EV-119",
  },
  {
    name: "Trace Investigator",
    icon: GitBranch,
    task: "Wait localized to DB",
    confidence: 91,
    ref: "EV-113",
  },
  {
    name: "Runbook Researcher",
    icon: BookOpen,
    task: "Procedure RB-DB-017",
    confidence: 88,
    ref: "EV-131",
  },
  {
    name: "Risk Guardian",
    icon: ShieldCheck,
    task: "Sensitive / reversible",
    confidence: 93,
    ref: "POL-08",
  },
  {
    name: "Verification Agent",
    icon: BadgeCheck,
    task: "Awaiting execution",
    confidence: 0,
    ref: "—",
  },
];

const runbooks = [
  {
    id: "RB-DB-017",
    title: "PostgreSQL connection-pool exhaustion",
    version: "3.4",
    trust: "Verified",
    chunk: "§4.2",
    text: "If pool acquire wait rises after a deployment, compare connection retention by code version. Prefer rollback before increasing the pool ceiling.",
  },
  {
    id: "RB-SVC-022",
    title: "Controlled service restart",
    version: "2.1",
    trust: "Verified",
    chunk: "§2.6",
    text: "Drain traffic, preserve at least two healthy replicas, restart sequentially, and verify three telemetry windows before confirmation.",
  },
  {
    id: "PM-2026-011",
    title: "Historical checkout saturation",
    version: "1.0",
    trust: "Reviewed",
    chunk: "Root cause",
    text: "A session cleanup regression retained connections. Rollback reduced pool occupancy within ninety seconds.",
  },
];

const architecture = [
  {
    id: "telemetry",
    name: "Telemetry Gateway",
    icon: Activity,
    tech: "FastAPI · Pydantic · WebSockets",
    responsibility: "Validates and streams synthetic logs, metrics and traces.",
    io: "OTLP-style events → normalized telemetry",
    failure: "Backpressure and dead-letter buffering",
    security: "Schema validation · rate limits · secret redaction",
    path: "apps/api/services/telemetry",
  },
  {
    id: "intelligence",
    name: "Evidence Engine",
    icon: BrainCircuit,
    tech: "scikit-learn · NetworkX · FAISS",
    responsibility:
      "Correlates signals and ranks causal hypotheses transparently.",
    io: "Telemetry + topology → evidence graph",
    failure: "Falls back to deterministic offline analysis",
    security: "Trusted-source labels · injection scanning",
    path: "ai/models + ai/retrieval",
  },
  {
    id: "agents",
    name: "Agent Council",
    icon: Bot,
    tech: "LangGraph-style state machine",
    responsibility:
      "Coordinates specialized investigation summaries without exposing hidden reasoning.",
    io: "Evidence state → structured findings",
    failure: "Timeout isolation and partial-result recovery",
    security: "Pydantic output · tool allow-list",
    path: "ai/agents/orchestrator.py",
  },
  {
    id: "simulator",
    name: "Digital Twin",
    icon: Boxes,
    tech: "Python · NetworkX · seeded models",
    responsibility:
      "Estimates recovery, risk and blast radius before an action.",
    io: "Candidate action → counterfactual state",
    failure: "Returns uncertainty instead of invented certainty",
    security: "No production credentials · safe tools only",
    path: "simulator/engine",
  },
  {
    id: "policy",
    name: "Policy & Execution",
    icon: LockKeyhole,
    tech: "Pydantic · signed audit records",
    responsibility: "Gates sensitive actions and verifies observed outcomes.",
    io: "Approved plan → simulated executor → verification",
    failure: "Fail closed; no success without telemetry",
    security: "RBAC · idempotency · explicit approval",
    path: "apps/api/services/policy",
  },
];

function statusFor(
  id: string,
  phase: number,
  simulated = false,
): ServiceStatus {
  if (simulated || phase === 0 || phase >= 6) return "healthy";
  if (id === "checkout" || id === "postgres")
    return phase >= 2 ? "critical" : "degraded";
  if (id === "payment" || id === "queue")
    return phase >= 2 ? "degraded" : "healthy";
  return "healthy";
}

function ServiceOrb({
  service,
  status,
  selected,
  compact,
  onSelect,
}: {
  service: ServiceNode;
  status: ServiceStatus;
  selected: boolean;
  compact: boolean;
  onSelect: (id: string) => void;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const color =
    status === "healthy"
      ? "#D8FF4F"
      : status === "degraded"
        ? "#FF9B4A"
        : "#FF3D72";

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const pulse =
      status === "critical"
        ? Math.sin(clock.elapsedTime * 5) * 0.08
        : Math.sin(clock.elapsedTime * 1.8) * 0.025;
    ref.current.scale.setScalar((selected ? 1.25 : 1) + pulse);
    ref.current.rotation.y += 0.004;
  });

  return (
    <group position={service.position}>
      <mesh
        ref={ref}
        onClick={(event) => {
          event.stopPropagation();
          onSelect(service.id);
        }}
      >
        <icosahedronGeometry args={[compact ? 0.32 : 0.43, 2]} />
        <meshStandardMaterial
          color="#34145F"
          emissive={color}
          emissiveIntensity={status === "critical" ? 2.4 : 1.4}
          roughness={0.18}
          metalness={0.82}
        />
      </mesh>
      <mesh scale={selected ? 1.55 : 1.15}>
        <sphereGeometry args={[compact ? 0.34 : 0.46, 24, 24]} />
        <meshBasicMaterial
          color={color}
          transparent
          opacity={selected ? 0.12 : 0.05}
          side={THREE.BackSide}
        />
      </mesh>
      {!compact && (
        <Html
          center
          position={[0, -0.72, 0]}
          distanceFactor={10}
          style={{ pointerEvents: "none" }}
        >
          <span className={`node-label ${selected ? "selected" : ""}`}>
            {service.name}
          </span>
        </Html>
      )}
    </group>
  );
}

function Universe({
  phase,
  compact = false,
  simulated = false,
  selected,
  onSelect,
}: {
  phase: number;
  compact?: boolean;
  simulated?: boolean;
  selected: string;
  onSelect: (id: string) => void;
}) {
  const lookup = useMemo(
    () => Object.fromEntries(services.map((service) => [service.id, service])),
    [],
  );
  return (
    <Canvas
      camera={{
        position: [0, 0.2, compact ? 11.5 : 10],
        fov: compact ? 50 : 48,
      }}
      dpr={[1, 1.6]}
    >
      <color attach="background" args={["#25103F"]} />
      <fog attach="fog" args={["#25103F", 9, 17]} />
      <ambientLight intensity={0.75} />
      <pointLight position={[0, 2, 6]} intensity={26} color="#FF4F91" />
      <pointLight position={[4, -2, 3]} intensity={20} color="#A071FF" />
      <Stars
        radius={40}
        depth={18}
        count={compact ? 300 : 850}
        factor={2}
        fade
        speed={0.3}
      />
      {edges.map(([from, to]) => {
        const a = lookup[from];
        const b = lookup[to];
        const affected = [from, to].some(
          (id) => statusFor(id, phase, simulated) !== "healthy",
        );
        return (
          <Line
            key={`${from}-${to}`}
            points={[a.position, b.position]}
            color={affected ? "#FF467A" : "#B98CFF"}
            transparent
            opacity={affected ? 0.8 : 0.4}
            lineWidth={affected ? 1.8 : 0.9}
            dashed
            dashScale={affected ? 2.4 : 1.2}
            dashSize={0.18}
            gapSize={0.12}
          />
        );
      })}
      {services.map((service) => (
        <ServiceOrb
          key={service.id}
          service={service}
          status={statusFor(service.id, phase, simulated)}
          selected={selected === service.id}
          compact={compact}
          onSelect={onSelect}
        />
      ))}
      <OrbitControls
        makeDefault
        enableDamping
        dampingFactor={0.06}
        minDistance={compact ? 8 : 6}
        maxDistance={compact ? 14 : 15}
        autoRotate={compact}
        autoRotateSpeed={0.25}
      />
    </Canvas>
  );
}

function MetricChart({
  dataKey,
  color,
  unit,
}: {
  dataKey: "latency" | "errors" | "pool";
  color: string;
  unit: string;
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart
        data={metrics}
        margin={{ top: 8, right: 5, left: -26, bottom: 0 }}
      >
        <defs>
          <linearGradient id={`fill-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid
          stroke="#16304a"
          strokeDasharray="3 6"
          vertical={false}
        />
        <XAxis
          dataKey="t"
          tick={{ fill: "#718aa2", fontSize: 9 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: "#718aa2", fontSize: 9 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "#071426",
            border: "1px solid #1a3b57",
            borderRadius: 10,
            fontSize: 11,
          }}
          formatter={(value) => [`${value}${unit}`, dataKey]}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fill={`url(#fill-${dataKey})`}
          isAnimationActive
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function PanelTitle({
  eyebrow,
  title,
  action,
}: {
  eyebrow: string;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="panel-title">
      <div>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}

function ScoreBar({
  value,
  tone = "cyan",
}: {
  value: number;
  tone?: "cyan" | "emerald" | "amber" | "coral" | "violet";
}) {
  return (
    <div className="score-track">
      <span className={`score-fill ${tone}`} style={{ width: `${value}%` }} />
    </div>
  );
}

function OpsAssistApp() {
  const auth = useOpsAssistAuth();
  const api = useMemo(
    () => new OpsAssistApi(auth.getAccessToken),
    [auth.getAccessToken],
  );
  const [showEntry, setShowEntry] = useState(true);
  const [activeView, setActiveView] = useState("mission");
  const [incidentActive, setIncidentActive] = useState(false);
  const [phase, setPhase] = useState(0);
  const [selectedService, setSelectedService] = useState("checkout");
  const [replayIndex, setReplayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [investigating, setInvestigating] = useState(false);
  const [simulated, setSimulated] = useState(false);
  const [approved, setApproved] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [sound, setSound] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState<
    (typeof evidenceItems)[number] | null
  >(null);
  const [approvalDialog, setApprovalDialog] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [tourStep, setTourStep] = useState(0);
  const [logInput, setLogInput] = useState("");
  const [logAnalyzed, setLogAnalyzed] = useState(false);
  const [detectionMethod, setDetectionMethod] = useState("hybrid");
  const [runbookQuery, setRunbookQuery] = useState("connection pool timeout");
  const [architectureSelection, setArchitectureSelection] = useState(
    architecture[1],
  );
  const [backendMode, setBackendMode] = useState<
    "checking" | "connected" | "offline"
  >(api.enabled ? "checking" : "offline");
  const [incidentId, setIncidentId] = useState<string | null>(null);
  const [remoteHypotheses, setRemoteHypotheses] = useState<ApiHypothesis[]>([]);
  const [simulationResult, setSimulationResult] =
    useState<ApiSimulation | null>(null);
  const [simulationId, setSimulationId] = useState<string | null>(null);
  const [approvalId, setApprovalId] = useState<string | null>(null);
  const [postmortem, setPostmortem] = useState({
    summary:
      "Checkout latency and payment timeouts were caused by connection retention introduced in Checkout v2.19.0.",
    impact:
      "12.4% of synthetic checkout attempts failed for 4 minutes 26 seconds. No real customers or systems were affected.",
    rootCause:
      "Deployment dpl_7f2 introduced a session-cleanup regression. PostgreSQL pool occupancy reached 98%, increasing acquire wait and propagating timeouts to Payment and Queue consumers.",
    resolution:
      "Rolled Checkout back to v2.18.0 and performed a controlled restart. Recovery was confirmed across three telemetry windows.",
  });

  const visualPhase = incidentActive ? timeline[replayIndex].phase : 0;
  const selectedServiceData =
    services.find((service) => service.id === selectedService) ?? services[2];
  const leadingScore = remoteHypotheses[0]
    ? Math.round(remoteHypotheses[0].score * 100)
    : 92;
  const displayHypotheses = remoteHypotheses.length
    ? remoteHypotheses.map((item, index) => ({
        name: item.label,
        score: Math.round(item.score * 100),
        state: index === 0 ? "leading" : "contradicted",
        evidence: item.supporting_evidence_ids.length,
      }))
    : hypotheses;
  const scoreComponents = remoteHypotheses[0]
    ? [
        [
          "Temporal precedence",
          remoteHypotheses[0].components.temporal_precedence * 100,
        ],
        [
          "Trace relationship",
          remoteHypotheses[0].components.trace_relationship * 100,
        ],
        [
          "Runbook relevance",
          remoteHypotheses[0].components.runbook_relevance * 100,
        ],
        [
          "Agent agreement",
          remoteHypotheses[0].components.agent_agreement * 100,
        ],
        [
          "Contradiction penalty",
          remoteHypotheses[0].components.contradiction_penalty * 100,
        ],
      ]
    : [
        ["Temporal precedence", 96],
        ["Trace relationship", 91],
        ["Runbook relevance", 88],
        ["Agent agreement", 94],
        ["Contradiction penalty", 12],
      ];
  const recoveryPercent = simulationResult
    ? Math.round(simulationResult.estimated_recovery_probability * 100)
    : 91;

  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () =>
        setReplayIndex((current) => {
          if (current >= timeline.length - 1) {
            setPlaying(false);
            return current;
          }
          return current + 1;
        }),
      1200 / playbackSpeed,
    );
    return () => window.clearInterval(timer);
  }, [playing, playbackSpeed]);

  useEffect(() => {
    if (!api.enabled) return;
    api
      .health()
      .then(() => setBackendMode("connected"))
      .catch(() => setBackendMode("offline"));
  }, [api]);

  const tone = (frequency = 520) => {
    if (!sound || typeof window === "undefined") return;
    const AudioContextClass =
      window.AudioContext ||
      (window as typeof window & { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!AudioContextClass) return;
    const context = new AudioContextClass();
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.frequency.value = frequency;
    oscillator.type = "sine";
    gain.gain.setValueAtTime(0.03, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.18);
    oscillator.connect(gain).connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + 0.18);
  };

  const runInvestigation = async () => {
    setIncidentActive(true);
    setInvestigating(true);
    setPhase(1);
    setReplayIndex(1);
    tone(440);
    if (backendMode === "connected") {
      try {
        const launched = incidentId ? null : await api.launchScenario();
        const activeId = incidentId ?? launched?.id;
        if (!activeId) throw new Error("The incident could not be created");
        setIncidentId(activeId);
        setPhase(2);
        setReplayIndex(2);
        const investigated = await api.investigate(activeId);
        setRemoteHypotheses(investigated.hypotheses);
        setPhase(3);
        setReplayIndex(3);
        setInvestigating(false);
        toast.success(
          "Python agents returned persisted evidence and computed rankings",
        );
        tone(660);
        return;
      } catch (error) {
        setBackendMode("offline");
        toast.error(
          error instanceof Error
            ? `${error.message} — switched to offline replay`
            : "Backend unavailable — switched to offline replay",
        );
      }
    }
    window.setTimeout(() => {
      setPhase(2);
      setReplayIndex(2);
    }, 650);
    window.setTimeout(() => {
      setPhase(3);
      setReplayIndex(3);
    }, 1350);
    window.setTimeout(() => {
      setInvestigating(false);
      toast.success(
        "Offline replay loaded from the versioned Checkout scenario",
      );
      tone(660);
    }, 2100);
  };

  const launchGuided = () => {
    setShowEntry(false);
    setActiveView("mission");
    runInvestigation();
  };
  const simulateAction = async () => {
    if (phase < 3) {
      toast.error("Run the evidence investigation first");
      return;
    }
    if (backendMode === "connected" && incidentId) {
      try {
        const result = await api.simulate(incidentId);
        setSimulationResult(result);
        setSimulationId(result.id);
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : "Simulation failed",
        );
        return;
      }
    }
    setSimulated(true);
    setPhase(Math.max(phase, 4));
    setReplayIndex(4);
    tone(580);
    toast.success(
      backendMode === "connected"
        ? "Python digital-twin estimate received"
        : "Offline scenario estimate loaded",
    );
  };
  const confirmApproval = async () => {
    if (backendMode === "connected" && incidentId && simulationId) {
      try {
        const record = await api.approve(incidentId, simulationId);
        setApprovalId(record.id);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Approval failed");
        return;
      }
    }
    setApproved(true);
    setApprovalDialog(false);
    setPhase(Math.max(phase, 5));
    setReplayIndex(5);
    tone(720);
    toast.success(
      backendMode === "connected"
        ? "Backend approval signed and persisted"
        : "Offline approval replayed",
    );
  };
  const executeAction = async () => {
    if (!simulated) {
      toast.error("Simulate the action before execution");
      return;
    }
    if (!approved) {
      toast.error("Explicit approval is required");
      return;
    }
    setExecuting(true);
    tone(380);
    if (
      backendMode === "connected" &&
      incidentId &&
      simulationId &&
      approvalId
    ) {
      try {
        const execution = await api.execute(
          incidentId,
          simulationId,
          approvalId,
        );
        const verification = await api.verify(incidentId, execution.id);
        if (verification.state !== "VERIFIED")
          throw new Error("Recovery criteria did not pass");
        setExecuting(false);
        setPhase(6);
        setReplayIndex(6);
        tone(820);
        toast.success(
          `Recovery verified across ${verification.windows_observed} backend telemetry windows`,
        );
        return;
      } catch (error) {
        setExecuting(false);
        toast.error(
          error instanceof Error ? error.message : "Execution failed",
        );
        return;
      }
    }
    window.setTimeout(() => {
      setExecuting(false);
      setPhase(6);
      setReplayIndex(6);
      tone(820);
      toast.success("Offline replay reached the checked-in verification state");
    }, 1600);
  };

  const exportPostmortem = () => {
    const markdown = `# INC-2026-0847 — Checkout Cascade\n\n> Synthetic public-demo incident.\n\n## Executive summary\n${postmortem.summary}\n\n## Customer impact\n${postmortem.impact}\n\n## Root cause\n${postmortem.rootCause}\n\n## Resolution and verification\n${postmortem.resolution}\n\n## Evidence\n${evidenceItems.map((item) => `- [${item.id}] ${item.label} — ${item.source}`).join("\n")}\n`;
    const url = URL.createObjectURL(
      new Blob([markdown], { type: "text/markdown" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "INC-2026-0847-postmortem.md";
    anchor.click();
    URL.revokeObjectURL(url);
    toast.success("Postmortem exported as Markdown");
  };
  const readLogFile = async (file?: File) => {
    if (!file) return;
    setLogInput(await file.text());
    setLogAnalyzed(false);
  };
  const runbookResults = useMemo(() => {
    const terms = runbookQuery.toLowerCase().split(/\s+/).filter(Boolean);
    return runbooks
      .map((doc) => ({
        ...doc,
        score: terms.reduce(
          (score, term) =>
            score +
            (`${doc.title} ${doc.text}`.toLowerCase().includes(term) ? 1 : 0),
          0,
        ),
      }))
      .sort((a, b) => b.score - a.score);
  }, [runbookQuery]);

  const tour = [
    {
      view: "mission",
      title: "1 · Signal chaos becomes one incident",
      text: "27 synthetic alerts are correlated into a single checkout cascade with a live dependency view.",
    },
    {
      view: "incident",
      title: "2 · Specialized agents challenge hypotheses",
      text: "Structured findings converge on one ranked cause, with confidence decomposed into evidence-backed factors.",
    },
    {
      view: "evidence",
      title: "3 · Every claim opens its source",
      text: "Metrics, traces, logs, deploys and runbook chunks support or contradict each hypothesis.",
    },
    {
      view: "twin",
      title: "4 · Simulate before touching the system",
      text: "A counterfactual twin estimates recovery, blast radius, downtime and rollback feasibility.",
    },
    {
      view: "evaluation",
      title: "5 · Finish with reproducible proof",
      text: "Non-perfect evaluation results and transparent limitations keep the project technically credible.",
    },
    {
      view: "architecture",
      title: "6 · Inspect how the system is engineered",
      text: "Each component explains its responsibility, failure behavior, security controls and source location.",
    },
  ];
  const advanceTour = () => {
    const next = tourStep + 1;
    if (next >= tour.length) {
      setTourOpen(false);
      setTourStep(0);
      return;
    }
    setTourStep(next);
    setActiveView(tour[next].view);
  };

  return (
    <div className={`ops-shell ${reducedMotion ? "reduce-ops-motion" : ""}`}>
      <Toaster position="bottom-right" theme="dark" />
      {showEntry && (
          <motion.section
            className="entry-screen"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="entry-canvas">
              <Universe
                phase={1}
                selected="checkout"
                onSelect={setSelectedService}
              />
            </div>
            <div className="entry-vignette" />
            <motion.div
              className="entry-copy"
              initial={{ y: 24, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="brand-lockup">
                <span className="brand-mark">
                  <BrainCircuit />
                </span>
                <span>
                  OPSASSIST <b>AI</b>
                </span>
              </div>
              <Badge className="synthetic-badge">
                <TestTube2 />{" "}
                {backendMode === "connected"
                  ? "Live Python backend · synthetic telemetry"
                  : backendMode === "checking"
                    ? "Connecting to Python backend"
                    : "Offline replay · synthetic telemetry"}
              </Badge>
              <h1>
                Turn signal chaos into
                <br />
                <em>verified action.</em>
              </h1>
              <p>
                Evidence-backed autonomous incident intelligence with a 3D
                service universe, agent council, causal evidence and a safe
                counterfactual twin.
              </p>
              <div className="entry-actions">
                <Button
                  size="lg"
                  className="primary-action"
                  onClick={launchGuided}
                >
                  <Play /> Launch guided incident
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="ghost-action"
                  onClick={() => setShowEntry(false)}
                >
                  Enter Ops Universe <ArrowRight />
                </Button>
              </div>
              <div className="entry-preferences">
                <label>
                  <Switch checked={sound} onCheckedChange={setSound} />
                  {sound ? <Volume2 /> : <VolumeX />} Sound
                </label>
                <label>
                  <Switch
                    checked={reducedMotion}
                    onCheckedChange={setReducedMotion}
                  />
                  <Eye /> Reduced motion
                </label>
                <button onClick={() => setShowEntry(false)}>
                  Fast skip <ChevronRight />
                </button>
              </div>
            </motion.div>
            <div className="entry-system-line">
              <span>10 services</span>
              <span>11 evidence agents</span>
              <span>safe simulator</span>
              <span>
                {backendMode === "connected"
                  ? "PostgreSQL connected"
                  : "offline ready"}
              </span>
            </div>
          </motion.section>
      )}

      <header className="topbar">
        <button
          className="brand-lockup compact"
          onClick={() => setShowEntry(true)}
          aria-label="Open OpsAssist entry"
        >
          <span className="brand-mark">
            <BrainCircuit />
          </span>
          <span>
            OPSASSIST <b>AI</b>
          </span>
        </button>
        <div className="environment-pill">
          <span
            className={
              incidentActive && phase < 6 ? "live-dot critical" : "live-dot"
            }
          />{" "}
          DEMO-EU-1{" "}
          <b>{incidentActive && phase < 6 ? "INCIDENT" : "HEALTHY"}</b>
        </div>
        <div className="topbar-actions">
          <Badge className="synthetic-badge desktop-only">
            <TestTube2 />{" "}
            {backendMode === "connected"
              ? "Python API connected"
              : backendMode === "checking"
                ? "Checking Python API"
                : "Offline synthetic replay"}
          </Badge>
          {auth.configured && (
            <Button
              variant="outline"
              size="sm"
              onClick={() =>
                void (auth.authenticated ? auth.logout() : auth.login())
              }
            >
              {auth.authenticated ? auth.name : "Sign in with SSO"}
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            className="tour-button"
            onClick={() => {
              setTourStep(0);
              setActiveView(tour[0].view);
              setTourOpen(true);
            }}
          >
            <WandSparkles /> Five-minute technical tour
          </Button>
          <button
            className="icon-button"
            onClick={() => setSound(!sound)}
            aria-label="Toggle interface sound"
          >
            {sound ? <Volume2 /> : <VolumeX />}
          </button>
        </div>
      </header>

      <Tabs
        value={activeView}
        onValueChange={setActiveView}
        className="workspace-tabs"
      >
        <TabsList
          variant="line"
          className="workspace-nav"
          aria-label="OpsAssist workspaces"
        >
          <TabsTrigger value="mission">
            <Gauge /> Mission
          </TabsTrigger>
          <TabsTrigger value="lab">
            <TestTube2 /> Lab
          </TabsTrigger>
          <TabsTrigger value="incident">
            <AlertTriangle /> Incident
          </TabsTrigger>
          <TabsTrigger value="evidence">
            <Network /> Evidence
          </TabsTrigger>
          <TabsTrigger value="twin">
            <Boxes /> Digital twin
          </TabsTrigger>
          <TabsTrigger value="knowledge">
            <BookOpen /> Runbooks
          </TabsTrigger>
          <TabsTrigger value="evaluation">
            <Activity /> Evaluation
          </TabsTrigger>
          <TabsTrigger value="postmortem">
            <FileText /> Postmortem
          </TabsTrigger>
          <TabsTrigger value="architecture">
            <Binary /> Architecture
          </TabsTrigger>
        </TabsList>

        <main className="workspace-main">
          <TabsContent value="mission" className="view-stack">
            <section className="mission-grid">
              <div className="universe-panel glass-panel">
                <PanelTitle
                  eyebrow="Live dependency graph"
                  title="Ops Universe"
                  action={
                    <div className="topology-mode">
                      <button className="active">Topology</button>
                      <button onClick={() => setActiveView("evidence")}>
                        Causal
                      </button>
                    </div>
                  }
                />
                <div className="universe-canvas">
                  <Universe
                    phase={visualPhase}
                    selected={selectedService}
                    onSelect={setSelectedService}
                  />
                </div>
                <div className="universe-overlay left">
                  <span>SELECTED SERVICE</span>
                  <strong>{selectedServiceData.name}</strong>
                  <div>
                    <i className={statusFor(selectedService, visualPhase)} />
                    {statusFor(selectedService, visualPhase)} ·{" "}
                    {selectedService === "checkout"
                      ? "p95 1,240 ms"
                      : "telemetry linked"}
                  </div>
                </div>
                <div className="universe-overlay right">
                  <span>DRAG TO ORBIT</span>
                  <span>SCROLL TO ZOOM</span>
                </div>
              </div>
              <aside className="incident-rail glass-panel">
                <div className="rail-kicker">
                  <span className="live-dot critical" /> ACTIVE INCIDENT
                </div>
                <h2>Checkout cascade</h2>
                <p>
                  Database connection-pool exhaustion propagating into Payment
                  and Queue consumers.
                </p>
                <div className="incident-id">
                  <code>{incidentId ?? "INC-2026-0847"}</code>
                  <Badge>SEV-1</Badge>
                </div>
                <div className="confidence-orbit">
                  <svg viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="48" />
                    <circle
                      className="value"
                      cx="60"
                      cy="60"
                      r="48"
                      pathLength="100"
                      strokeDasharray={`${phase >= 3 ? leadingScore : 0} 100`}
                    />
                  </svg>
                  <div>
                    <b>{phase >= 3 ? leadingScore : 0}%</b>
                    <span>
                      computed root-cause
                      <br />
                      confidence
                    </span>
                  </div>
                </div>
                <div className="rail-evidence">
                  <span>
                    <FileSearch />{" "}
                    {phase >= 3
                      ? (remoteHypotheses[0]?.supporting_evidence_ids.length ??
                        7)
                      : 0}{" "}
                    supporting
                  </span>
                  <span>
                    <GitBranch />{" "}
                    {phase >= 3
                      ? (remoteHypotheses[0]?.contradicting_evidence_ids
                          .length ?? 2)
                      : 0}{" "}
                    contradicting
                  </span>
                </div>
                <Button
                  className="primary-action full"
                  onClick={() => {
                    setActiveView("incident");
                    void runInvestigation();
                  }}
                  disabled={investigating}
                >
                  {investigating ? (
                    <RefreshCcw className="spin" />
                  ) : (
                    <BrainCircuit />
                  )}
                  {investigating
                    ? "Agents investigating…"
                    : phase >= 3
                      ? "Re-run investigation"
                      : "Investigate incident"}
                </Button>
                <button
                  className="text-action"
                  onClick={() => setActiveView("evidence")}
                >
                  Inspect evidence constellation <ArrowRight />
                </button>
              </aside>
            </section>
            <section className="metric-strip">
              <article>
                <span>Checkout p95</span>
                <strong className="coral">
                  {visualPhase > 0 && visualPhase < 6 ? "1,240" : "186"} ms
                </strong>
                <small>
                  {visualPhase > 0 && visualPhase < 6
                    ? "+566% vs baseline"
                    : "within SLO"}
                </small>
                <div className="mini-chart">
                  <MetricChart dataKey="latency" color="#ff4567" unit="ms" />
                </div>
              </article>
              <article>
                <span>Error rate</span>
                <strong className="amber">
                  {visualPhase > 1 && visualPhase < 6 ? "13.2" : "0.4"}%
                </strong>
                <small>5-minute window</small>
                <div className="mini-chart">
                  <MetricChart dataKey="errors" color="#ffb547" unit="%" />
                </div>
              </article>
              <article>
                <span>DB pool</span>
                <strong className="violet">
                  {visualPhase > 1 && visualPhase < 6 ? "98" : "58"}%
                </strong>
                <small>98 / 100 active</small>
                <div className="mini-chart">
                  <MetricChart dataKey="pool" color="#8b5cff" unit="%" />
                </div>
              </article>
              <article className="decision-card">
                <span>AI decision</span>
                <div className="decision-icon">
                  <ShieldCheck />
                </div>
                <strong>
                  {phase >= 4 ? "Simulation ready" : "Evidence required"}
                </strong>
                <small>
                  {phase >= 4
                    ? "No production action executed"
                    : "Read-only investigation"}
                </small>
              </article>
            </section>
            <section className="timeline-panel glass-panel">
              <PanelTitle
                eyebrow="Synchronized replay"
                title="Incident Time Machine"
                action={
                  <div className="playback-controls">
                    <button
                      onClick={() => setPlaying(!playing)}
                      aria-label={playing ? "Pause incident replay" : "Play incident replay"}
                    >
                      {playing ? <Pause /> : <Play />}
                    </button>
                    <Select
                      value={String(playbackSpeed)}
                      onValueChange={(value) => setPlaybackSpeed(Number(value))}
                    >
                      <SelectTrigger
                        className="speed-trigger"
                        aria-label="Playback speed"
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1×</SelectItem>
                        <SelectItem value="2">2×</SelectItem>
                        <SelectItem value="4">4×</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                }
              />
              <Slider
                value={[replayIndex]}
                min={0}
                max={timeline.length - 1}
                step={1}
                onValueChange={([value]) => setReplayIndex(value)}
                aria-label="Incident replay time"
                className="timeline-slider"
              />
              <div className="timeline-events">
                {timeline.map((event, index) => (
                  <button
                    key={event.time}
                    className={index === replayIndex ? "active" : ""}
                    onClick={() => setReplayIndex(index)}
                  >
                    <i />
                    <span>{event.time}</span>
                    <strong>{event.title}</strong>
                  </button>
                ))}
              </div>
              <div className="timeline-detail">
                <Clock3 />
                <div>
                  <span>{timeline[replayIndex].time}</span>
                  <strong>{timeline[replayIndex].title}</strong>
                  <p>{timeline[replayIndex].detail}</p>
                </div>
                <Badge>
                  {replayIndex < 4
                    ? "Observed"
                    : replayIndex < 6
                      ? "Decision"
                      : "Verified"}
                </Badge>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="lab" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <TestTube2 /> Controlled input
                </Badge>
                <h1>Incident Lab</h1>
                <p>
                  Analyze your own sample or launch a reproducible synthetic
                  failure. Processing stays in this browser for the public demo.
                </p>
              </div>
              <Button
                className="primary-action"
                onClick={() => {
                  setLogInput(
                    "2026-08-29T09:43:12Z ERROR checkout-pod-7c9 sqlalchemy.exc.TimeoutError: QueuePool limit of size 100 reached\n2026-08-29T09:43:13Z WARN payment trace=8baf1 upstream timeout checkout\n2026-08-29T09:43:14Z METRIC postgres.pool.used=98 postgres.pool.idle=0",
                  );
                  setLogAnalyzed(false);
                }}
              >
                <Sparkles /> Load checkout cascade
              </Button>
            </section>
            <section className="lab-layout">
              <div className="log-console glass-panel">
                <div className="console-toolbar">
                  <div className="window-dots">
                    <i />
                    <i />
                    <i />
                  </div>
                  <span>telemetry-input.log</span>
                  <label className="upload-control">
                    <Upload /> Upload .log
                    <input
                      type="file"
                      accept=".log,.txt,.json"
                      onChange={(event) => readLogFile(event.target.files?.[0])}
                    />
                  </label>
                </div>
                <textarea
                  value={logInput}
                  onChange={(event) => {
                    setLogInput(event.target.value);
                    setLogAnalyzed(false);
                  }}
                  placeholder="Paste logs, metric events or JSON telemetry here…"
                  aria-label="Telemetry input"
                />
                <div className="console-footer">
                  <span>
                    {logInput ? logInput.split("\n").length : 0} events ·
                    secrets auto-redacted
                  </span>
                  <button onClick={() => setLogInput("")}>Clear</button>
                </div>
              </div>
              <aside className="analysis-config glass-panel">
                <PanelTitle eyebrow="Pipeline" title="Analysis configuration" />
                <label>
                  Detection strategy
                  <Select
                    value={detectionMethod}
                    onValueChange={setDetectionMethod}
                  >
                    <SelectTrigger
                      className="wide-select"
                      aria-label="Detection strategy"
                    >
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="hybrid">
                        Hybrid: z-score + change point
                      </SelectItem>
                      <SelectItem value="isolation">
                        Isolation Forest
                      </SelectItem>
                      <SelectItem value="rate">Rate of change</SelectItem>
                    </SelectContent>
                  </Select>
                </label>
                <div className="config-row">
                  <span>Correlation window</span>
                  <b>90 seconds</b>
                </div>
                <div className="config-row">
                  <span>Minimum severity</span>
                  <b>Warning</b>
                </div>
                <div className="config-row">
                  <span>Execution policy</span>
                  <b>Read-only</b>
                </div>
                <Button
                  className="primary-action full"
                  disabled={!logInput.trim()}
                  onClick={() => {
                    setLogAnalyzed(true);
                    toast.success(
                      "3 anomalies correlated into one incident candidate",
                    );
                  }}
                >
                  <Radar /> Analyze telemetry
                </Button>
              </aside>
            </section>
            <AnimatePresence>
              {logAnalyzed && (
                <motion.section
                  className="analysis-result glass-panel"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  <div className="result-signal">
                    <span>ANOMALY CLUSTER</span>
                    <strong>Connection saturation signature</strong>
                    <p>
                      Three events share temporal proximity, Checkout dependency
                      distance and the same database resource.
                    </p>
                  </div>
                  <div>
                    <span className="result-value">0.91</span>
                    <small>cluster confidence</small>
                  </div>
                  <div>
                    <span className="result-value coral">3.8σ</span>
                    <small>baseline deviation</small>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setActiveView("incident");
                      runInvestigation();
                    }}
                  >
                    Open investigation <ArrowRight />
                  </Button>
                </motion.section>
              )}
            </AnimatePresence>
          </TabsContent>

          <TabsContent value="incident" className="view-stack">
            <section className="incident-heading">
              <div>
                <div className="incident-title-line">
                  <Badge className="critical-badge">SEV-1</Badge>
                  <code>INC-2026-0847</code>
                  <span className="live-dot critical" />{" "}
                  {phase >= 6 ? "RECOVERED" : "ACTIVE"}
                </div>
                <h1>Checkout Cascade</h1>
                <p>
                  Connection-pool exhaustion · detected 09:42:14 · synthetic
                  scenario
                </p>
              </div>
              <div className="incident-actions">
                <Button variant="outline" onClick={() => setReplayIndex(0)}>
                  <RotateCcw /> Replay
                </Button>
                <Button
                  className="primary-action"
                  onClick={runInvestigation}
                  disabled={investigating}
                >
                  {investigating ? (
                    <RefreshCcw className="spin" />
                  ) : (
                    <BrainCircuit />
                  )}
                  {investigating ? "Investigating…" : "Run agent council"}
                </Button>
              </div>
            </section>
            <section className="phase-rail">
              {[
                "Detected",
                "Correlated",
                "Investigated",
                "Simulated",
                "Approved",
                "Verified",
              ].map((label, index) => {
                const threshold = [1, 2, 3, 4, 5, 6][index];
                return (
                  <div
                    className={
                      phase >= threshold
                        ? "done"
                        : phase + 1 === threshold
                          ? "current"
                          : ""
                    }
                    key={label}
                  >
                    <i>{phase >= threshold ? <Check /> : index + 1}</i>
                    <span>{label}</span>
                  </div>
                );
              })}
            </section>
            <section className="investigation-layout">
              <div className="agent-council glass-panel">
                <PanelTitle
                  eyebrow="Structured findings · no hidden chain-of-thought"
                  title="Agent Council"
                  action={
                    <Badge
                      className={
                        investigating ? "running-badge" : "ready-badge"
                      }
                    >
                      {investigating
                        ? "Investigating"
                        : phase >= 3
                          ? "Converged"
                          : "Ready"}
                    </Badge>
                  }
                />
                <div className="council-core">
                  <div className="core-rings">
                    <i />
                    <i />
                    <span>
                      <BrainCircuit />
                      <b>{phase >= 3 ? "92%" : "—"}</b>
                    </span>
                  </div>
                  <p>shared incident state</p>
                </div>
                <div className="agent-list">
                  {agents.map((agent, index) => {
                    const Icon = agent.icon;
                    const ready = phase >= 3 && index < 5;
                    return (
                      <article
                        key={agent.name}
                        className={ready ? "active" : ""}
                      >
                        <div className="agent-icon">
                          <Icon />
                        </div>
                        <div>
                          <span>{agent.name}</span>
                          <strong>
                            {ready
                              ? agent.task
                              : index === 5 && phase >= 6
                                ? "Recovery confirmed"
                                : "Awaiting evidence"}
                          </strong>
                          <small>
                            {ready
                              ? `${agent.ref} · ${agent.confidence}% confidence`
                              : "queued"}
                          </small>
                        </div>
                        <i className="agent-state">
                          {ready || (index === 5 && phase >= 6) ? (
                            <Check />
                          ) : (
                            <CircleDot />
                          )}
                        </i>
                      </article>
                    );
                  })}
                </div>
              </div>
              <div className="hypothesis-panel glass-panel">
                <PanelTitle
                  eyebrow="Transparent causal scoring"
                  title="Root-cause hypotheses"
                  action={
                    <button
                      className="text-action"
                      onClick={() => setActiveView("evidence")}
                    >
                      Graph view <Network />
                    </button>
                  }
                />
                <div className="hypothesis-list">
                  {displayHypotheses.map((hypothesis, index) => (
                    <article
                      key={hypothesis.name}
                      className={index === 0 && phase >= 3 ? "leading" : ""}
                    >
                      <div className="rank">0{index + 1}</div>
                      <div className="hypothesis-copy">
                        <div>
                          <strong>{hypothesis.name}</strong>
                          <Badge>
                            {phase >= 3 ? hypothesis.state : "pending"}
                          </Badge>
                        </div>
                        <ScoreBar
                          value={phase >= 3 ? hypothesis.score : 5}
                          tone={
                            index === 0
                              ? "cyan"
                              : index === 1
                                ? "amber"
                                : "violet"
                          }
                        />
                        <small>
                          {phase >= 3
                            ? `${hypothesis.evidence} linked evidence objects`
                            : "Awaiting agent findings"}
                        </small>
                      </div>
                      <b>{phase >= 3 ? hypothesis.score : 0}%</b>
                    </article>
                  ))}
                </div>
                <div className="score-decomposition">
                  <h3>Why the leading hypothesis ranks first</h3>
                  <div>
                    {scoreComponents.map(([label, value]) => (
                      <div key={String(label)}>
                        <span>{label}</span>
                        <ScoreBar
                          value={Number(value)}
                          tone={
                            label === "Contradiction penalty"
                              ? "coral"
                              : "emerald"
                          }
                        />
                        <b>{value}</b>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>
            <section className="recommendation-strip">
              <div className="recommendation-icon">
                <ShieldCheck />
              </div>
              <div>
                <span>RECOMMENDED REMEDIATION</span>
                <h3>Rollback Checkout v2.19.0, then controlled restart</h3>
                <p>
                  Reversible · estimated 2m 20s · requires Incident Commander
                  approval
                </p>
              </div>
              <Button
                className="primary-action"
                onClick={() => setActiveView("twin")}
              >
                Open Risk Glass & simulate <ArrowRight />
              </Button>
            </section>
          </TabsContent>

          <TabsContent value="evidence" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <Network /> Causal provenance
                </Badge>
                <h1>Evidence Constellation</h1>
                <p>
                  The leading hypothesis is surrounded by exact supporting and
                  contradicting observations. Select any evidence object to
                  inspect its provenance.
                </p>
              </div>
              <div className="evidence-legend">
                <span>
                  <i className="support" /> Supports
                </span>
                <span>
                  <i className="contradict" /> Contradicts
                </span>
              </div>
            </section>
            <section className="constellation glass-panel">
              <svg
                className="constellation-lines"
                viewBox="0 0 1000 600"
                preserveAspectRatio="none"
              >
                {[
                  [500, 300, 180, 100],
                  [500, 300, 790, 110],
                  [500, 300, 170, 430],
                  [500, 300, 820, 430],
                  [500, 300, 500, 65],
                  [500, 300, 500, 540],
                ].map((coords, index) => (
                  <line
                    key={index}
                    x1={coords[0]}
                    y1={coords[1]}
                    x2={coords[2]}
                    y2={coords[3]}
                    className={index === 3 ? "contradict" : "support"}
                  />
                ))}
              </svg>
              <div className="hypothesis-core">
                <span>LEADING HYPOTHESIS</span>
                <BrainCircuit />
                <strong>
                  Database pool
                  <br />
                  exhaustion
                </strong>
                <b>92%</b>
              </div>
              {evidenceItems.map((item, index) => {
                const positions = ["p1", "p2", "p3", "p4", "p5", "p6"];
                return (
                  <button
                    key={item.id}
                    className={`evidence-node ${positions[index]} ${item.stance === "Contradicts" ? "contradict" : "support"}`}
                    onClick={() => setEvidenceOpen(item)}
                  >
                    <span>{item.type}</span>
                    <strong>{item.label}</strong>
                    <code>{item.id}</code>
                    <i>{item.reliability}%</i>
                  </button>
                );
              })}
              <div className="constellation-note">
                <Keyboard /> Select a node to open source evidence
              </div>
            </section>
          </TabsContent>

          <TabsContent value="twin" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <Boxes /> Counterfactual simulator
                </Badge>
                <h1>Digital Twin</h1>
                <p>
                  Compare the observed production state with a seeded
                  counterfactual estimate. Simulation is not a guarantee.
                </p>
              </div>
              <Badge className="estimate-badge">ESTIMATED · NOT EXECUTED</Badge>
            </section>
            <section className="twin-grid">
              <div className="twin-universe glass-panel">
                <div className="twin-label">
                  <span>CURRENT OBSERVED STATE</span>
                  <b className="coral">Degraded</b>
                </div>
                <div className="twin-canvas">
                  <Universe
                    phase={3}
                    compact
                    selected={selectedService}
                    onSelect={setSelectedService}
                  />
                </div>
                <div className="twin-stats">
                  <span>
                    p95 <b>1,240 ms</b>
                  </span>
                  <span>
                    errors <b>13.2%</b>
                  </span>
                  <span>
                    pool <b>98%</b>
                  </span>
                </div>
              </div>
              <div className="twin-arrow">
                <Zap />
                <span>SIMULATE</span>
              </div>
              <div
                className={`twin-universe glass-panel ${simulated ? "simulated" : "pending"}`}
              >
                <div className="twin-label">
                  <span>COUNTERFACTUAL STATE</span>
                  <b className={simulated ? "emerald" : "muted"}>
                    {simulated ? "Likely recovered" : "Awaiting model"}
                  </b>
                </div>
                <div className="twin-canvas">
                  <Universe
                    phase={simulated ? 6 : 3}
                    compact
                    simulated={simulated}
                    selected={selectedService}
                    onSelect={setSelectedService}
                  />
                </div>
                <div className="twin-stats">
                  <span>
                    p95 <b>{simulated ? "212 ms" : "—"}</b>
                  </span>
                  <span>
                    errors <b>{simulated ? "0.9%" : "—"}</b>
                  </span>
                  <span>
                    pool <b>{simulated ? "62%" : "—"}</b>
                  </span>
                </div>
              </div>
            </section>
            <section className="simulation-console glass-panel">
              <div className="simulation-plan">
                <PanelTitle
                  eyebrow="Candidate action"
                  title="Rollback + controlled restart"
                />
                <div className="action-code">
                  <code>
                    rollback(service=&quot;checkout&quot;,
                    target=&quot;v2.18.0&quot;)
                  </code>
                  <code>
                    restart(strategy=&quot;rolling&quot;, min_healthy=2)
                  </code>
                </div>
                <Button className="primary-action" onClick={simulateAction}>
                  <Sparkles />{" "}
                  {simulated ? "Re-run simulation" : "Simulate action"}
                </Button>
              </div>
              <div className="prediction-grid">
                <div>
                  <span>Recovery probability</span>
                  <strong>{simulated ? `${recoveryPercent}%` : "—"}</strong>
                  <ScoreBar value={simulated ? recoveryPercent : 0} tone="emerald" />
                </div>
                <div>
                  <span>Expected downtime</span>
                  <strong>{simulated ? "2m 20s" : "—"}</strong>
                  <small>± 44 seconds</small>
                </div>
                <div>
                  <span>Blast radius</span>
                  <strong>{simulated ? "3 services" : "—"}</strong>
                  <small>Checkout, Payment, Queue</small>
                </div>
                <div>
                  <span>Rollback feasibility</span>
                  <strong>{simulated ? "High" : "—"}</strong>
                  <small>Artifact verified</small>
                </div>
              </div>
            </section>
            <section className="risk-glass">
              <div className="risk-header">
                <div className="risk-icon">
                  <LockKeyhole />
                </div>
                <div>
                  <span>RISK GLASS</span>
                  <h2>Sensitive action · explicit approval required</h2>
                  <p>
                    Scope is allow-listed. No destructive production integration
                    exists in this demo.
                  </p>
                </div>
                <Badge className="amber-badge">MEDIUM RISK</Badge>
              </div>
              <div className="risk-grid">
                <div>
                  <span>Preconditions</span>
                  <ul>
                    <li>
                      <Check /> Simulation complete
                    </li>
                    <li>
                      <Check /> Rollback artifact verified
                    </li>
                    <li>
                      <Check /> Two healthy replicas available
                    </li>
                  </ul>
                </div>
                <div>
                  <span>Rollback plan</span>
                  <p>
                    Redeploy v2.19.0 only if the prior version introduces
                    regression; stop automatically if healthy replicas fall
                    below two.
                  </p>
                </div>
                <div>
                  <span>Evidence basis</span>
                  <p>
                    <code>EV-104</code> <code>EV-108</code> <code>EV-113</code>{" "}
                    <code>RB-DB-017</code>
                  </p>
                </div>
              </div>
              <div className="approval-bar">
                <div>
                  <i className={approved ? "approved" : ""}>
                    {approved ? <Check /> : <LockKeyhole />}
                  </i>
                  <div>
                    <strong>
                      {approved
                        ? "Approved by Incident Commander"
                        : "Awaiting Incident Commander"}
                    </strong>
                    <span>
                      {approved
                        ? "Signed local-demo record · 09:45:19"
                        : "Action remains blocked"}
                    </span>
                  </div>
                </div>
                <div>
                  <Button
                    variant="outline"
                    disabled={!simulated || approved}
                    onClick={() => setApprovalDialog(true)}
                  >
                    {approved ? <Check /> : <ShieldCheck />}
                    {approved ? "Approved" : "Review & approve"}
                  </Button>
                  <Button
                    className="execute-action"
                    disabled={!approved || executing || phase >= 6}
                    onClick={executeAction}
                  >
                    {executing ? (
                      <RefreshCcw className="spin" />
                    ) : phase >= 6 ? (
                      <BadgeCheck />
                    ) : (
                      <Zap />
                    )}
                    {executing
                      ? "Executing safely…"
                      : phase >= 6
                        ? "Recovery verified"
                        : "Execute in simulator"}
                  </Button>
                </div>
              </div>
            </section>
          </TabsContent>

          <TabsContent value="knowledge" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <BookOpen /> FAISS-style local retrieval
                </Badge>
                <h1>Runbook Intelligence</h1>
                <p>
                  Search versioned operational knowledge with transparent chunk
                  IDs, metadata filters and retrieval scores.
                </p>
              </div>
              <Badge className="ready-badge">
                <Check /> 18 chunks indexed
              </Badge>
            </section>
            <section className="knowledge-search glass-panel">
              <Search />
              <input
                value={runbookQuery}
                onChange={(event) => setRunbookQuery(event.target.value)}
                placeholder="Search runbooks and historical incidents…"
                aria-label="Search runbooks"
              />
              <kbd>Local index</kbd>
            </section>
            <section className="knowledge-layout">
              <div className="retrieval-results">
                {runbookResults.map((doc, index) => (
                  <article className="runbook-result glass-panel" key={doc.id}>
                    <div className="result-rank">0{index + 1}</div>
                    <div className="runbook-copy">
                      <div>
                        <Badge>{doc.trust}</Badge>
                        <code>
                          {doc.id} · v{doc.version} · {doc.chunk}
                        </code>
                      </div>
                      <h3>{doc.title}</h3>
                      <p>{doc.text}</p>
                      <div className="retrieval-score">
                        <ScoreBar
                          value={Math.max(38, 93 - index * 17)}
                          tone={index === 0 ? "cyan" : "violet"}
                        />
                        <span>{(0.93 - index * 0.17).toFixed(2)} cosine</span>
                      </div>
                    </div>
                    <button
                      onClick={() =>
                        toast.info(`${doc.id} source viewer opened`)
                      }
                      aria-label={`Open ${doc.title}`}
                    >
                      <ArrowRight />
                    </button>
                  </article>
                ))}
              </div>
              <aside className="index-health glass-panel">
                <PanelTitle eyebrow="Index status" title="ops-knowledge-v4" />
                <div className="index-orbit">
                  <CloudCog />
                  <strong>18</strong>
                  <span>chunks</span>
                </div>
                <dl>
                  <div>
                    <dt>Embedding model</dt>
                    <dd>all-MiniLM-L6-v2</dd>
                  </div>
                  <div>
                    <dt>Documents</dt>
                    <dd>7 versioned</dd>
                  </div>
                  <div>
                    <dt>Last evaluation</dt>
                    <dd>MRR 0.83</dd>
                  </div>
                  <div>
                    <dt>Trust filter</dt>
                    <dd>Verified + reviewed</dd>
                  </div>
                </dl>
                <div className="security-note">
                  <ShieldCheck />
                  <p>
                    <b>Injection scan passed</b>
                    <br />
                    Retrieved text is treated as untrusted data, never as
                    instructions.
                  </p>
                </div>
              </aside>
            </section>
          </TabsContent>

          <TabsContent value="evaluation" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <Activity /> Reproducible benchmark
                </Badge>
                <h1>Evaluation Laboratory</h1>
                <p>
                  Seeded results from five synthetic scenarios. Scores are
                  intentionally non-perfect and show the limits of the
                  prototype.
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  toast.success(
                    "Evaluation recomputed from seeded scenario outputs",
                  )
                }
              >
                <RefreshCcw /> Recompute
              </Button>
            </section>
            <section className="evaluation-hero glass-panel">
              <div>
                <span>END-TO-END TASK SUCCESS</span>
                <strong>82%</strong>
                <p>
                  41 / 50 scenario runs reached verified recovery without a
                  policy violation.
                </p>
              </div>
              <div className="eval-wave">
                <svg viewBox="0 0 500 130">
                  <path d="M0 98 C60 92 72 40 130 62 S220 118 270 55 S370 20 500 28" />
                  <path
                    className="ghost"
                    d="M0 111 C80 101 92 82 145 91 S235 94 300 70 S410 60 500 50"
                  />
                </svg>
              </div>
              <div className="guarded-result">
                <ShieldCheck />
                <strong>0 prohibited actions</strong>
                <span>
                  Guarded execution blocked all 12 injected unsafe plans
                </span>
              </div>
            </section>
            <section className="eval-grid">
              {[
                ["Anomaly precision", "85%", "17 TP · 3 FP", "cyan"],
                ["Anomaly recall", "85%", "17 TP · 3 FN", "emerald"],
                ["Root cause Top-1", "80%", "4 / 5 scenarios", "violet"],
                ["Root cause Top-3", "100%", "5 / 5 scenarios", "cyan"],
                ["Citation coverage", "91%", "41 / 45 claims", "emerald"],
                ["Mean diagnosis time", "18.4s", "offline demo", "amber"],
              ].map(([label, value, note, toneName]) => (
                <article className="eval-card" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <ScoreBar
                    value={
                      label === "Mean diagnosis time"
                        ? 74
                        : Number(String(value).replace("%", ""))
                    }
                    tone={toneName as "cyan" | "emerald" | "violet" | "amber"}
                  />
                  <small>{note}</small>
                </article>
              ))}
            </section>
            <section className="ablation-table glass-panel">
              <PanelTitle
                eyebrow="Safety ablation"
                title="Guarded vs direct execution"
              />
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Mode</th>
                      <th>Task success</th>
                      <th>Unsafe plans blocked</th>
                      <th>False confirmations</th>
                      <th>p50 latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>
                        <ShieldCheck /> Guarded execution
                      </td>
                      <td className="emerald">82%</td>
                      <td>12 / 12</td>
                      <td>0</td>
                      <td>2.8s</td>
                    </tr>
                    <tr>
                      <td>
                        <Zap /> Direct execution
                      </td>
                      <td>86%</td>
                      <td className="coral">0 / 12</td>
                      <td className="coral">3</td>
                      <td>1.9s</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="table-note">
                Guarding adds 0.9 seconds median latency but eliminates unsafe
                plans and unverified success claims in this seeded evaluation.
              </p>
            </section>
          </TabsContent>

          <TabsContent value="postmortem" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <FileText /> Living document
                </Badge>
                <h1>Postmortem Studio</h1>
                <p>
                  Editable conclusions remain linked to observed evidence.
                  AI-authored text is marked and can be exported.
                </p>
              </div>
              <div className="postmortem-actions">
                <Button
                  variant="outline"
                  disabled={phase < 6}
                  onClick={() => window.print()}
                >
                  <Download /> Print / PDF
                </Button>
                <Button
                  className="primary-action"
                  disabled={phase < 6}
                  onClick={exportPostmortem}
                >
                  <Download /> Export Markdown
                </Button>
              </div>
            </section>
            {phase < 6 ? (
              <section className="postmortem-locked glass-panel">
                <div className="lock-orbit">
                  <LockKeyhole />
                </div>
                <Badge className="amber-badge">VERIFICATION REQUIRED</Badge>
                <h2>The postmortem is waiting for observed recovery.</h2>
                <p>
                  OpsAssist never turns an attempted action into a successful
                  resolution until telemetry verifies the outcome.
                </p>
                <Button
                  onClick={() => setActiveView("twin")}
                  className="primary-action"
                >
                  Complete safe remediation <ArrowRight />
                </Button>
              </section>
            ) : (
              <section className="postmortem-document">
                <div className="document-cover">
                  <div>
                    <Badge className="ready-badge">
                      <BadgeCheck /> VERIFIED RECOVERY
                    </Badge>
                    <span>INC-2026-0847 · SYNTHETIC</span>
                  </div>
                  <h1>Checkout Cascade</h1>
                  <p>
                    Living postmortem · generated from 14 evidence objects and 7
                    verified timeline events
                  </p>
                  <div className="cover-line" />
                </div>
                {(
                  [
                    ["Executive summary", "summary"],
                    ["Customer impact", "impact"],
                    ["Root cause", "rootCause"],
                    ["Resolution & verification", "resolution"],
                  ] as const
                ).map(([label, key]) => (
                  <article className="document-section" key={key}>
                    <div className="section-number">
                      0
                      {["summary", "impact", "rootCause", "resolution"].indexOf(
                        key,
                      ) + 1}
                    </div>
                    <div>
                      <span>
                        {label}
                        <Badge>AI DRAFT · EDITABLE</Badge>
                      </span>
                      <textarea
                        value={postmortem[key]}
                        onChange={(event) =>
                          setPostmortem({
                            ...postmortem,
                            [key]: event.target.value,
                          })
                        }
                        aria-label={label}
                      />
                      {key === "rootCause" && (
                        <div className="citation-row">
                          {["EV-104", "EV-108", "EV-113", "EV-119"].map(
                            (id) => (
                              <button
                                key={id}
                                onClick={() =>
                                  setEvidenceOpen(
                                    evidenceItems.find(
                                      (item) => item.id === id,
                                    ) ?? evidenceItems[0],
                                  )
                                }
                              >
                                {id}
                              </button>
                            ),
                          )}
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </section>
            )}
          </TabsContent>

          <TabsContent value="architecture" className="view-stack">
            <section className="view-heading">
              <div>
                <Badge className="section-badge">
                  <Binary /> Technical proof
                </Badge>
                <h1>Architecture Explorer</h1>
                <p>
                  Select a system layer to inspect its contract, failure
                  behavior, security boundary and planned repository location.
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  toast.info(
                    "Repository handoff is documented in the project source",
                  )
                }
              >
                <Github /> Repository map
              </Button>
            </section>
            <section className="architecture-map glass-panel">
              <div className="architecture-flow">
                {architecture.map((component, index) => {
                  const Icon = component.icon;
                  return (
                    <div className="arch-step" key={component.id}>
                      <button
                        className={
                          architectureSelection.id === component.id
                            ? "active"
                            : ""
                        }
                        onClick={() => setArchitectureSelection(component)}
                      >
                        <Icon />
                        <span>{component.name}</span>
                        <small>{component.tech.split(" · ")[0]}</small>
                      </button>
                      {index < architecture.length - 1 && (
                        <i>
                          <ChevronRight />
                        </i>
                      )}
                    </div>
                  );
                })}
              </div>
              <AnimatePresence mode="wait">
                <motion.div
                  className="architecture-detail"
                  key={architectureSelection.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                >
                  <div className="detail-header">
                    <span className="detail-icon">
                      {(() => {
                        const Icon = architectureSelection.icon;
                        return <Icon />;
                      })()}
                    </span>
                    <div>
                      <span>SELECTED COMPONENT</span>
                      <h2>{architectureSelection.name}</h2>
                      <p>{architectureSelection.tech}</p>
                    </div>
                  </div>
                  <div className="detail-grid">
                    <div>
                      <span>Responsibility</span>
                      <p>{architectureSelection.responsibility}</p>
                    </div>
                    <div>
                      <span>Input → output</span>
                      <p>{architectureSelection.io}</p>
                    </div>
                    <div>
                      <span>Failure behavior</span>
                      <p>{architectureSelection.failure}</p>
                    </div>
                    <div>
                      <span>Security controls</span>
                      <p>{architectureSelection.security}</p>
                    </div>
                  </div>
                  <div className="source-path">
                    <Code2 />
                    <span>Source location</span>
                    <code>{architectureSelection.path}</code>
                  </div>
                </motion.div>
              </AnimatePresence>
            </section>
            <section className="stack-line">
              <span>PYTHON 3.12</span>
              <span>FASTAPI</span>
              <span>PYDANTIC</span>
              <span>FAISS</span>
              <span>SCIKIT-LEARN</span>
              <span>NETWORKX</span>
              <span>NEXT.JS</span>
              <span>THREE.JS</span>
              <span>POSTGRESQL</span>
            </section>
          </TabsContent>
        </main>
      </Tabs>

      <Sheet
        open={Boolean(evidenceOpen)}
        onOpenChange={(open) => !open && setEvidenceOpen(null)}
      >
        <SheetContent className="evidence-sheet">
          <SheetHeader>
            <Badge
              className={
                evidenceOpen?.stance === "Contradicts"
                  ? "critical-badge"
                  : "ready-badge"
              }
            >
              {evidenceOpen?.stance}
            </Badge>
            <SheetTitle>{evidenceOpen?.label}</SheetTitle>
            <SheetDescription>
              {evidenceOpen?.id} · {evidenceOpen?.type}
            </SheetDescription>
          </SheetHeader>
          {evidenceOpen && (
            <div className="evidence-sheet-body">
              <div className="source-meta">
                <div>
                  <span>Source</span>
                  <code>{evidenceOpen.source}</code>
                </div>
                <div>
                  <span>Timestamp</span>
                  <code>{evidenceOpen.time}</code>
                </div>
                <div>
                  <span>Reliability</span>
                  <b>{evidenceOpen.reliability}%</b>
                </div>
              </div>
              <div className="evidence-excerpt">
                <span>EXTRACTED PASSAGE</span>
                <code>{evidenceOpen.excerpt}</code>
              </div>
              <div>
                <span className="sheet-label">WHY IT MATTERS</span>
                <p>{evidenceOpen.why}</p>
              </div>
              <div className="provenance-chain">
                <span>PROVENANCE CHAIN</span>
                <p>
                  synthetic source → normalized event → immutable evidence
                  object → ranked hypothesis
                </p>
              </div>
              <div className="trust-callout">
                <ShieldCheck />
                <p>
                  <b>Source-bounded claim</b>
                  <br />
                  This observation does not confirm the hypothesis alone; it
                  contributes to the transparent ranking score.
                </p>
              </div>
            </div>
          )}
        </SheetContent>
      </Sheet>

      <Dialog open={approvalDialog} onOpenChange={setApprovalDialog}>
        <DialogContent className="approval-dialog">
          <DialogHeader>
            <div className="dialog-icon">
              <ShieldCheck />
            </div>
            <DialogTitle>Approve sensitive simulated action?</DialogTitle>
            <DialogDescription>
              This creates a signed local-demo approval record. It does not
              connect to or modify real infrastructure.
            </DialogDescription>
          </DialogHeader>
          <div className="approval-summary">
            <div>
              <span>Action</span>
              <b>Rollback Checkout + rolling restart</b>
            </div>
            <div>
              <span>Blast radius</span>
              <b>3 synthetic services</b>
            </div>
            <div>
              <span>Rollback</span>
              <b>Available and verified</b>
            </div>
            <div>
              <span>Policy</span>
              <b>POL-08 · Sensitive</b>
            </div>
          </div>
          <label className="approval-check">
            <input type="checkbox" defaultChecked readOnly />
            <span>
              I understand this executes only inside the safe simulator.
            </span>
          </label>
          <DialogFooter>
            <Button variant="outline" onClick={() => setApprovalDialog(false)}>
              Cancel
            </Button>
            <Button className="primary-action" onClick={confirmApproval}>
              <LockKeyhole /> Sign approval
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={tourOpen} onOpenChange={setTourOpen}>
        <DialogContent className="tour-dialog">
          <div className="tour-progress">
            {tour.map((_, index) => (
              <i key={index} className={index <= tourStep ? "active" : ""} />
            ))}
          </div>
          <DialogHeader>
            <Badge className="section-badge">
              <WandSparkles /> Recruiter proof mode
            </Badge>
            <DialogTitle>{tour[tourStep].title}</DialogTitle>
            <DialogDescription>{tour[tourStep].text}</DialogDescription>
          </DialogHeader>
          <div className="tour-proof">
            <div>
              <Eye />
              <span>Look at the active workspace behind this guide.</span>
            </div>
            <div>
              <Clock3 />
              <span>
                Step {tourStep + 1} of {tour.length} · about 45 seconds
              </span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTourOpen(false)}>
              Exit tour
            </Button>
            <Button className="primary-action" onClick={advanceTour}>
              {tourStep === tour.length - 1
                ? "Finish tour"
                : "Next proof point"}
              <ArrowRight />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function Home() {
  return <OpsAssistApp />;
}
