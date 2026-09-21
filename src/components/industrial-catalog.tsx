'use client';

import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  CircleGauge,
  Info,
  Minus,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  TriangleAlert,
  ZoomIn,
} from 'lucide-react';
import { useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { z } from 'zod';
import { Catalog } from '@a2ui/web_core/v0_9';
import {
  createComponentImplementation,
  type ReactComponentImplementation,
} from '@a2ui/react/v0_9';

export const INDUSTRIAL_CATALOG_ID = 'https://fieldguide.demo/a2ui/catalogs/industrial/v1';

const layoutApi = {
  name: 'ResponseLayout',
  schema: z.object({
    children: z.array(z.string()),
    intent: z.string(),
    question: z.string(),
  }),
};

const ResponseLayout = createComponentImplementation(
  layoutApi,
  ({ props, buildChild }) => (
    <section className="agent-response" aria-label={`Agent response for: ${props.question}`}>
      <div className="a2ui-proof-row">
        <span><span className="protocol-dot" /> A2UI v0.9.1 rendered</span>
        <span>{props.intent.replace('_', ' ')} layout</span>
      </div>
      {props.children.map((child: string) => (
        <div className="a2ui-child" key={child}>{buildChild(child)}</div>
      ))}
    </section>
  ),
);

const summaryApi = {
  name: 'OperationalSummary',
  schema: z.object({
    title: z.string(),
    explanation: z.string(),
    severity: z.enum(['normal', 'warning', 'alarm', 'data']),
    confidence: z.number(),
    window: z.string(),
    tags: z.array(z.string()),
    qualityNote: z.string(),
  }),
};

const OperationalSummary = createComponentImplementation(summaryApi, ({ props }) => (
  <article className={`summary-card ${props.severity}`}>
    <div className="summary-icon">
      {props.severity === 'normal' ? <CheckCircle2 size={20} /> : props.severity === 'data' ? <ShieldAlert size={20} /> : <Sparkles size={20} />}
    </div>
    <div className="summary-body">
      <div className="summary-meta">
        <span>{props.severity === 'normal' ? 'PROCESS STATUS' : props.severity === 'data' ? 'DATA QUALITY' : 'EVIDENCE-BASED INSIGHT'}</span>
        <span>{Math.round(props.confidence * 100)}% confidence</span>
        <span>{props.window}</span>
      </div>
      <h2>{props.title}</h2>
      <p>{props.explanation}</p>
      {props.tags.length > 0 && <div className="tag-list">{props.tags.map((tag: string) => <span key={tag}>{tag}</span>)}</div>}
      {props.qualityNote && <div className="quality-note"><Info size={13} /> {props.qualityNote}</div>}
    </div>
  </article>
));

const kpiCardSchema = z.object({
  tag: z.string(),
  value: z.number().nullable(),
  unit: z.string(),
  quality: z.string(),
  state: z.string(),
  normalText: z.string(),
  timestamp: z.string(),
});
const kpiApi = { name: 'KpiGrid', schema: z.object({ title: z.string(), cards: z.array(kpiCardSchema) }) };

const KpiGrid = createComponentImplementation(kpiApi, ({ props }) => (
  <section aria-labelledby="kpi-heading">
    <div className="section-heading"><div><span>MEASURED EVIDENCE</span><h3 id="kpi-heading">{props.title}</h3></div><span>Units shown at source</span></div>
    <div className="response-kpi-grid">
      {props.cards.map((card) => (
        <article className={`response-kpi ${card.state}`} key={card.tag}>
          <div className="response-kpi-top"><strong>{card.tag}</strong><span className={`quality ${card.quality.toLowerCase()}`}>{card.quality}</span></div>
          <div className="response-kpi-value">{card.value === null ? '—' : card.value.toFixed(card.unit === 'bar' ? 2 : 1)} <span>{card.unit.replace('m3', 'm³')}</span></div>
          <div className="response-kpi-limit">{card.state !== 'normal' ? <TriangleAlert size={12} /> : <CheckCircle2 size={12} />}{card.normalText.replace('m3', 'm³')}</div>
          <time>{card.timestamp.slice(11, 16)}</time>
        </article>
      ))}
    </div>
  </section>
));

const seriesItem = z.object({
  timestamp: z.string(),
  time: z.string(),
  'FT-101': z.number().nullable().optional(),
  'PT-101': z.number().nullable().optional(),
  'LT-101': z.number().nullable().optional(),
  'LT-102': z.number().nullable().optional(),
});
const trendApi = {
  name: 'TrendChart',
  schema: z.object({ title: z.string(), subtitle: z.string(), series: z.array(seriesItem), incidentStart: z.string(), incidentEnd: z.string(), incidentLabel: z.string() }),
};

const TrendChart = createComponentImplementation(trendApi, ({ props }) => (
  <article className="response-panel trend-panel">
    <div className="section-heading"><div><span>CORRELATED TRENDS</span><h3>{props.title}</h3></div><span>{props.subtitle}</span></div>
    <figure className="chart-wrap" aria-label="Interactive line chart showing pressure, flow, and tank levels">
      <ResponsiveContainer width="100%" height="100%" initialDimension={{ width: 800, height: 310 }}>
        <LineChart data={props.series} margin={{ top: 12, right: 8, left: -22, bottom: 0 }}>
          <CartesianGrid stroke="#e8edef" strokeDasharray="2 4" vertical={false} />
          <XAxis dataKey="time" tick={{ fill: '#788891', fontSize: 10 }} axisLine={{ stroke: '#d9e1e5' }} tickLine={false} minTickGap={28} />
          <YAxis yAxisId="process" domain={[0, 90]} tick={{ fill: '#788891', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis yAxisId="pressure" orientation="right" domain={[0, 7]} tick={{ fill: '#788891', fontSize: 10 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #d7e0e4', boxShadow: '0 10px 30px rgba(23,36,46,.12)', fontSize: 11 }} labelStyle={{ color: '#667883', marginBottom: 6 }} />
          <Legend iconType="plainline" iconSize={16} wrapperStyle={{ fontSize: 10, paddingTop: 8 }} />
          {props.incidentStart && props.incidentEnd && <ReferenceArea x1={props.incidentStart} x2={props.incidentEnd} fill="#edb03c" fillOpacity={0.1} strokeOpacity={0} />}
          <Line yAxisId="process" type="monotone" dataKey="FT-101" name="FT-101 · m³/h" stroke="#1876a5" strokeWidth={2.3} dot={false} connectNulls={false} />
          <Line yAxisId="pressure" type="monotone" dataKey="PT-101" name="PT-101 · bar" stroke="#be443f" strokeWidth={2.2} dot={false} connectNulls={false} />
          <Line yAxisId="process" type="monotone" dataKey="LT-101" name="LT-101 · %" stroke="#da941c" strokeWidth={2} dot={false} connectNulls={false} />
          <Line yAxisId="process" type="monotone" dataKey="LT-102" name="LT-102 · %" stroke="#728790" strokeWidth={1.6} strokeDasharray="4 3" dot={false} connectNulls={false} />
        </LineChart>
      </ResponsiveContainer>
    </figure>
    <div className="chart-foot"><span>{props.incidentStart ? <i className="incident-swatch" /> : <CheckCircle2 size={13} />}{props.incidentLabel}</span><span>Hover for exact readings</span></div>
  </article>
));

const timelineEvent = z.object({
  timestamp: z.string(), time: z.string(), label: z.string(), tag: z.string(), value: z.number(), unit: z.string(), severity: z.string(),
});
const timelineApi = { name: 'IncidentTimeline', schema: z.object({ title: z.string(), events: z.array(timelineEvent) }) };

const IncidentTimeline = createComponentImplementation(timelineApi, ({ props }) => (
  <article className="response-panel timeline-panel" id="timeline">
    <div className="section-heading"><div><span>EVENT SEQUENCE</span><h3>{props.title}</h3></div><span>Chronological · calculated</span></div>
    <ol className="event-list">
      {props.events.map((event, index) => (
        <li key={`${event.timestamp}-${event.tag}`}>
          <div className={`event-marker ${event.severity}`}>{index + 1}</div>
          <time>{event.time}</time>
          <div><strong>{event.label}</strong><span>{event.tag} · {event.value.toFixed(event.unit === 'bar' ? 2 : 1)} {event.unit.replace('m3', 'm³')}</span></div>
        </li>
      ))}
    </ol>
  </article>
));

const qualityProblem = z.object({
  tag: z.string(), count: z.number(), first: z.string(), last: z.string(), qualities: z.array(z.string()), impact: z.string(),
});
const qualityApi = { name: 'SensorQualityWarning', schema: z.object({ title: z.string(), problems: z.array(qualityProblem) }) };

const SensorQualityWarning = createComponentImplementation(qualityApi, ({ props }) => (
  <article className="quality-warning">
    <div className="quality-warning-icon"><ShieldAlert size={21} /></div>
    <div><span>QUALITY LIMITATION</span><h3>{props.title}</h3><p>Calculations automatically exclude unavailable values. Review the historian interface before relying on this window.</p></div>
    <div className="quality-count">{props.problems.reduce((total, item) => total + item.count, 0)}<span>affected samples</span></div>
  </article>
));

const diagramApi = { name: 'ProcessDiagram', schema: z.object({ title: z.string(), highlightedTags: z.array(z.string()), status: z.enum(['normal', 'warning', 'alarm']) }) };
const assetInfo: Record<string, { label: string; sensor: string; detail: string }> = {
  'T-101': { label: 'Feed tank', sensor: 'LT-101', detail: 'Level rose while transfer flow fell.' },
  'P-101': { label: 'Centrifugal pump', sensor: 'PT-101 · P-101_STATUS', detail: 'Pump remained running; discharge pressure increased.' },
  'FT-101': { label: 'Flow transmitter', sensor: 'FT-101', detail: 'Measured flow fell below the 42 m³/h normal limit.' },
  'FV-101': { label: 'Flow control valve', sensor: 'FV-101_POS', detail: 'Commanded open while measured flow remained low.' },
  'T-102': { label: 'Destination tank', sensor: 'LT-102', detail: 'Level increased more slowly during the incident.' },
};

const ProcessDiagram = createComponentImplementation(diagramApi, ({ props }) => {
  const [selected, setSelected] = useState('FV-101');
  const [zoom, setZoom] = useState(1);
  const active = new Set(props.highlightedTags);
  const choose = (tag: string) => setSelected(tag);
  const keyboardChoose = (event: React.KeyboardEvent<SVGGElement>, tag: string) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); choose(tag); }
  };
  return (
    <article className="response-panel diagram-panel" id="process-diagram">
      <div className="section-heading">
        <div><span>PLANT TOPOLOGY</span><h3>{props.title}</h3></div>
        <div className="zoom-controls" aria-label="Diagram zoom controls">
          <button onClick={() => setZoom((value) => Math.min(1.45, value + 0.15))} aria-label="Zoom in"><ZoomIn size={14} /></button>
          <button onClick={() => setZoom((value) => Math.max(.7, value - 0.15))} aria-label="Zoom out"><Minus size={14} /></button>
          <button onClick={() => setZoom(1)} aria-label="Reset zoom"><RotateCcw size={14} /></button>
        </div>
      </div>
      <div className="diagram-layout">
        <div className="response-process-canvas">
          <svg viewBox="0 0 900 265" style={{ transform: `scale(${zoom})` }} aria-label="Clickable synthetic P&ID for the tank transfer process">
            <defs><marker id="response-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill={active.size ? '#dc991f' : '#24759b'} /></marker></defs>
            <path d="M160 137 H745" className={active.size ? 'diagram-flow active' : 'diagram-flow'} markerEnd="url(#response-arrow)" />
            <path d="M227 137 V72 H355" className="diagram-signal" /><path d="M512 137 V72 H626" className="diagram-signal" />
            <g className={`diagram-asset ${active.has('T-101') ? 'active' : ''} ${selected === 'T-101' ? 'selected' : ''}`} role="button" tabIndex={0} onClick={() => choose('T-101')} onKeyDown={(event) => keyboardChoose(event, 'T-101')}>
              <path d="M66 62 H160 V195 Q113 225 66 195 Z" /><path d="M72 151 H154 V190 Q113 214 72 190 Z" className="tank-level" /><text x="113" y="38" className="asset-tag">T-101</text><text x="113" y="241" className="asset-caption">FEED TANK</text>
            </g>
            <g className={`diagram-asset ${active.has('P-101') ? 'active' : ''} ${selected === 'P-101' ? 'selected' : ''}`} role="button" tabIndex={0} onClick={() => choose('P-101')} onKeyDown={(event) => keyboardChoose(event, 'P-101')}>
              <circle cx="270" cy="137" r="37" /><path d="M254 116 L292 137 L254 158 Z" className="pump-fill" /><text x="270" y="199" className="asset-tag">P-101</text><text x="270" y="222" className="asset-caption">PUMP</text>
            </g>
            <g className={`diagram-asset instrument ${active.has('FT-101') ? 'active' : ''} ${selected === 'FT-101' ? 'selected' : ''}`} role="button" tabIndex={0} onClick={() => choose('FT-101')} onKeyDown={(event) => keyboardChoose(event, 'FT-101')}>
              <circle cx="414" cy="137" r="30" /><text x="414" y="134" className="instrument-name">FT</text><text x="414" y="149" className="instrument-id">101</text><text x="414" y="199" className="asset-caption">FLOW</text>
            </g>
            <g className={`diagram-asset ${active.has('FV-101') ? 'active' : ''} ${selected === 'FV-101' ? 'selected' : ''}`} role="button" tabIndex={0} onClick={() => choose('FV-101')} onKeyDown={(event) => keyboardChoose(event, 'FV-101')}>
              <path d="M540 114 L579 137 L540 160 Z M618 114 L579 137 L618 160 Z" /><line x1="579" y1="137" x2="579" y2="91" /><circle cx="579" cy="77" r="13" /><text x="579" y="199" className="asset-tag">FV-101</text><text x="579" y="222" className="asset-caption">CONTROL VALVE</text>
            </g>
            <g className={`diagram-asset ${active.has('T-102') ? 'active' : ''} ${selected === 'T-102' ? 'selected' : ''}`} role="button" tabIndex={0} onClick={() => choose('T-102')} onKeyDown={(event) => keyboardChoose(event, 'T-102')}>
              <path d="M745 62 H839 V195 Q792 225 745 195 Z" /><path d="M751 172 H833 V190 Q792 214 751 190 Z" className="tank-level normal" /><text x="792" y="38" className="asset-tag">T-102</text><text x="792" y="241" className="asset-caption">DESTINATION</text>
            </g>
            <g className={`diagram-asset instrument ${active.has('PT-101') ? 'active' : ''}`}><circle cx="355" cy="72" r="25" /><text x="355" y="69" className="instrument-name">PT</text><text x="355" y="83" className="instrument-id">101</text></g>
            <g className="diagram-asset instrument"><circle cx="626" cy="72" r="25" /><text x="626" y="69" className="instrument-name">FC</text><text x="626" y="83" className="instrument-id">101</text></g>
          </svg>
          <div className="diagram-key"><span className={active.size ? 'active' : ''} /> {active.size ? 'Affected path' : 'Normal process path'}</div>
        </div>
        <aside className="tag-detail">
          <span>SELECTED TAG</span><h4>{selected}</h4><p className="tag-type">{assetInfo[selected].label}</p>
          <dl><div><dt>Related signal</dt><dd>{assetInfo[selected].sensor}</dd></div><div><dt>Evidence</dt><dd>{assetInfo[selected].detail}</dd></div></dl>
          <p className="click-hint"><CircleGauge size={13} /> Select any equipment tag for context</p>
        </aside>
      </div>
    </article>
  );
});

const rowSchema = z.object({ tag: z.string(), type: z.string(), status: z.string(), detail: z.string() });
const equipmentApi = { name: 'EquipmentTable', schema: z.object({ title: z.string(), rows: z.array(rowSchema) }) };
const EquipmentTable = createComponentImplementation(equipmentApi, ({ props }) => (
  <article className="response-panel equipment-panel">
    <div className="section-heading"><div><span>TAG REVIEW</span><h3>{props.title}</h3></div></div>
    <div className="table-scroll"><table><thead><tr><th>Tag</th><th>Type</th><th>Status</th><th>Operational context</th></tr></thead><tbody>{props.rows.map((row) => <tr key={row.tag}><td><strong>{row.tag}</strong></td><td>{row.type}</td><td><span className="table-status">{row.status}</span></td><td>{row.detail}</td></tr>)}</tbody></table></div>
  </article>
));

const inspectionItem = z.object({ priority: z.string(), tag: z.string(), text: z.string() });
const inspectionApi = { name: 'InspectionPanel', schema: z.object({ title: z.string(), confidence: z.number(), items: z.array(inspectionItem) }) };
const InspectionPanel = createComponentImplementation(inspectionApi, ({ props }) => (
  <article className="response-panel inspection-panel">
    <div className="section-heading"><div><span>ADVISORY NEXT STEPS</span><h3>{props.title}</h3></div><span>Confirm in the field</span></div>
    <div className="inspection-list">{props.items.map((item) => <div key={item.priority}><span className="inspection-priority">{item.priority}</span><div><strong>{item.tag}</strong><p>{item.text}</p></div><ChevronRight size={15} /></div>)}</div>
    <div className="safety-note"><AlertTriangle size={14} /><span>Follow site procedures and permits. This prototype cannot command or isolate equipment.</span></div>
  </article>
));

const statusApi = { name: 'StatusState', schema: z.object({ state: z.enum(['loading', 'empty', 'error']), title: z.string(), message: z.string() }) };
const StatusState = createComponentImplementation(statusApi, ({ props }) => (
  <div className={`catalog-status ${props.state}`}><AlertTriangle size={18} /><div><strong>{props.title}</strong><p>{props.message}</p></div></div>
));

export const industrialCatalog = new Catalog<ReactComponentImplementation>(
  INDUSTRIAL_CATALOG_ID,
  [ResponseLayout, OperationalSummary, KpiGrid, TrendChart, IncidentTimeline, SensorQualityWarning, ProcessDiagram, EquipmentTable, InspectionPanel, StatusState],
);
