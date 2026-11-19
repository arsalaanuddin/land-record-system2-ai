import React, { useEffect, useState } from 'react';
import { 
  FileText, 
  Download, 
  ShieldCheck, 
  Database, 
  Search, 
  CheckCircle2, 
  FileCode,
  Lock
} from 'lucide-react';
import { api, AuditLogEntry, LandRecord } from '../services/api';

export const Reports: React.FC = () => {
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [records, setRecords] = useState<LandRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'audit' | 'repository'>('audit');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    api.getAuditLogs().then(setAuditLogs);
    api.getRecords().then(setRecords);
  }, []);

  const q = searchTerm.toLowerCase();
  const has = (value: string | null | undefined) => (value ?? '').toLowerCase().includes(q);
  const filteredLogs = auditLogs.filter(log =>
    has(log.recordId) || has(log.user) || has(log.details) || has(log.fieldChanged),
  );

  const filteredRecords = records.filter(
    rec => has(rec.id) || has(rec.surveyNumber) || has(rec.ownerName) || has(rec.documentType),
  );

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <FileText size={26} className="text-primary" />
            Document Repository &amp; Compliance Audit Trails
          </h1>
          <p className="subtitle">
            SHA-256 document archiving with field-level audit history stored locally. No government portal submission is configured.
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">
            <Download size={16} /> Export Audit Log (PDF)
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="card" style={{ marginBottom: '1.25rem', padding: '0.75rem 1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button 
              className={`btn ${activeTab === 'audit' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              onClick={() => setActiveTab('audit')}
            >
              <ShieldCheck size={16} /> Immutable System Audit Trail ({auditLogs.length})
            </button>
            <button 
              className={`btn ${activeTab === 'repository' ? 'btn-primary' : 'btn-secondary'} btn-sm`}
              onClick={() => setActiveTab('repository')}
            >
              <Database size={16} /> Secure Document Archive ({records.length})
            </button>
          </div>

          <div className="input-with-icon" style={{ width: '280px' }}>
            <Search size={16} className="input-icon" />
            <input 
              type="text" 
              className="input-field input-field-sm" 
              placeholder="Search audit trail or repository..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {activeTab === 'audit' ? (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Record ID</th>
                  <th>Officer / User</th>
                  <th>Role</th>
                  <th>Action</th>
                  <th>Field Edit History (Old → New)</th>
                  <th>Compliance Details</th>
                  <th>Client IP</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map(log => (
                  <tr key={log.id}>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                      {log.timestamp}
                    </td>
                    <td>
                      <strong style={{ fontFamily: 'monospace' }}>{log.recordId}</strong>
                    </td>
                    <td style={{ fontWeight: 600 }}>{log.user}</td>
                    <td>
                      <span className="badge badge-info" style={{ fontSize: '0.68rem' }}>
                        {log.role.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        log.action === 'VERIFY_APPROVE' ? 'badge-success' :
                        log.action === 'FIELD_EDIT' ? 'badge-warning' : 'badge-info'
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td>
                      {log.fieldChanged ? (
                        <div style={{ fontSize: '0.78rem' }}>
                          <span style={{ fontWeight: 600 }}>{log.fieldChanged}:</span>
                          <span style={{ color: 'var(--error-color)', textDecoration: 'line-through', marginLeft: '4px' }}>
                            {log.oldValue}
                          </span>
                          <span style={{ margin: '0 4px', color: 'var(--text-dim)' }}>→</span>
                          <span style={{ color: 'var(--success-color)', fontWeight: 600 }}>
                            {log.newValue}
                          </span>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>N/A (System Event)</span>
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {log.details}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      {log.ipAddress}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Document Type</th>
                  <th>Primary Landowner</th>
                  <th>Survey / Khasra</th>
                  <th>SHA-256 Tamper-Proof Checksum</th>
                  <th>Digital Sign Status</th>
                  <th>Archive Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map(rec => (
                  <tr key={rec.id}>
                    <td>
                      <strong style={{ fontFamily: 'monospace' }}>{rec.id}</strong>
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{rec.documentType}</div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Language: {rec.documentLanguage}</span>
                    </td>
                    <td>{rec.ownerName ?? '—'}</td>
                    <td>{rec.surveyNumber ?? '—'} ({rec.village ?? '—'})</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <Lock size={13} className="text-muted" />
                        <span style={{ fontFamily: 'monospace', fontSize: '0.75rem', background: '#f1f3f5', padding: '0.15rem 0.4rem', borderRadius: '4px' }}>
                          {rec.sha256Hash.substring(0, 24)}...
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${rec.status === 'verified' ? 'badge-success' : 'badge-warning'}`}>
                        {rec.status === 'verified' ? (
                          <>
                            <CheckCircle2 size={12} style={{ display: 'inline', marginRight: '3px' }} />
                            e-Signed (Tehsildar)
                          </>
                        ) : 'Pending Sign'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.35rem' }}>
                        <button className="btn btn-secondary btn-sm" title="Download Original Scanned PDF">
                          <Download size={13} /> Original Scan
                        </button>
                        <button className="btn btn-secondary btn-sm" title="Export GeoJSON Spatial Geometry">
                          <FileCode size={13} /> GeoJSON
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
