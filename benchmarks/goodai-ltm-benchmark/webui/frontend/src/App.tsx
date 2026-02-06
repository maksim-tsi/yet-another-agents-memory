import { useEffect, useMemo, useState } from "react";

type LlmPreset = {
  id: string;
  label: string;
  agent_name: string;
  wrapper_agent_type?: string;
  wrapper_model?: string;
  wrapper_port?: number;
};

type AgentPreset = { id: string; label: string };

type BenchmarkPreset = {
  id: string;
  label: string;
  config_path: string;
  description: string;
};

type PresetsResponse = {
  llm_presets: LlmPreset[];
  agent_presets: AgentPreset[];
  benchmark_presets: BenchmarkPreset[];
};

type RunSummary = {
  run_id: string;
  run_name: string;
  agent_name: string;
  start_time?: string;
  end_time?: string;
  status: string;
  path: string;
};

type IndexSummary = {
  totals?: { examples: number; questions: number };
  examples?: Array<{ dataset: string; example_id: string; questions: number }>;
};

export default function App() {
  const [presets, setPresets] = useState<PresetsResponse | null>(null);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [progress, setProgress] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [selectedLog, setSelectedLog] = useState<string>("");
  const [indexSummary, setIndexSummary] = useState<IndexSummary | null>(null);

  const [llmPresetId, setLlmPresetId] = useState<string>("");
  const [agentId, setAgentId] = useState<string>("");
  const [benchmarkId, setBenchmarkId] = useState<string>("");
  const [runName, setRunName] = useState<string>("MAS Run");
  const [runId, setRunId] = useState<string>("");
  const [testFilter, setTestFilter] = useState<string>("");
  const [stuckTimeout, setStuckTimeout] = useState<number>(15);

  useEffect(() => {
    fetch("/api/presets")
      .then((res) => res.json())
      .then((data) => {
        setPresets(data);
        setLlmPresetId(data.llm_presets[0]?.id ?? "");
        setAgentId(data.agent_presets[0]?.id ?? "");
        setBenchmarkId(data.benchmark_presets[0]?.id ?? "");
      });
  }, []);

  useEffect(() => {
    const loadRuns = () =>
      fetch("/api/runs")
        .then((res) => res.json())
        .then((data) => {
          setRuns(data.runs || []);
          if (!selectedRunId && data.runs?.[0]) {
            setSelectedRunId(data.runs[0].run_id);
          }
        });
    loadRuns();
    const timer = setInterval(loadRuns, 8000);
    return () => clearInterval(timer);
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) return;
    const loadProgress = () =>
      fetch(`/api/runs/${selectedRunId}/progress`)
        .then((res) => res.json())
        .then(setProgress);
    loadProgress();
    const timer = setInterval(loadProgress, 5000);
    return () => clearInterval(timer);
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedRunId) return;
    fetch(`/api/runs/${selectedRunId}/logs`)
      .then((res) => res.json())
      .then((data) => setLogs(data.files || []));
  }, [selectedRunId]);

  useEffect(() => {
    if (!selectedRunId || !selectedLog) return;
    fetch(`/api/runs/${selectedRunId}/logs/${selectedLog}`)
      .then((res) => res.json())
      .then((data) => setLogLines(data.lines || []));
  }, [selectedRunId, selectedLog]);

  useEffect(() => {
    if (!presets || !benchmarkId) return;
    const preset = presets.benchmark_presets.find((p) => p.id === benchmarkId);
    if (!preset) return;
    fetch(`/api/index?config_path=${encodeURIComponent(preset.config_path)}`)
      .then((res) => res.json())
      .then(setIndexSummary)
      .catch(() => setIndexSummary(null));
  }, [presets, benchmarkId]);

  const selectedLlm = useMemo(
    () => presets?.llm_presets.find((p) => p.id === llmPresetId),
    [presets, llmPresetId]
  );
  const selectedBenchmark = useMemo(
    () => presets?.benchmark_presets.find((p) => p.id === benchmarkId),
    [presets, benchmarkId]
  );

  const startWrapper = async () => {
    if (!selectedLlm?.wrapper_agent_type || !selectedLlm.wrapper_port) return;
    await fetch("/api/wrappers/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent_type: selectedLlm.wrapper_agent_type,
        port: selectedLlm.wrapper_port,
        model: selectedLlm.wrapper_model
      })
    });
  };

  const startRun = async () => {
    if (!selectedBenchmark || !selectedLlm) return;
    await fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        config_path: selectedBenchmark.config_path,
        agent_name: agentId || selectedLlm.agent_name,
        run_name: runName,
        run_id: runId || undefined,
        stuck_timeout: stuckTimeout,
        test_filter: testFilter || undefined
      })
    });
  };

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">GoodAI Benchmark</p>
          <h1>Transparency &amp; Progress Dashboard</h1>
          <p className="subtitle">
            Launch runs, track progress, inspect logs, and verify visibility instrumentation.
          </p>
        </div>
        <div className="hero-card">
          <div className="hero-metric">
            <span>Active Runs</span>
            <strong>{runs.filter((run) => run.status === "running").length}</strong>
          </div>
          <div className="hero-metric">
            <span>Latest Status</span>
            <strong>{runs[0]?.status ?? "none"}</strong>
          </div>
        </div>
      </header>

      <section className="grid">
        <div className="panel">
          <h2>Setup</h2>
          <div className="field">
            <label>LLM Preset</label>
            <select value={llmPresetId} onChange={(e) => setLlmPresetId(e.target.value)}>
              {presets?.llm_presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Agent</label>
            <select value={agentId} onChange={(e) => setAgentId(e.target.value)}>
              {presets?.agent_presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Benchmark Scope</label>
            <select value={benchmarkId} onChange={(e) => setBenchmarkId(e.target.value)}>
              {presets?.benchmark_presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.label}
                </option>
              ))}
            </select>
            <p className="hint">{selectedBenchmark?.description}</p>
          </div>
          <div className="field">
            <label>Run Name</label>
            <input value={runName} onChange={(e) => setRunName(e.target.value)} />
          </div>
          <div className="field">
            <label>Run ID (optional)</label>
            <input value={runId} onChange={(e) => setRunId(e.target.value)} />
          </div>
          <div className="field">
            <label>Single Test Filter</label>
            <input
              value={testFilter}
              onChange={(e) => setTestFilter(e.target.value)}
              placeholder="dataset:example_id"
            />
          </div>
          <div className="field">
            <label>Stuck Timeout (minutes)</label>
            <input
              type="number"
              value={stuckTimeout}
              onChange={(e) => setStuckTimeout(parseInt(e.target.value, 10))}
            />
          </div>
          <div className="button-row">
            <button className="primary" onClick={startRun}>
              Start Run
            </button>
            {selectedLlm?.wrapper_agent_type && (
              <button className="ghost" onClick={startWrapper}>
                Start Wrapper
              </button>
            )}
          </div>
        </div>

        <div className="panel">
          <h2>Benchmark Scope</h2>
          <div className="scope">
            <div>
              <span className="tag">Config</span>
              <strong>{selectedBenchmark?.config_path ?? "none"}</strong>
            </div>
            <div>
              <span className="tag">Questions</span>
              <strong>{indexSummary?.totals?.questions ?? "unknown"}</strong>
            </div>
            <div>
              <span className="tag">Examples</span>
              <strong>{indexSummary?.totals?.examples ?? "unknown"}</strong>
            </div>
          </div>
          <div className="scope-list">
            {(indexSummary?.examples || []).slice(0, 8).map((example, idx) => (
              <div key={`${example.dataset}-${example.example_id}-${idx}`} className="scope-row">
                <span>{example.dataset}</span>
                <span>#{example.example_id}</span>
                <span>{example.questions} q</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Run Progress</h2>
          <div className="field">
            <label>Active Run</label>
            <select value={selectedRunId} onChange={(e) => setSelectedRunId(e.target.value)}>
              {runs.map((run) => (
                <option key={run.run_id} value={run.run_id}>
                  {run.run_name} · {run.agent_name} · {run.status}
                </option>
              ))}
            </select>
          </div>
          <div className="progress-card">
            <div>
              <span className="tag">Status</span>
              <strong>{runs.find((r) => r.run_id === selectedRunId)?.status}</strong>
            </div>
            <div>
              <span className="tag">Turns</span>
              <strong>{progress?.count ?? 0}</strong>
            </div>
            <div>
              <span className="tag">Tokens</span>
              <strong>{progress?.runstats?.total_tokens ?? 0}</strong>
            </div>
          </div>
          <div className="metrics">
            <div>
              <span>LLM p95</span>
              <strong>{progress?.runstats?.llm_ms_p95?.toFixed?.(0) ?? "n/a"} ms</strong>
            </div>
            <div>
              <span>Storage p95</span>
              <strong>{progress?.runstats?.storage_ms_p95?.toFixed?.(0) ?? "n/a"} ms</strong>
            </div>
          </div>
          <div className="latest">
            <p>Latest Turn</p>
            <pre>{JSON.stringify(progress?.latest ?? {}, null, 2)}</pre>
          </div>
        </div>

        <div className="panel">
          <h2>Logs</h2>
          <div className="logs">
            <div className="log-list">
              {logs.map((file) => (
                <button
                  key={file.name}
                  className={selectedLog === file.name ? "active" : ""}
                  onClick={() => setSelectedLog(file.name)}
                >
                  {file.name}
                </button>
              ))}
            </div>
            <div className="log-viewer">
              <pre>{logLines.join("\n") || "Select a log file."}</pre>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
