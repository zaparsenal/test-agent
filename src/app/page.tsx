'use client';

import {
  Activity,
  ArrowLeft,
  BarChart3,
  Check,
  ChevronDown,
  CircleAlert,
  Database,
  Download,
  FileCode2,
  FileSearch,
  LoaderCircle,
  MessageSquareText,
  RotateCcw,
  Send,
  ShieldCheck,
  Sparkles,
  Upload,
} from 'lucide-react';
import { ChangeEvent, DragEvent, SyntheticEvent, useCallback, useEffect, useRef, useState } from 'react';
import { AgentSurface } from '@/components/agent-surface';

type InputKind = 'diagram' | 'dcs';

type InputMetadata = {
  kind: InputKind;
  name: string;
  fileType: string;
  sizeBytes: number;
  origin: string;
  status: string;
  compatible: boolean;
  note: string;
  tags: string[];
  tagCount: number;
  nodeCount?: number;
  edgeCount?: number;
  rowCount?: number;
  timeRange?: { start: string; end: string };
  qualityCounts?: Record<string, number>;
  sampleRows?: Array<Record<string, string | number | null>>;
};

type InputStatus = {
  diagram: InputMetadata | null;
  dcs: InputMetadata | null;
  analysisReady: boolean;
  message: string;
};

type AgentResponse = {
  question: string;
  intent: string;
  surfaceId: string;
  messages: unknown[];
  answer: { title: string; text: string; confidence: number; severity: string; window: string };
  metadata: { protocol: string; catalogId: string; advisoryOnly: boolean; dataThrough: string };
};

type ConversationTurn = {
  id: string;
  question: string;
  initial: boolean;
  status: 'loading' | 'complete' | 'error';
  response?: AgentResponse;
  error?: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const EMPTY_INPUTS: InputStatus = { diagram: null, dcs: null, analysisReady: false, message: 'Add both inputs to continue.' };
const INITIAL_QUESTION = 'What is happening in the process right now?';
const SUGGESTIONS = [
  "Why did T-101's level increase?",
  'Show pressure and flow during the event.',
  'What should the operator inspect first?',
  'Which sensor readings are unreliable?',
];

function formatBytes(bytes: number): string {
  return bytes > 1_000_000 ? `${(bytes / 1_000_000).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1000))} KB`;
}

function timeLabel(timestamp?: string): string {
  return timestamp ? timestamp.replace('T', ' ').slice(0, 16) : '—';
}

function FileInputCard({
  kind,
  index,
  metadata,
  busy,
  onFile,
  onPreview,
}: {
  kind: InputKind;
  index: number;
  metadata: InputMetadata | null;
  busy: boolean;
  onFile: (kind: InputKind, file: File) => void;
  onPreview: (kind: InputKind) => void;
}) {
  const isDiagram = kind === 'diagram';
  const inputId = `${kind}-file`;
  const accept = isDiagram ? '.xml,.dexpi,.svg,.json' : '.csv,.json';

  const handleDrop = (event: DragEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file) onFile(kind, file);
  };

  return (
    <article className={`upload-card ${metadata ? 'has-file' : ''} ${metadata && !metadata.compatible ? 'incompatible' : ''}`}>
      <div className="upload-card-header">
        <div className="step-number">{index}</div>
        <div className="upload-title">
          <span>{isDiagram ? 'PROCESS CONTEXT' : 'OPERATING DATA'}</span>
          <h2>{isDiagram ? 'PFD or P&ID' : 'DCS historian export'}</h2>
        </div>
        <div className="upload-icon">{isDiagram ? <FileCode2 /> : <Database />}</div>
      </div>

      <p className="upload-description">
        {isDiagram
          ? 'Add a machine-readable process diagram so the assistant can identify equipment, instruments, and the process path.'
          : 'Add timestamped tag readings so the assistant can calculate trends, events, limits, and data-quality issues.'}
      </p>

      {metadata ? (
        <div className="loaded-file">
          <div className="loaded-file-icon">{metadata.compatible ? <Check /> : <CircleAlert />}</div>
          <div className="loaded-file-copy">
            <strong>{metadata.name}</strong>
            <span>{metadata.fileType} · {formatBytes(metadata.sizeBytes)}</span>
            <p>{metadata.note}</p>
          </div>
          <button onClick={() => onPreview(kind)}><FileSearch /> Inspect</button>
        </div>
      ) : (
        <button className="drop-zone" type="button" disabled={busy} onClick={() => document.getElementById(inputId)?.click()} onDragOver={(event) => event.preventDefault()} onDrop={handleDrop}>
          {busy ? <LoaderCircle className="spin" /> : <Upload />}
          <strong>{busy ? 'Reading file…' : 'Drop a file here or choose one'}</strong>
          <span>{isDiagram ? 'DEXPI XML, tagged SVG, or topology JSON' : 'CSV or JSON · maximum 8 MB'}</span>
        </button>
      )}
      <input
        className="file-input"
        id={inputId}
        type="file"
        accept={accept}
        disabled={busy}
        onChange={(event: ChangeEvent<HTMLInputElement>) => {
          const file = event.target.files?.[0];
          if (file) onFile(kind, file);
          event.target.value = '';
        }}
      />

      <div className="upload-card-footer">
        <label htmlFor={inputId}>{metadata ? 'Replace file' : 'Choose file'}</label>
        <a href={`${API_URL}/api/samples/${kind}`} download><Download /> Download sample</a>
      </div>
    </article>
  );
}

