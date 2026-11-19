import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Server, Settings, FileSearch, CheckCircle2, ShieldCheck, Layers, AlertTriangle } from 'lucide-react';
import { api, DocumentStatusResponse, StageView } from '../services/api';
import './Processing.css';

const STAGE_META: Record<string, { label: string; desc: string; icon: React.ReactNode }> = {
  pdf_render: {
    label: 'Page rendering',
    desc: 'PDF pages rendered to images, checksum recorded',
    icon: <Server size={22} />,
  },
  preprocess: {
    label: 'Preprocessing & quality check',
    desc: 'Contrast enhancement, deskew and measured scan quality',
    icon: <Settings size={22} />,
  },
  ocr: {
    label: 'Printed-text OCR',
    desc: 'PaddleOCR recognition of printed Telugu / English text',
    icon: <FileSearch size={22} />,
  },
  field_extraction: {
    label: 'Field extraction',
    desc: 'Rule-based mapping of OCR lines to Telangana record fields',
    icon: <Layers size={22} />,
  },
  validation: {
    label: 'Field validation',
    desc: 'Required-field and format rules; duplicates checked locally',
    icon: <ShieldCheck size={22} />,
  },
};

const TERMINAL = ['processed', 'needs_review', 'verified', 'rejected', 'failed'];

function statusClass(status: StageView['status']): string {
  if (status === 'completed') return 'completed';
  if (status === 'running') return 'active';
  if (status === 'failed') return 'failed';
  if (status === 'unavailable') return 'unavailable';
  return 'pending';
}

export const Processing: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<DocumentStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!documentId) return;
    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        const next = await api.getDocumentStatus(documentId);
        if (cancelled) return;
        setStatus(next);
        if (TERMINAL.includes(next.status)) {
          navigate(`/dashboard/verification/${documentId}`);
          return;
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Could not read processing status.');
        }
      }
      if (!cancelled) timer = window.setTimeout(poll, 1500);
    };

    poll();
    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [documentId, navigate]);

  const stages = status?.stages ?? [];

  return (
    <div className="processing-container animate-fade-in">
      <div className="processing-card card">
        <div className="processing-badge">Document {documentId}</div>
        <h2 className="processing-title">Land Record Processing</h2>
        <p className="processing-subtitle">
          Live server-side stage status. Nothing here is simulated: unavailable engines are reported as
          unavailable.
        </p>

        {error && (
          <div style={{ marginTop: '1rem', padding: '0.85rem', borderRadius: 'var(--radius-md)', background: 'rgba(244,63,94,0.1)', color: 'var(--error-color)' }}>
            {error}
          </div>
        )}

        <div className="stepper">
          {(stages.length ? stages : Object.keys(STAGE_META).map((name) => ({ name, status: 'pending' as const, message: null }))).map(
            (stage) => {
              const meta = STAGE_META[stage.name] ?? {
                label: stage.name,
                desc: '',
                icon: <Layers size={22} />,
              };
              const cls = statusClass(stage.status);
              return (
                <div key={stage.name} className={`step ${cls}`}>
                  <div className="step-icon">
                    {stage.status === 'completed' ? <CheckCircle2 size={22} className="completed-check" /> : meta.icon}
                    {stage.status === 'running' && <div className="spinner"></div>}
                  </div>
                  <div className="step-content">
                    <div className="step-label-row">
                      <h3>{meta.label}</h3>
                      <span className={`status-badge ${cls}`}>{stage.status.replace('_', ' ')}</span>
                    </div>
                    <p className="step-desc">{stage.message ?? meta.desc}</p>
                  </div>
                </div>
              );
            },
          )}
        </div>

        {status && status.warnings.length > 0 && (
          <div style={{ marginTop: '1.25rem', padding: '0.85rem', background: 'rgba(245,158,11,0.1)', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--warning-color)' }}>
            <strong style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
              <AlertTriangle size={14} /> Warnings ({status.warnings.length})
            </strong>
            <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
              {status.warnings.slice(0, 8).map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
