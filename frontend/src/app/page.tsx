"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";

type Body = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  mass: number;
  radius: number;
  color: string;
};

type Diagnostics = {
  kinetic_energy: number;
  potential_energy: number;
  total_energy: number;
  energy_drift_percent: number;
  linear_momentum: [number, number];
  angular_momentum: number;
  center_of_mass: [number, number];
  maximum_velocity: number;
};

type SimulationResponse = {
  bodies: Body[];
  elapsed_time: number;
  diagnostics: Diagnostics;
};

type Preset = "solar" | "binary" | "scatter";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const presets: Record<Preset, Body[]> = {
  solar: [
    { x: 450, y: 400, vx: 0, vy: 45, mass: 333000, radius: 20, color: "#fdb813" },
    { x: 550, y: 400, vx: -20, vy: -45, mass: 333000, radius: 20, color: "#4390c6" },
    { x: 100, y: 400, vx: 0, vy: 40, mass: 1, radius: 6, color: "#4390c6" },
    { x: 700, y: 400, vx: 0, vy: -60, mass: 1, radius: 6, color: "#dc4c46" },
    { x: 500, y: 700, vx: 40, vy: 0, mass: 1, radius: 6, color: "#1bc935" },
  ],
  binary: [
    { x: 390, y: 400, vx: 0, vy: -38, mass: 12000, radius: 15, color: "#80aaff" },
    { x: 610, y: 400, vx: 0, vy: 38, mass: 12000, radius: 15, color: "#fdb813" },
    { x: 500, y: 185, vx: 44, vy: 0, mass: 3, radius: 7, color: "#ff766c" },
  ],
  scatter: [
    { x: 500, y: 400, vx: 0, vy: 0, mass: 22000, radius: 19, color: "#fdb813" },
    { x: 230, y: 280, vx: 5, vy: 43, mass: 40, radius: 9, color: "#4390c6" },
    { x: 740, y: 600, vx: -42, vy: -9, mass: 65, radius: 10, color: "#1bc935" },
    { x: 760, y: 240, vx: -7, vy: 35, mass: 24, radius: 8, color: "#dc4c46" },
    { x: 300, y: 680, vx: 34, vy: -16, mass: 18, radius: 7, color: "#bd8cff" },
  ],
};

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function GravityCanvas({
  bodies,
  running,
}: {
  bodies: Body[];
  running: boolean;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const bodiesRef = useRef(bodies);
  const cameraRef = useRef({ zoom: 1, x: 0, y: 0 });
  const pointerRef = useRef<{ x: number; y: number } | null>(null);
  const redrawRef = useRef<() => void>(() => {});

  useEffect(() => {
    bodiesRef.current = bodies;
    if (!running) redrawRef.current();
  }, [bodies, running]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;

    let frame = 0;
    let width = 0;
    let height = 0;
    const resize = () => {
      const bounds = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      width = bounds.width;
      height = bounds.height;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.fillStyle = "#080d17";
      context.fillRect(0, 0, width, height);
    };

    const draw = () => {
      context.fillStyle = "rgba(8, 13, 23, 0.18)";
      context.fillRect(0, 0, width, height);
      const camera = cameraRef.current;
      const centerX = width / 2 + camera.x;
      const centerY = height / 2 + camera.y;

      context.save();
      context.strokeStyle = "rgba(112, 137, 173, 0.08)";
      context.lineWidth = 1;
      const gridSize = 80 * camera.zoom;
      const offsetX = ((centerX % gridSize) + gridSize) % gridSize;
      const offsetY = ((centerY % gridSize) + gridSize) % gridSize;
      for (let x = offsetX; x < width; x += gridSize) {
        context.beginPath();
        context.moveTo(x, 0);
        context.lineTo(x, height);
        context.stroke();
      }
      for (let y = offsetY; y < height; y += gridSize) {
        context.beginPath();
        context.moveTo(0, y);
        context.lineTo(width, y);
        context.stroke();
      }

      for (const body of bodiesRef.current) {
        const x = centerX + (body.x - 500) * camera.zoom;
        const y = centerY + (body.y - 400) * camera.zoom;
        const radius = Math.max(2, body.radius * camera.zoom);
        const glow = context.createRadialGradient(x, y, radius * 0.2, x, y, radius * 3);
        glow.addColorStop(0, `${body.color}55`);
        glow.addColorStop(1, `${body.color}00`);
        context.fillStyle = glow;
        context.beginPath();
        context.arc(x, y, radius * 3, 0, Math.PI * 2);
        context.fill();
        context.fillStyle = body.color;
        context.shadowBlur = 12;
        context.shadowColor = body.color;
        context.beginPath();
        context.arc(x, y, radius, 0, Math.PI * 2);
        context.fill();
        context.shadowBlur = 0;
      }
      context.restore();

      if (running) frame = requestAnimationFrame(draw);
    };

    redrawRef.current = draw;
    resize();
    draw();
    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
    };
  }, [running]);

  const handlePointerDown = (event: React.PointerEvent<HTMLCanvasElement>) => {
    pointerRef.current = { x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const handlePointerMove = (event: React.PointerEvent<HTMLCanvasElement>) => {
    if (!pointerRef.current) return;
    cameraRef.current.x += event.clientX - pointerRef.current.x;
    cameraRef.current.y += event.clientY - pointerRef.current.y;
    pointerRef.current = { x: event.clientX, y: event.clientY };
  };
  const handleWheel = (event: React.WheelEvent<HTMLCanvasElement>) => {
    event.preventDefault();
    cameraRef.current.zoom = Math.min(
      3,
      Math.max(0.35, cameraRef.current.zoom * (event.deltaY < 0 ? 1.1 : 0.9)),
    );
  };

  return (
    <canvas
      ref={canvasRef}
      className="space-canvas"
      aria-label="Animated gravity simulation"
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={() => {
        pointerRef.current = null;
      }}
      onPointerCancel={() => {
        pointerRef.current = null;
      }}
      onWheel={handleWheel}
    />
  );
}

export default function Home() {
  const [bodies, setBodies] = useState<Body[]>(presets.solar);
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null);
  const [running, setRunning] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [preset, setPreset] = useState<Preset>("solar");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");
  const busyRef = useRef(false);
  const bodiesRef = useRef(bodies);
  const runningRef = useRef(running);
  const speedRef = useRef(speed);
  const presetRef = useRef(preset);
  const referenceEnergyRef = useRef<number | null>(null);

  useEffect(() => {
    bodiesRef.current = bodies;
  }, [bodies]);
  useEffect(() => {
    runningRef.current = running;
  }, [running]);
  useEffect(() => {
    speedRef.current = speed;
  }, [speed]);
  useEffect(() => {
    presetRef.current = preset;
  }, [preset]);

  const reset = useCallback((nextPreset: Preset = presetRef.current) => {
    const nextBodies = presets[nextPreset].map((body) => ({ ...body }));
    bodiesRef.current = nextBodies;
    setBodies(nextBodies);
    setPreset(nextPreset);
    setDiagnostics(null);
    referenceEnergyRef.current = null;
    setError("");
  }, []);

  useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_URL}/api/health`);
        if (!response.ok) throw new Error(`Backend returned ${response.status}`);
        if (active) {
          setConnected(true);
          setError("");
        }
      } catch {
        if (active) {
          setConnected(false);
          setError("Backend unavailable. Start the FastAPI server to run the simulation.");
        }
      }
    };
    void checkHealth();
    const healthInterval = window.setInterval(() => {
      void checkHealth();
    }, 3000);
    const interval = window.setInterval(() => {
      if (!active || !runningRef.current || busyRef.current || !connected) return;
      busyRef.current = true;
      void fetch(`${API_URL}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bodies: bodiesRef.current,
          dt: 0.1,
          steps: speedRef.current,
          gravitational_constant: 1,
          reference_energy: referenceEnergyRef.current,
          collisions: true,
        }),
      })
        .then(async (response) => {
          if (!response.ok) {
            const detail = await response.text();
            throw new Error(`Simulation failed (${response.status}): ${detail}`);
          }
          return (await response.json()) as SimulationResponse;
        })
        .then((result) => {
          if (!active) return;
          bodiesRef.current = result.bodies;
          setBodies(result.bodies);
          setDiagnostics(result.diagnostics);
          if (referenceEnergyRef.current === null) {
            referenceEnergyRef.current = result.diagnostics.total_energy;
          }
          setError("");
        })
        .catch((cause: unknown) => {
          if (!active) return;
          setRunning(false);
          setError(cause instanceof Error ? cause.message : "Simulation request failed.");
        })
        .finally(() => {
          busyRef.current = false;
        });
    }, 40);
    return () => {
      active = false;
      window.clearInterval(healthInterval);
      window.clearInterval(interval);
    };
  }, [connected]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Gravity Lab home">
          <span className="brand-mark">G</span>
          <span>gravity<span className="brand-light">lab</span></span>
        </Link>
        <div className="topbar-meta">
          <span className={`connection ${connected ? "online" : ""}`}>
            <span className="status-dot" />
            {connected ? "ENGINE ONLINE" : "ENGINE OFFLINE"}
          </span>
          <span className="topbar-divider" />
          <span className="topbar-caption">N-BODY SIMULATOR <span>·</span> v1.0</span>
        </div>
      </header>

      <section className="workspace">
        <div className="main-column">
          <div className="page-heading">
            <div>
              <p className="eyebrow">ORBITAL MECHANICS / LIVE EXPERIMENT</p>
              <h1>Gravity, in motion.</h1>
              <p className="subtitle">Build a system. Watch the universe respond.</p>
            </div>
            <div className="time-chip">
              <span className="time-icon">◷</span>
              <span>SIM TIME</span>
              <strong>{diagnostics ? "RUNNING" : "READY"}</strong>
            </div>
          </div>

          <div className="simulation-window">
            <GravityCanvas bodies={bodies} running={running} />
            <div className="canvas-label"><span className="mini-orbit">◎</span> ORBITAL VIEW <span>·</span> {bodies.length} BODIES</div>
            <div className="canvas-hint">DRAG TO PAN <span>·</span> SCROLL TO ZOOM</div>
            {!connected && <div className="canvas-offline">Waiting for Python engine</div>}
            <div className="canvas-crosshair">+</div>
          </div>

          <div className="transport">
            <div className="transport-actions">
              <button
                className={`play-button ${running ? "is-playing" : ""}`}
                onClick={() => setRunning((value) => !value)}
                aria-label={running ? "Pause simulation" : "Start simulation"}
              >
                {running ? "Ⅱ" : "▶"}
              </button>
              <button className="icon-button" onClick={() => reset()} aria-label="Reset simulation">↺</button>
              <span className="transport-divider" />
              <div className="speed-control">
                <span className="control-label">SIM SPEED</span>
                {[1, 2, 4].map((value) => (
                  <button
                    className={speed === value ? "speed-option selected" : "speed-option"}
                    key={value}
                    onClick={() => setSpeed(value)}
                  >
                    {value}×
                  </button>
                ))}
              </div>
            </div>
            <div className="transport-readout">
              <span className="live-indicator" />
              <span>{running && connected ? "LIVE SIMULATION" : running ? "CONNECTING" : "PAUSED"}</span>
              <span className="readout-divider" />
              <span>{bodies.length} ACTIVE BODIES</span>
            </div>
          </div>

          {error && <div className="error-banner" role="status">{error}</div>}

          <section className="preset-section">
            <div className="section-title">
              <div><p className="eyebrow">START WITH A SYSTEM</p><h2>Choose an experiment</h2></div>
              <span className="preset-count">03 PRESETS</span>
            </div>
            <div className="preset-grid">
              <button className={`preset-card ${preset === "solar" ? "active" : ""}`} onClick={() => reset("solar")}>
                <span className="preset-illustration solar-art"><i /><i /><i /></span>
                <span className="preset-copy"><strong>Solar dance</strong><small>Two stars, three wanderers</small></span>
                <span className="preset-arrow">↗</span>
              </button>
              <button className={`preset-card ${preset === "binary" ? "active" : ""}`} onClick={() => reset("binary")}>
                <span className="preset-illustration binary-art"><i /><i /><i /></span>
                <span className="preset-copy"><strong>Binary stars</strong><small>A paired stellar system</small></span>
                <span className="preset-arrow">↗</span>
              </button>
              <button className={`preset-card ${preset === "scatter" ? "active" : ""}`} onClick={() => reset("scatter")}>
                <span className="preset-illustration scatter-art"><i /><i /><i /></span>
                <span className="preset-copy"><strong>Cosmic scatter</strong><small>Chaos around a giant</small></span>
                <span className="preset-arrow">↗</span>
              </button>
            </div>
          </section>
        </div>

        <aside className="inspector">
          <div className="inspector-heading">
            <div><p className="eyebrow">SYSTEM TELEMETRY</p><h2>Diagnostics</h2></div>
            <span className="telemetry-icon">⌁</span>
          </div>
          <div className="metric-highlight">
            <div className="metric-heading"><span>TOTAL ENERGY</span><span className="metric-mark">↗</span></div>
            <div className="metric-value">{diagnostics ? formatNumber(diagnostics.total_energy) : "—"}</div>
            <div className="energy-bar"><span style={{ width: diagnostics ? `${Math.max(3, Math.min(100, 50 + diagnostics.energy_drift_percent))}%` : "3%" }} /></div>
            <div className="metric-foot"><span>ENERGY DRIFT</span><strong>{diagnostics ? `${formatNumber(diagnostics.energy_drift_percent)}%` : "—"}</strong></div>
          </div>
          <div className="metric-list">
            <div className="metric-row"><span><i className="metric-dot kinetic" /> Kinetic energy</span><strong>{diagnostics ? formatNumber(diagnostics.kinetic_energy) : "—"}</strong></div>
            <div className="metric-row"><span><i className="metric-dot potential" /> Potential energy</span><strong>{diagnostics ? formatNumber(diagnostics.potential_energy) : "—"}</strong></div>
            <div className="metric-row"><span><i className="metric-dot momentum" /> Linear momentum</span><strong>{diagnostics ? `${formatNumber(diagnostics.linear_momentum[0])}, ${formatNumber(diagnostics.linear_momentum[1])}` : "—"}</strong></div>
            <div className="metric-row"><span><i className="metric-dot angular" /> Angular momentum</span><strong>{diagnostics ? formatNumber(diagnostics.angular_momentum) : "—"}</strong></div>
            <div className="metric-row"><span><i className="metric-dot center" /> Center of mass</span><strong>{diagnostics ? `${formatNumber(diagnostics.center_of_mass[0])}, ${formatNumber(diagnostics.center_of_mass[1])}` : "—"}</strong></div>
            <div className="metric-row"><span><i className="metric-dot velocity" /> Max velocity</span><strong>{diagnostics ? formatNumber(diagnostics.maximum_velocity) : "—"}</strong></div>
          </div>

          <div className="inspector-rule" />
          <div className="bodies-heading"><span>CELESTIAL BODIES</span><span>{String(bodies.length).padStart(2, "0")}</span></div>
          <div className="body-list">
            {bodies.map((body, index) => (
              <div className="body-item" key={`${body.color}-${index}`}>
                <span className="body-swatch" style={{ backgroundColor: body.color, boxShadow: `0 0 10px ${body.color}55` }} />
                <span className="body-name">{body.mass > 1000 ? "Stellar body" : `Body ${String(index + 1).padStart(2, "0")}`}</span>
                <span className="body-mass">{formatNumber(body.mass)} <small>u</small></span>
              </div>
            ))}
          </div>
          <div className="physics-note"><span>✳</span><p>Powered by <strong>Newtonian gravity</strong><br />with adaptive collision merging.</p></div>
        </aside>
      </section>
      <footer className="footer">
        <span>AN EXPERIMENT IN CELESTIAL MECHANICS</span>
        <span>PYTHON ENGINE <i>×</i> NEXT.JS</span>
      </footer>
    </main>
  );
}
