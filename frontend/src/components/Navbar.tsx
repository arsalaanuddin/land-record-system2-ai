import React from 'react';
import './Layout.css';

export const Navbar: React.FC = () => {
  return (
    <header className="top-banner-bar">
      <div className="banner-left">
        <span className="env-pill">Local deployment (Telangana v1)</span>
        <span className="divider">•</span>
        <span className="banner-text">AI-Powered Land Record Digitization &amp; Validation System</span>
      </div>
      <div className="banner-right">
        <span className="live-status-dot"></span>
        <span className="live-status-text">
          Self-hosted · no government registry connection configured
        </span>
      </div>
    </header>
  );
};

