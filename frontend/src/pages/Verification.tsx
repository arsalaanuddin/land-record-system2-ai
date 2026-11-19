import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api, LandRecord } from '../services/api';
import { CheckCircle2, AlertTriangle, ShieldCheck, FileText, MapPin, ArrowLeft, Layers, User, Hash } from 'lucide-react';

const orDash = (value: string | null | undefined) => (value && value.trim() ? value : '—');

export function VerificationStudio() {
  const { recordId } = useParams<{ recordId: string }>();
  const navigate = useNavigate();

  const [record, setRecord] = useState<LandRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const [updatedFields, setUpdatedFields] = useState<Record<string, string>>({});
  const [remarks, setRemarks] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRecordDetails() {
      if (!recordId) return;
      try {
        setLoading(true);
        const data: LandRecord = await api.getRecord(recordId);
        setRecord(data);
        
        // Initialize editable map with all extracted OCR field values
        const initialMap: Record<string, string> = {};
        data.fields?.forEach((f) => {
          initialMap[f.key] = f.value ?? '';
        });
        setUpdatedFields(initialMap);
      } catch (err: unknown) {
        console.error('Failed to load record:', err);
        setError((err as Error).message || 'Failed to fetch record for verification.');
      } finally {
        setLoading(false);
      }
    }

    fetchRecordDetails();
  }, [recordId]);

  const handleFieldChange = (key: string, value: string) => {
    setUpdatedFields(prev => ({ ...prev, [key]: value }));
  };

  const handleVerificationAction = async (action: 'approve' | 'review' | 'reject') => {
    if (!recordId) return;
    try {
      setSubmitting(true);
      const payload = {
        action,
        officer_id: 'OFFICER-7749',
        role: 'tehsildar' as const,
        updated_fields: updatedFields,
        remarks: remarks || 'Verified via AI Verification Studio'
      };

      await api.submitVerification(recordId, payload);
      setSuccessMessage(`Record successfully ${action}ed and saved.`);
      setTimeout(() => {
        navigate('/dashboard/records');
      }, 1500);
    } catch (err: unknown) {
      console.error('Verification submission failed:', err);
      setError((err as Error).message || 'Failed to submit verification review.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="page-container" style={{ textAlign: 'center', padding: '4rem' }}>Loading Verification Studio...</div>;
  }

  if (error || !record) {
    return (
      <div className="page-container" style={{ padding: '2rem' }}>
        <button onClick={() => navigate(-1)} className="btn btn-secondary" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ArrowLeft size={16} /> Back
        </button>
        <div style={{ padding: '1rem', background: 'rgba(244,63,94,0.1)', color: 'var(--error-color)', borderRadius: 'var(--radius-md)' }}>
          {error || 'Record not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in" style={{ paddingBottom: '3rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate(-1)} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ArrowLeft size={16} /> Back to Records
        </button>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className="badge badge-info">Record ID: {record.id}</span>
          <span className={`badge ${(record.confidenceScore ?? 0) > 85 ? 'badge-success' : 'badge-warning'}`}>
            Pipeline Confidence: {record.confidenceScore === null ? 'not available' : `${record.confidenceScore}%`}
          </span>
        </div>
      </div>

      {successMessage && (
        <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'rgba(16,185,129,0.1)', color: 'var(--success-color)', borderRadius: 'var(--radius-md)', fontWeight: 600 }}>
          {successMessage}
        </div>
      )}

      {/* Top Summary Banner */}
      <div className="card" style={{ marginBottom: '1.5rem', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', background: 'var(--bg-main)' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Hash size={14}/> Survey Number</span>
          <strong style={{ fontSize: '1.1rem' }}>{orDash(record.surveyNumber)}</strong>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><User size={14}/> Primary Landowner</span>
          <strong style={{ fontSize: '1.1rem' }}>{orDash(record.ownerName)}</strong>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Layers size={14}/> Total Extent / Area</span>
          <strong style={{ fontSize: '1.1rem' }}>{orDash(record.area)}</strong>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}><MapPin size={14}/> Jurisdiction</span>
          <strong style={{ fontSize: '1.1rem' }}>{orDash(record.district)}, {record.state}</strong>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
        {/* Left Column: All Itemized Extracted Fields & OCR Tokens */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem' }}>
              <FileText size={20} className="text-primary" /> Itemized AI Extracted Fields ({record.fields?.length || 0})
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Review &amp; correct OCR tokens</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '520px', overflowY: 'auto', paddingRight: '0.5rem' }}>
            {record.fields?.map((field) => (
              <div key={field.key} style={{ padding: '0.85rem', background: 'var(--bg-main)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {field.label} <span className="badge badge-secondary" style={{ fontSize: '0.65rem' }}>{field.category}</span>
                  </span>
                  <span style={{ fontSize: '0.75rem', fontWeight: 600, color: (field.confidence ?? 0) > 85 ? 'var(--success-color)' : 'var(--warning-color)' }}>
                    {field.confidence === null ? 'no OCR confidence' : `${field.confidence}% OCR`}
                  </span>
                </div>
                <input 
                  type="text"
                  value={updatedFields[field.key] !== undefined ? updatedFields[field.key] : (field.value ?? '')}
                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                  className="input-field"
                  style={{ width: '100%', padding: '0.5rem', fontSize: '0.9rem' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '0.75rem', marginTop: '0.3rem', fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                  <span>Original text: {field.original_text ?? 'not read'}</span>
                  <span>
                    {field.validation_status.replace('_', ' ')} · {field.verification_status}
                    {field.source.bbox ? ` · page ${field.source.page}` : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Validation, GIS & Tehsildar Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Validation Summary Card */}
          <div className="card">
            <h3 style={{ fontSize: '1.05rem', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={18} className="text-success" /> Field Validation &amp; Cross-Database Checks
            </h3>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                <span>External registry check:</span>
                <strong style={{ color: 'var(--text-muted)', textAlign: 'right' }}>
                  {record.validation?.crossDatabaseChecks?.[0]?.status?.replace('_', ' ') ?? 'not configured'}
                </strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Duplicate Check:</span>
                <strong style={{ color: 'var(--success-color)' }}>{record.validation?.duplicateCheck?.message || 'Unique Record'}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>GIS Spatial Coordinates:</span>
                <strong style={{ color: 'var(--primary-color)' }}>{record.coordinates?.length || 0} Polygon Vertices</strong>
              </div>
            </div>
          </div>

          {/* Officer Remarks & Action Buttons Card */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: 'auto' }}>
            <h3 style={{ fontSize: '1.05rem' }}>Tehsildar Certification &amp; Review</h3>
            
            <div className="input-group">
              <label className="input-label">Officer Remarks / Audit Notes</label>
              <textarea 
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Enter review remarks or corrections notes..."
                className="input-field"
                rows={3}
                style={{ resize: 'vertical' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <button 
                onClick={() => handleVerificationAction('approve')} 
                disabled={submitting}
                className="btn btn-primary"
                style={{ background: 'var(--success-color)', borderColor: 'var(--success-color)', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
              >
                <CheckCircle2 size={16} /> Approve &amp; Certify
              </button>
              <button 
                onClick={() => handleVerificationAction('review')} 
                disabled={submitting}
                className="btn btn-secondary"
                style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem' }}
              >
                <AlertTriangle size={16} /> Flag for Audit
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}