function InputPreview({ metadata, onClose }: { metadata: InputMetadata; onClose: () => void }) {
  return (
    <section className="input-preview" aria-label={`Parsed preview for ${metadata.name}`}>
      <div className="preview-header">
        <div><span>PARSED INPUT</span><h2>{metadata.name}</h2><p>{metadata.fileType} · {formatBytes(metadata.sizeBytes)}</p></div>
        <button onClick={onClose}>Close preview</button>
      </div>

      <div className="preview-stats">
        <div><span>{metadata.kind === 'diagram' ? 'Components' : 'Rows'}</span><strong>{(metadata.nodeCount ?? metadata.rowCount ?? 0).toLocaleString()}</strong></div>
        <div><span>Unique tags</span><strong>{metadata.tagCount}</strong></div>
        {metadata.kind === 'diagram' ? (
          <div><span>Connections</span><strong>{metadata.edgeCount ?? 'Source-specific'}</strong></div>
        ) : (
          <div><span>Time window</span><strong>{timeLabel(metadata.timeRange?.start)}<br />to {timeLabel(metadata.timeRange?.end)}</strong></div>
        )}
      </div>

      <div className="preview-content">
        <div>
          <h3>Tags found</h3>
          <div className="preview-tags">{metadata.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
        </div>
        {metadata.kind === 'dcs' && metadata.sampleRows && (
          <div>
            <h3>First parsed rows</h3>
            <div className="preview-table-wrap">
              <table>
                <thead><tr><th>Timestamp</th><th>Tag</th><th>Value</th><th>Unit</th><th>Quality</th></tr></thead>
                <tbody>{metadata.sampleRows.map((row, index) => <tr key={`${row.timestamp}-${row.tag}-${index}`}><td>{String(row.timestamp).slice(0, 16).replace('T', ' ')}</td><td>{row.tag}</td><td>{row.value ?? '—'}</td><td>{row.unit}</td><td>{row.quality}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export default function Home() {
  const [view, setView] = useState<'inputs' | 'analysis'>('inputs');
  const [inputs, setInputs] = useState<InputStatus>(EMPTY_INPUTS);
  const [previewKind, setPreviewKind] = useState<InputKind | null>(null);
  const [uploading, setUploading] = useState<InputKind | null>(null);
  const [inputError, setInputError] = useState('');
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [question, setQuestion] = useState('');
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'offline'>('connecting');
  const latestTurnRef = useRef<HTMLElement>(null);

  useEffect(() => {
    void fetch(`${API_URL}/api/inputs`)
      .then((response) => {
        if (!response.ok) throw new Error();
        return response.json() as Promise<InputStatus>;
      })
      .then((status) => { setInputs(status); setBackendStatus('connected'); })
      .catch(() => setBackendStatus('offline'));
  }, []);

  const uploadFile = async (kind: InputKind, file: File) => {
    setUploading(kind);
    setInputError('');
    try {
      const content = await file.text();
      const response = await fetch(`${API_URL}/api/inputs/inspect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind, name: file.name, content, sizeBytes: file.size }),
      });
      const payload = await response.json() as InputStatus | { detail?: string };
      if (!response.ok) throw new Error('detail' in payload ? payload.detail : 'The file could not be parsed');
      setInputs(payload as InputStatus);
      setPreviewKind(kind);
      setBackendStatus('connected');
    } catch (error) {
      setInputError(error instanceof Error ? error.message : 'The file could not be parsed');
    } finally {
      setUploading(null);
    }
  };

  const loadSampleInputs = async () => {
    setUploading('diagram');
    setInputError('');
    try {
      const response = await fetch(`${API_URL}/api/inputs/demo`, { method: 'POST' });
      if (!response.ok) throw new Error('The sample inputs could not be loaded');
      setInputs(await response.json() as InputStatus);
      setPreviewKind(null);
      setBackendStatus('connected');
    } catch (error) {
      setInputError(error instanceof Error ? error.message : 'The sample inputs could not be loaded');
    } finally {
      setUploading(null);
    }
  };

  const clearInputs = async () => {
    if (uploading) return;
    const response = await fetch(`${API_URL}/api/inputs`, { method: 'DELETE' });
    if (response.ok) setInputs(await response.json() as InputStatus);
    setPreviewKind(null);
    setTurns([]);
    setView('inputs');
  };

  const ask = useCallback(async (text: string, initial = false) => {
    const cleanQuestion = text.trim();
    if (!cleanQuestion) return;
    const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    setTurns((current) => [...current, { id, question: cleanQuestion, initial, status: 'loading' }]);
    try {
      const response = await fetch(`${API_URL}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: cleanQuestion }),
      });
      const payload = await response.json() as AgentResponse | { detail?: string };
      if (!response.ok) throw new Error('detail' in payload ? payload.detail : 'The analysis failed');
      setTurns((current) => current.map((turn) => turn.id === id ? { ...turn, status: 'complete', response: payload as AgentResponse } : turn));
      setBackendStatus('connected');
    } catch (error) {
      setTurns((current) => current.map((turn) => turn.id === id ? { ...turn, status: 'error', error: error instanceof Error ? error.message : 'The analysis failed' } : turn));
      setBackendStatus('offline');
    }
  }, []);

  const startAnalysis = () => {
    if (!inputs.analysisReady) return;
    setTurns([]);
    setView('analysis');
    void ask(INITIAL_QUESTION, true);
  };

  const loading = turns.some((turn) => turn.status === 'loading');
  const latestTurnId = turns.at(-1)?.id;

  useEffect(() => {
    const frame = requestAnimationFrame(() => latestTurnRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    return () => cancelAnimationFrame(frame);
  }, [turns]);

  const submitQuestion = (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim() || loading) return;
    const submitted = question;
    setQuestion('');
    void ask(submitted);
  };

  const selectedPreview = previewKind ? inputs[previewKind] : null;

  return (
    <main className="product-shell">
      <header className="topbar">
        <div className="product-brand"><span className="brand-mark"><Activity /></span><div><strong>FieldGuide</strong><small>Process Insights</small></div></div>
        <nav aria-label="Workspace sections">
          <button className={view === 'inputs' ? 'active' : ''} onClick={() => setView('inputs')}><FileCode2 /> Inputs</button>
          <button className={view === 'analysis' ? 'active' : ''} onClick={() => inputs.analysisReady && setView('analysis')} disabled={!inputs.analysisReady}><MessageSquareText /> Analysis</button>
        </nav>
        <div className="connection-status"><span className={`status-dot ${backendStatus}`} /><div><strong>{backendStatus === 'connected' ? 'Local agent ready' : backendStatus === 'offline' ? 'Agent offline' : 'Connecting'}</strong><small>Advisory only</small></div></div>
      </header>

      {view === 'inputs' ? (
        <div className="inputs-page">
          <section className="inputs-heading">
            <div><span className="section-label">NEW ANALYSIS</span><h1>Choose what the agent should investigate</h1><p>Load the process diagram and historian export, inspect what was parsed, then start the analysis.</p></div>
            <div className="sample-actions"><button className="secondary-button" onClick={() => void clearInputs()} disabled={!inputs.diagram && !inputs.dcs}><RotateCcw /> Clear</button><button className="sample-button" onClick={() => void loadSampleInputs()} disabled={Boolean(uploading)}><Sparkles /> Load sample inputs</button></div>
          </section>

          {inputError && <div className="input-error"><CircleAlert /><span>{inputError}</span></div>}

          <section className="upload-grid" aria-label="Input files">
            <FileInputCard kind="diagram" index={1} metadata={inputs.diagram} busy={uploading === 'diagram'} onFile={(kind, file) => void uploadFile(kind, file)} onPreview={setPreviewKind} />
            <FileInputCard kind="dcs" index={2} metadata={inputs.dcs} busy={uploading === 'dcs'} onFile={(kind, file) => void uploadFile(kind, file)} onPreview={setPreviewKind} />
          </section>

          {selectedPreview && <InputPreview metadata={selectedPreview} onClose={() => setPreviewKind(null)} />}

          <section className={`readiness-panel ${inputs.analysisReady ? 'ready' : ''}`}>
            <div className="readiness-icon">{inputs.analysisReady ? <Check /> : <BarChart3 />}</div>
            <div><span>ANALYSIS READINESS</span><h2>{inputs.analysisReady ? 'Both inputs are ready' : 'Two inputs are required'}</h2><p>{inputs.analysisReady ? 'The tags, timestamps, and process equipment match the demonstration analysis model.' : 'Load a compatible process diagram and DCS export. You can use the included sample files for a quick team demo.'}</p></div>
            <button onClick={startAnalysis} disabled={!inputs.analysisReady}><Sparkles /> Analyze these inputs</button>
          </section>
        </div>
      ) : (
        <div className="analysis-page">
          <div className="analysis-context-bar">
            <button onClick={() => setView('inputs')}><ArrowLeft /> View or replace inputs</button>
            <div className="active-inputs"><span><FileCode2 /> {inputs.diagram?.name}</span><span><Database /> {inputs.dcs?.name}</span></div>
          </div>

          <div className="chat-scroll">
            <div className="chat-thread">
              <section className="chat-intro">
                <div className="assistant-avatar"><Sparkles /></div>
                <div><strong>Process Insights</strong><p>I’ve read both files and started with a general operating review. Ask me follow-up questions as you would ask an operations engineer.</p></div>
              </section>

              {turns.map((turn) => {
                const latest = turn.id === latestTurnId;
                return (
                  <article className="chat-turn" key={turn.id} ref={latest ? latestTurnRef : undefined}>
                    {!turn.initial && <div className="operator-message"><div><span>You</span><p>{turn.question}</p></div></div>}
                    <div className="assistant-response">
                      <div className="assistant-avatar"><Sparkles /></div>
                      <div className="assistant-response-body">
                        <div className="speaker-label"><strong>Process Insights</strong><span>{turn.initial ? 'Initial review' : 'Follow-up analysis'}</span></div>
                        {turn.status === 'loading' && <div className="thinking-message"><LoaderCircle className="spin" /><div><strong>Working through the evidence…</strong><p>Checking the process path, operating limits, trends, and signal quality.</p></div></div>}
                        {turn.status === 'error' && <div className="chat-error"><CircleAlert /><div><strong>I couldn’t complete that analysis.</strong><p>{turn.error}</p></div></div>}
                        {turn.status === 'complete' && turn.response && (
                          <>
                            <div className={`conversational-answer ${turn.response.answer.severity}`}>
                              <h2>{turn.response.answer.title}</h2>
                              <p>{turn.response.answer.text}</p>
                              <div className="answer-meta"><span>{Math.round(turn.response.answer.confidence * 100)}% evidence confidence</span><span>{turn.response.answer.window}</span></div>
                            </div>
                            <details className="evidence-drawer" open={latest}>
                              <summary><div><BarChart3 /><span><strong>Supporting evidence</strong><small>Charts, readings, timeline, and process context</small></span></div><ChevronDown /></summary>
                              <div className="evidence-drawer-body"><AgentSurface messages={turn.response.messages} hideSummary /></div>
                            </details>
                          </>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}

              {!loading && turns.length > 0 && <div className="suggestion-group"><span>Useful follow-ups</span><div>{SUGGESTIONS.map((suggestion) => <button key={suggestion} onClick={() => void ask(suggestion)}>{suggestion}</button>)}</div></div>}
            </div>
          </div>

          <footer className="chat-composer-wrap">
            <form className="chat-composer" onSubmit={submitQuestion}>
              <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask a question about the process or data…" aria-label="Ask a question" disabled={loading} />
              <button type="submit" disabled={loading || !question.trim()} aria-label="Send question"><Send /></button>
            </form>
            <p><ShieldCheck /> Advisory analysis only. Confirm findings against plant procedures and field conditions.</p>
          </footer>
        </div>
      )}
    </main>
  );
}
