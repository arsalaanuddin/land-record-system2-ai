import React, { useEffect, useState } from 'react';
import { 
  KeyRound, 
  Copy, 
  Check, 
  Layers, 
  Code2, 
  RefreshCw,
  Plus
} from 'lucide-react';
import { api, ApiKeyItem, IntegrationStatus } from '../services/api';

const API_ENDPOINTS = [
  {
    method: 'POST',
    path: '/api/documents/upload',
    desc: 'Accepts a scanned PDF or image, stores it with a SHA-256 checksum and starts the staged pipeline.',
    auth: 'Open in this build (no API keys issued)'
  },
  {
    method: 'GET',
    path: '/api/documents/{documentId}/status',
    desc: 'Returns the real status of each pipeline stage: completed, failed, unavailable or pending.',
    auth: 'Open in this build'
  },
  {
    method: 'GET',
    path: '/api/documents/{documentId}',
    desc: 'Returns extracted fields with original text, OCR and extraction confidence, bbox source and warnings.',
    auth: 'Open in this build'
  },
  {
    method: 'PUT',
    path: '/api/documents/{documentId}/verification',
    desc: 'Persists officer corrections and the verification decision, with a field-level audit trail.',
    auth: 'Open in this build (role selection only)'
  },
  {
    method: 'GET',
    path: '/api/gis/parcels',
    desc: 'Returns stored parcel geometry as GeoJSON. Empty until cadastral vectorisation is implemented.',
    auth: 'Open in this build'
  }
];

export const ApiPortal: React.FC = () => {
  const [data, setData] = useState<{ apiKeys: ApiKeyItem[]; integrations: IntegrationStatus[] } | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    api.getApiPortalData().then(setData);
  }, []);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (!data) return <div className="page-container loading-container">Loading GovTech API gateway...</div>;

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <KeyRound size={26} className="text-primary" />
            GovTech APIs &amp; National System Interoperability
          </h1>
          <p className="subtitle">
            Local REST API for this system. External registry integrations (Bhu-Naksha, Dharani, SRO) are listed as targets only and are not configured in this build.
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary">
            <Plus size={16} /> Generate Government API Key
          </button>
        </div>
      </div>

      {/* Integration Connectivity Health Grid */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3>Live Gateway Integrations Status</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>            Government integrations are not configured in this build, so no sync is claimed.</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => api.getApiPortalData().then(setData)}>
            <RefreshCw size={14} /> Refresh Telemetry
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          {data.integrations.map((item, idx) => (
            <div key={idx} style={{ background: '#f8f9fa', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{item.name}</span>
                <span className={`badge ${item.status === 'ok' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                  {item.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <p style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {item.endpoint}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
                <span>Latency: {item.latency}</span>
                <span>Synced: {item.lastSync}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* API Key Management */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <h3 style={{ marginBottom: '0.5rem' }}>Authorized API Authentication Keys</h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          No API keys are issued yet. Keys created by an administrator will be listed here.
        </p>

        <div className="table-container" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Key Name / Application</th>
                <th>Token Prefix</th>
                <th>Role Scope</th>
                <th>Created</th>
                <th>Last Used</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data.apiKeys.map(k => (
                <tr key={k.id}>
                  <td><strong>{k.name}</strong></td>
                  <td>
                    <code style={{ background: '#f1f3f5', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem' }}>
                      {k.prefix}
                    </code>
                  </td>
                  <td><span className="badge badge-info">{k.role}</span></td>
                  <td>{k.created}</td>
                  <td>{k.lastUsed}</td>
                  <td>
                    <button 
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleCopy(k.prefix, k.id)}
                    >
                      {copiedKey === k.id ? <Check size={14} className="text-success" /> : <Copy size={14} />}
                      {copiedKey === k.id ? 'Copied' : 'Copy Token'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* REST API Endpoints Documentation */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Code2 size={20} className="text-primary" />
          <h3>Open e-Governance RESTful Endpoints (OpenAPI 3.1)</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {API_ENDPOINTS.map((ep, i) => (
            <div key={i} style={{ border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '0.85rem', background: '#fff' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                <span className={`badge ${ep.method === 'POST' ? 'badge-warning' : 'badge-info'}`} style={{ fontWeight: 700, minWidth: '55px', textAlign: 'center' }}>
                  {ep.method}
                </span>
                <code style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  {ep.path}
                </code>
                <span style={{ marginLeft: 'auto', fontSize: '0.72rem', color: 'var(--text-dim)', background: '#f8f9fa', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                  {ep.auth}
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{ep.desc}</p>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            Compliance: ISO 19152 (Land Administration Domain Model - LADM) &amp; Open Geospatial Consortium (OGC WFS/WMS).
          </span>
          <button className="btn btn-secondary btn-sm">
            <Layers size={14} /> Download Swagger / OpenAPI JSON Spec
          </button>
        </div>
      </div>
    </div>
  );
};

