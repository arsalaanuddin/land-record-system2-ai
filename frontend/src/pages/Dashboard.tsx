import React, { useEffect, useState } from 'react';
import { api, DashboardStats } from '../services/api';
import {
  FileText,
  CheckCircle,
  AlertTriangle,
  Activity,
  Target,
  RefreshCw,
  Search,
  XCircle,
  Layers
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(err => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="page-container">
        <div className="card" style={{ padding: '2rem', color: 'var(--error-color)' }}>
          Could not load dashboard statistics: {error}
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="page-container loading-container">
        <RefreshCw size={24} className="spin-icon text-muted" />
        <p>Loading stored statistics...</p>
      </div>
    );
  }

  const typeEntries = Object.entries(stats.byType).filter(([name]) =>
    name.toLowerCase().includes(typeFilter.toLowerCase()),
  );

  return (
    <div className="page-container animate-fade-in dashboard-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Activity size={26} className="text-primary" />
            Land Record Digitization Dashboard
          </h1>
          <p className="subtitle">
            Telangana • counts come from stored documents; accuracy is reported only after a held-out evaluation
          </p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/dashboard/upload')}>
            + Ingest New Land Document
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="stat-card card">
          <div className="stat-icon info"><FileText size={22} /></div>
          <div className="stat-details">
            <h3>Documents Received</h3>
            <p className="stat-value">{stats.totalDocuments.toLocaleString()}</p>
            <span className="stat-trend neutral">{stats.totalProcessed} processed</span>
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-icon success"><CheckCircle size={22} /></div>
          <div className="stat-details">
            <h3>Verified Records</h3>
            <p className="stat-value">{stats.verifiedRecords.toLocaleString()}</p>
            <span className="stat-trend positive">Approved by an officer</span>
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-icon warning"><AlertTriangle size={22} /></div>
          <div className="stat-details">
            <h3>Awaiting Review</h3>
            <p className="stat-value">{stats.requiresReview.toLocaleString()}</p>
            <span className="stat-trend neutral">Missing fields, low confidence or OCR unavailable</span>
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-icon"><XCircle size={22} /></div>
          <div className="stat-details">
            <h3>Failed</h3>
            <p className="stat-value">{stats.failedDocuments.toLocaleString()}</p>
            <span className="stat-trend neutral">Stages that could not complete</span>
          </div>
        </div>

        <div className="stat-card card highlight-card">
          <div className="stat-icon primary-accent"><Target size={22} /></div>
          <div className="stat-details">
            <h3>Extraction Accuracy</h3>
            <p className="stat-value">
              {stats.extractionAccuracy === null ? 'Not measured' : `${stats.extractionAccuracy}%`}
            </p>
            <span className="stat-trend neutral">{stats.accuracyNote}</span>
          </div>
        </div>
      </div>

      <div className="dashboard-two-col">
        <div className="card progress-overview-card">
          <div className="card-header-flex">
            <h3>Pipeline Completion</h3>
            <span className="badge badge-info">{stats.processingProgress}%</span>
          </div>

          <div className="target-progress-bar-wrapper">
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${Math.min(stats.processingProgress, 100)}%` }}></div>
            </div>
            <div className="progress-meta">
              <span className="meta-left">
                <strong>{stats.totalProcessed}</strong> of <strong>{stats.totalDocuments}</strong> documents reached the end of the pipeline
              </span>
              <span className="meta-right">
                Avg OCR confidence:{' '}
                {stats.avgConfidenceScore === null ? 'not available' : `${stats.avgConfidenceScore}%`}
              </span>
            </div>
          </div>

          <div className="progress-milestones">
            <div className="milestone-item">
              <span className="milestone-label">Verified</span>
              <span className="milestone-val">{stats.verifiedRecords}</span>
            </div>
            <div className="milestone-item">
              <span className="milestone-label">Awaiting human review</span>
              <span className="milestone-val">{stats.requiresReview}</span>
            </div>
            <div className="milestone-item">
              <span className="milestone-label">Failed stages</span>
              <span className="milestone-val">{stats.failedDocuments}</span>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.75rem' }}>
            Active-learning retraining runs: {stats.activeLearningRetrainedCount}. Field extraction currently uses
            state-config rules; no LayoutLM model has been trained yet.
          </p>
        </div>

        <div className="card error-stats-card">
          <div className="card-header-flex">
            <h3>
              <AlertTriangle size={18} className="text-warning inline-icon" />
              Processing Warnings
            </h3>
            <span className="badge badge-warning">{stats.errorStats.reduce((sum, item) => sum + item.count, 0)} documents</span>
          </div>
          <p className="section-subtext">Measured causes that route scans to human review.</p>

          {stats.errorStats.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '1rem 0' }}>
              No warnings recorded yet.
            </p>
          ) : (
            <div className="error-list">
              {stats.errorStats.map((err) => (
                <div key={err.type} className="error-stat-row">
                  <div className="error-stat-header">
                    <span className="error-stat-name">{err.type}</span>
                    <span className="error-stat-numbers">{err.count} ({err.percentage}%)</span>
                  </div>
                  <div className="error-bar-bg">
                    <div className="error-bar-fill" style={{ width: `${Math.min(err.percentage, 100)}%`, backgroundColor: err.color }}></div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card state-progress-card">
        <div className="card-header-flex">
          <div>
            <h3>
              <Layers size={20} className="text-primary inline-icon" />
              Documents by Type
            </h3>
            <p className="section-subtext">Counts from stored documents after classification</p>
          </div>
          <div className="input-with-icon search-states">
            <Search size={16} className="input-icon" />
            <input
              type="text"
              placeholder="Filter type..."
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="input-field input-field-sm"
            />
          </div>
        </div>

        {typeEntries.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '1rem 0' }}>
            No documents uploaded yet.
          </p>
        ) : (
          <div className="table-container">
            <table className="state-table">
              <thead>
                <tr>
                  <th>Document Type</th>
                  <th>Documents</th>
                  <th>Share</th>
                </tr>
              </thead>
              <tbody>
                {typeEntries.map(([name, count]) => (
                  <tr key={name}>
                    <td><strong>{name}</strong></td>
                    <td>{count}</td>
                    <td>{stats.totalDocuments ? Math.round((count / stats.totalDocuments) * 100) : 0}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card activity-card">
        <h3>Recent Activity</h3>
        {stats.recentActivity.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', padding: '0.5rem 0' }}>
            No activity recorded yet.
          </p>
        ) : (
          <ul className="activity-list">
            {stats.recentActivity.map((act) => (
              <li key={act.id} className="activity-item">
                <div className={`activity-dot ${act.type}`}></div>
                <div className="activity-info">
                  <p>{act.text}</p>
                  <span className="activity-time">{act.time}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};
