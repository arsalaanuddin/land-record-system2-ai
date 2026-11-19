import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, LandRecord } from '../services/api';
import {
  AlertCircle,
  Eye,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  Search
} from 'lucide-react';

export const ReviewQueue: React.FC = () => {
  const [records, setRecords] = useState<LandRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.getRecords().then(res =>
      setRecords(res.filter(r => r.status === 'review' || (r.confidenceScore !== null && r.confidenceScore < 85))),
    );
  }, []);

  const filtered = records.filter(r => {
    const q = searchTerm.toLowerCase();
    const has = (value: string | null) => (value ?? '').toLowerCase().includes(q);
    return has(r.id) || has(r.surveyNumber) || has(r.ownerName) || has(r.village);
  });

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <AlertCircle size={26} className="text-warning" />
            Human-in-the-Loop Review Queue
          </h1>
          <p className="subtitle">
            Records flagged by business logic rules, cross-database discrepancies, or OCR confidence below 85%.
          </p>
        </div>
        <div className="header-actions">
          <span className="badge badge-warning" style={{ fontSize: '0.85rem', padding: '0.4rem 0.8rem' }}>
            {records.length} Requiring Action
          </span>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="input-with-icon" style={{ flex: 1 }}>
            <Search size={18} className="input-icon" />
            <input
              type="text"
              className="input-field"
              placeholder="Search by Record ID, Survey No, Landowner, or Village..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="table-container card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Record ID</th>
              <th>Document Type</th>
              <th>Jurisdiction (Village / Tehsil)</th>
              <th>Survey / Khasra No.</th>
              <th>Landowner Name</th>
              <th>Flagged Reason</th>
              <th>OCR Confidence</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(record => (
              <tr key={record.id}>
                <td>
                  <strong style={{ fontFamily: 'monospace' }}>{record.id}</strong>
                </td>
                <td>
                  <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                    {record.documentType}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.85rem' }}>
                    <MapPin size={13} className="text-muted" />
                    <span>{record.village ?? '—'}, {record.tehsil ?? '—'}</span>
                  </div>
                </td>
                <td>
                  <strong>{record.surveyNumber ?? '—'}</strong> / {record.khasraNumber ?? '—'}
                </td>
                <td>{record.ownerName ?? '—'}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--warning-color)', fontSize: '0.8rem' }}>
                    <AlertTriangle size={14} />
                    <span>{record.validation.errors[0] || 'Low confidence handwriting'}</span>
                  </div>
                </td>
                <td>
                  <span className={`badge ${(record.confidenceScore ?? 0) < 85 ? 'badge-error' : 'badge-success'}`}>
                    {record.confidenceScore === null ? 'n/a' : `${record.confidenceScore}%`}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => navigate(`/dashboard/verification/${record.id}`)}
                  >
                    <Eye size={14} /> Audit &amp; Resolve
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  <CheckCircle2 size={32} style={{ color: 'var(--success-color)', margin: '0 auto 0.5rem auto' }} />
                  <p>All records have been verified. Zero pending items in this queue.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
