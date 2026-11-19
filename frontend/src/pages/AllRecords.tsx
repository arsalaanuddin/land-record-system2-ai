import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, LandRecord } from '../services/api';
import { 
  List as ListIcon, 
  Search, 
  Filter, 
  MapPin, 
  Map as MapIcon, 
  Eye, 
  ShieldCheck, 
  FileSpreadsheet
} from 'lucide-react';

export const AllRecords: React.FC = () => {
  const [records, setRecords] = useState<LandRecord[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    api.getRecords().then(setRecords);
  }, []);

  const filteredRecords = records.filter(r => {
    const q = search.toLowerCase();
    const has = (value: string | null) => (value ?? '').toLowerCase().includes(q);
    const matchesSearch =
      has(r.surveyNumber) ||
      has(r.khasraNumber) ||
      has(r.khataNumber) ||
      has(r.ownerName) ||
      has(r.village) ||
      has(r.id);

    const matchesStatus = statusFilter === 'all' || r.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <ListIcon size={26} className="text-primary" />
            Central Digitized Land Records Repository
          </h1>
          <p className="subtitle">
            Searchable registry of all digitized, validated, and georeferenced land parcels.
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">
            <FileSpreadsheet size={16} /> Export CSV/Excel
          </button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div className="input-with-icon" style={{ flex: 1, minWidth: '260px' }}>
            <Search size={18} className="input-icon" />
            <input 
              type="text" 
              className="input-field" 
              placeholder="Search by Record ID, Survey No, Khasra, Khata, Landowner, or Village..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Filter size={16} className="text-muted" />
            <select 
              className="input-field" 
              value={statusFilter} 
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ width: '170px' }}
            >
              <option value="all">All Statuses</option>
              <option value="verified">Verified &amp; Certified</option>
              <option value="review">Needs Review</option>
              <option value="processing">Processing</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="table-container card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>Record ID</th>
              <th>Survey / Khasra</th>
              <th>Khata No.</th>
              <th>Primary Landowner</th>
              <th>Jurisdiction</th>
              <th>Plot Area</th>
              <th>Classification</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.map(record => (
              <tr key={record.id}>
                <td>
                  <strong style={{ fontFamily: 'monospace' }}>{record.id}</strong>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                    SHA: {record.sha256Hash.substring(0, 8)}...
                  </div>
                </td>
                <td>
                  <strong>{record.surveyNumber ?? '—'}</strong>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Khasra: {record.khasraNumber ?? '—'}
                  </div>
                </td>
                <td>
                  <span className="badge badge-info" style={{ fontFamily: 'monospace', fontSize: '0.72rem' }}>
                    {record.khataNumber ?? '—'}
                  </span>
                </td>
                <td>
                  <div style={{ fontWeight: 600 }}>{record.ownerName ?? '—'}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {record.ownershipType ?? 'ownership not classified'}
                  </div>
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.82rem' }}>
                    <MapPin size={13} className="text-muted" />
                    <span>{record.village ?? '—'}, {record.district ?? '—'}</span>
                  </div>
                </td>
                <td>{record.area ?? '—'}</td>
                <td>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {record.landClassification ?? '—'}
                  </span>
                </td>
                <td>
                  <span className={`badge ${record.status === 'verified' ? 'badge-success' : 'badge-warning'}`}>
                    {record.status === 'verified' ? <ShieldCheck size={12} style={{ display: 'inline', marginRight: '3px' }} /> : null}
                    {record.status.toUpperCase()}
                  </span>
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '0.35rem' }}>
                    <button 
                      className="btn btn-secondary btn-sm"
                      onClick={() => navigate(`/dashboard/verification/${record.id}`)}
                      title="Inspect / Edit Record Fields"
                    >
                      <Eye size={14} /> View
                    </button>
                    <button 
                      className="btn btn-secondary btn-sm"
                      onClick={() => navigate(`/dashboard/map?recordId=${record.id}`)}
                      title="View Spatial Cadastral Parcel"
                    >
                      <MapIcon size={14} /> Map
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
