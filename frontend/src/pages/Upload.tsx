import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Upload, Cpu, FileText } from 'lucide-react';

export function UploadComponent() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Dynamic UI Form States
  const [language, setLanguage] = useState<string>('auto');
  const [documentType, setDocumentType] = useState<string>('pahani');
  const [stateSelection, setStateSelection] = useState<string>('telangana');
  const [districtSelection, setDistrictSelection] = useState<string>('');

  const [enableDenoise, setEnableDenoise] = useState<boolean>(true);
  
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMessage(null);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMessage('Please select a land record document to upload.');
      return;
    }

    try {
      setLoading(true);
      setErrorMessage(null);

      const response = await api.uploadDocument({
        file: selectedFile,
        language,
        documentType,
        state: stateSelection,
        district: districtSelection,
        enableDenoise,
      });

      if (response.documentId) {
        navigate(`/dashboard/processing/${response.documentId}`);
      } else {
        setErrorMessage('Upload succeeded, but no documentId was returned.');
      }
    } catch (error: unknown) {
      console.error('Upload failed:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Failed to upload document to FastAPI backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Upload size={26} className="text-primary" />
            Multilingual Land Document Ingestion
          </h1>
          <p className="subtitle">
            Upload historical scanned land registers, handwritten PDFs, sale deeds, or cadastral maps for AI extraction.
          </p>
        </div>
      </div>

      {errorMessage && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(244,63,94,0.1)', color: 'var(--error-color)', borderRadius: 'var(--radius-md)' }}>
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleUploadSubmit} style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '1.5rem' }}>
        {/* Left: Drag & Drop Dropzone */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '420px', textAlign: 'center', border: '2px dashed var(--border-color)' }}>
          <div style={{ background: 'var(--primary-glow)', padding: '1rem', borderRadius: '50%', marginBottom: '1rem' }}>
            <Upload size={36} style={{ color: 'var(--primary-color)' }} />
          </div>
          <h3 style={{ marginBottom: '0.5rem' }}>Drag &amp; Drop Historical Land Records</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '320px', marginBottom: '1.5rem' }}>
            Supports scanned high-res PDFs, TIFF, JPEG, PNG registers, and Cadastral Map blueprints.
          </p>
          <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
            Browse Files on System
            <input type="file" onChange={handleFileChange} accept=".pdf,.png,.jpg,.jpeg,.tiff" style={{ display: 'none' }} />
          </label>
          {selectedFile && (
            <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: 'var(--success-color)', fontWeight: 600 }}>
              Selected: {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
            </p>
          )}

          <div style={{ marginTop: '2rem', padding: '1rem', background: 'var(--bg-main)', borderRadius: 'var(--radius-md)', width: '100%', textAlign: 'left' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.85rem' }}>
              <Cpu size={16} className="text-primary" /> Deep Learning Indic OCR Stack
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Printed text is read with PaddleOCR using a Telugu recogniser. Handwriting regions without an installed recogniser are flagged for human transcription rather than guessed.
            </p>
          </div>
        </div>

        {/* Right: Pipeline Settings */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.1rem' }}>Extraction Pipeline Settings</h3>
            <span className="badge badge-info">V2.4 ENGINE</span>
          </div>

          <div className="input-group">
            <label className="input-label">Document Language / Script</label>
            <select value={language} onChange={(e) => setLanguage(e.target.value)} className="input-field">
              <option value="auto">Auto (Telugu + English printed text)</option>
              <option value="te">Telugu</option>
              <option value="en">English</option>
            </select>
          </div>

          <div className="input-group">
            <label className="input-label">Document Type &amp; Jurisdiction Template</label>
            <select value={documentType} onChange={(e) => setDocumentType(e.target.value)} className="input-field">
              <option value="pahani">Pahani / Record of Rights (Telangana)</option>
              <option value="ror_1b">ROR-1B (Telangana)</option>
              <option value="pattadar_passbook">Pattadar Passbook</option>
              <option value="sale_deed">Sale Deed (SRO)</option>
              <option value="mutation_register">Mutation Register</option>
              <option value="">Let the pipeline classify it</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            <div className="input-group">
              <label className="input-label" style={{ fontSize: '0.75rem' }}>State Jurisdiction</label>
              <select value={stateSelection} onChange={(e) => setStateSelection(e.target.value)} className="input-field" style={{ fontSize: '0.85rem' }}>
                <option value="telangana">Telangana (v1)</option>
              </select>
            </div>
            <div className="input-group">
              <label className="input-label" style={{ fontSize: '0.75rem' }}>District / Revenue Circle</label>
              <input 
                type="text" 
                value={districtSelection} 
                onChange={(e) => setDistrictSelection(e.target.value)} 
                className="input-field" 
                style={{ fontSize: '0.85rem', padding: '0.5rem' }} 
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem', padding: '0.25rem 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={enableDenoise} onChange={(e) => setEnableDenoise(e.target.checked)} />
              <span><strong>Computer Vision Preprocessing &amp; Deskewing</strong><br/><span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>OpenCV contrast enhancement (CLAHE), binarization &amp; noise removal</span></span>
            </label>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', paddingLeft: '1.5rem' }}>
              Cadastral vectorisation and government-registry cross-checks are not configured in this build; the
              record will show them as not configured rather than reporting a match.
            </div>
          </div>

          <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid rgba(245, 158, 11, 0.2)', fontSize: '0.75rem', color: 'var(--warning-color)' }}>
            ⚡ Records with extraction confidence below 85% or detected validation discrepancies will be automatically routed to the Human-in-the-Loop Review Queue.
          </div>

          <button type="submit" disabled={loading || !selectedFile} className="btn btn-primary" style={{ width: '100%', padding: '0.85rem', marginTop: 'auto' }}>
            <FileText size={18} /> {loading ? 'Running AI Pipeline...' : 'Launch Automated Digitization Pipeline'}
          </button>
        </div>
      </form>
    </div>
  );
}