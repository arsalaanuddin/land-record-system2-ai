import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Map as MapIcon, 
  Layers, 
  Eye, 
  MapPin, 
  Compass, 
  Search,
  ExternalLink
} from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api, LandRecord } from '../services/api';
import './GISMap.css';

// Component to dynamically pan and zoom to selected parcel
const MapController: React.FC<{ targetCoords: [number, number] | null }> = ({ targetCoords }) => {
  const map = useMap();
  useEffect(() => {
    if (targetCoords) {
      map.flyTo(targetCoords, 18, { duration: 1.2 });
    }
  }, [targetCoords, map]);
  return null;
};

export const GISMap: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const requestedId = searchParams.get('recordId');

  const [records, setRecords] = useState<LandRecord[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<LandRecord | null>(null);
  const [showVerifiedOnly, setShowVerifiedOnly] = useState<boolean>(false);
  const [showSatellite, setShowSatellite] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    api.getRecords().then(data => {
      setRecords(data);
      if (requestedId) {
        const found = data.find(r => r.id === requestedId);
        if (found) setSelectedRecord(found);
      }
    });
  }, [requestedId]);

  const filteredRecords = records.filter(r => {
    if (showVerifiedOnly && r.status !== 'verified') return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const has = (value: string | null) => (value ?? '').toLowerCase().includes(q);
      return has(r.surveyNumber) || has(r.ownerName) || has(r.village);
    }
    return true;
  });

  const getParcelColor = (record: LandRecord) => {
    if (selectedRecord?.id === record.id) return '#2563eb';
    if (record.status === 'verified') return '#2e7d32';
    return '#f57f17';
  };

  const centerPoint: [number, number] = selectedRecord && selectedRecord.coordinates.length > 0
    ? selectedRecord.coordinates[0]
    : [17.3850, 78.4867];

  return (
    <div className="page-container animate-fade-in map-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <MapIcon size={26} className="text-primary" />
            Cadastral GIS Map &amp; Spatial Alignment
          </h1>
          <p className="subtitle">
            Cadastral boundary visualization linked to textual revenue records. No cadastral vectorisation or Bhu-Naksha service is configured, so the map is empty until parcel geometry exists.
          </p>
        </div>

        <div className="header-actions">
          <button 
            className={`btn ${showSatellite ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setShowSatellite(!showSatellite)}
          >
            <Layers size={16} /> {showSatellite ? 'Satellite Hybrid WMS' : 'Standard Cadastral Map'}
          </button>
        </div>
      </div>

      {/* Map Control Bar */}
      <div className="card map-toolbar-card">
        <div className="map-toolbar-row">
          <div className="input-with-icon" style={{ flex: 1, maxWidth: '340px' }}>
            <Search size={16} className="input-icon" />
            <input 
              type="text" 
              className="input-field input-field-sm"
              placeholder="Search Survey No, Owner, or Village..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="filter-chips-row">
            <label className="checkbox-chip">
              <input 
                type="checkbox" 
                checked={showVerifiedOnly} 
                onChange={(e) => setShowVerifiedOnly(e.target.checked)} 
              />
              <span>Only Verified Parcels</span>
            </label>
          </div>

          <div className="map-legend">
            <span className="legend-item"><span className="color-dot verified"></span> Verified Parcel</span>
            <span className="legend-item"><span className="color-dot review"></span> Review Needed</span>
            <span className="legend-item"><span className="color-dot selected"></span> Selected</span>
          </div>
        </div>
      </div>

      {/* Main Map + Side Inspector Layout */}
      <div className="map-layout-grid">
        <div className="card map-container-card">
          <MapContainer 
            center={centerPoint} 
            zoom={17} 
            scrollWheelZoom={true}
            style={{ height: '560px', width: '100%', borderRadius: 'var(--radius-md)' }}
          >
            <MapController
              targetCoords={selectedRecord && selectedRecord.coordinates.length > 0 ? selectedRecord.coordinates[0] : null}
            />

            {showSatellite ? (
              <TileLayer
                attribution='&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />
            ) : (
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            )}
            
            {filteredRecords.map(parcel => (
              <Polygon 
                key={parcel.id}
                pathOptions={{ 
                  color: getParcelColor(parcel), 
                  fillColor: getParcelColor(parcel), 
                  fillOpacity: selectedRecord?.id === parcel.id ? 0.65 : 0.4,
                  weight: selectedRecord?.id === parcel.id ? 3.5 : 2
                }} 
                positions={parcel.coordinates}
                eventHandlers={{
                  click: () => setSelectedRecord(parcel)
                }}
              >
                <Popup>
                  <div className="gis-popup-content">
                    <h4>{parcel.ownerName}</h4>
                    <p><strong>Survey No:</strong> {parcel.surveyNumber ?? '—'}</p>
                    <p><strong>Khasra:</strong> {parcel.khasraNumber ?? '—'} | <strong>Khata:</strong> {parcel.khataNumber ?? '—'}</p>
                    <p><strong>Area:</strong> {parcel.area ?? '—'}</p>
                    <p><strong>Status:</strong> {parcel.status.toUpperCase()}</p>
                    <button 
                      className="btn btn-secondary btn-sm w-100" 
                      style={{ marginTop: '0.5rem' }}
                      onClick={() => navigate(`/dashboard/verification/${parcel.id}`)}
                    >
                      <Eye size={13} /> Open Verification Studio
                    </button>
                  </div>
                </Popup>
              </Polygon>
            ))}
          </MapContainer>
        </div>

        {/* Selected Parcel Inspector Side Panel */}
        <div className="card parcel-inspector-card">
          <div className="inspector-header">
            <Compass size={18} className="text-primary" />
            <h3>Spatial Parcel Inspector</h3>
          </div>

          {selectedRecord ? (
            <div className="inspector-details animate-fade-in">
              <div className="inspector-top-meta">
                <span className="record-chip">{selectedRecord.id}</span>
                <span className={`badge ${selectedRecord.status === 'verified' ? 'badge-success' : 'badge-warning'}`}>
                  {selectedRecord.status.toUpperCase()}
                </span>
              </div>

              <div className="inspector-field">
                <label>Primary Landowner</label>
                <p className="field-value primary">{selectedRecord.ownerName ?? '—'}</p>
                <span className="field-note">{selectedRecord.ownershipType ?? 'ownership not classified'}</span>
              </div>

              <div className="inspector-row-grid">
                <div className="inspector-field">
                  <label>Survey No.</label>
                  <p className="field-value">{selectedRecord.surveyNumber ?? '—'}</p>
                </div>
                <div className="inspector-field">
                  <label>Khasra No.</label>
                  <p className="field-value">{selectedRecord.khasraNumber ?? '—'}</p>
                </div>
                <div className="inspector-field">
                  <label>Khata No.</label>
                  <p className="field-value">{selectedRecord.khataNumber ?? '—'}</p>
                </div>
                <div className="inspector-field">
                  <label>Total Plot Area</label>
                  <p className="field-value">{selectedRecord.area ?? '—'}</p>
                </div>
              </div>

              <div className="inspector-field">
                <label>Classification</label>
                <p className="field-value">{selectedRecord.landClassification ?? '—'}</p>
              </div>

              <div className="inspector-field">
                <label>Administrative Jurisdiction</label>
                <div className="jur-text">
                  <MapPin size={14} className="text-muted" />
                  <span>
                    {selectedRecord.village ?? '—'}, Mandal {selectedRecord.tehsil ?? '—'}, Dist. {selectedRecord.district ?? '—'}
                  </span>
                </div>
              </div>

              <div className="inspector-field">
                <label>Mutation &amp; SRO Deed</label>
                <p className="field-sub-value">{selectedRecord.mutationNumber ?? '—'}</p>
                <p className="field-sub-value">{selectedRecord.registrationDeedNo ?? '—'}</p>
              </div>

              <div className="inspector-actions">
                <button 
                  className="btn btn-primary w-100"
                  onClick={() => navigate(`/dashboard/verification/${selectedRecord.id}`)}
                >
                  <ExternalLink size={16} /> Open Verification Studio
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-inspector">
              <p>Click on any cadastral parcel polygon on the map to inspect its spatial and textual attributes.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
