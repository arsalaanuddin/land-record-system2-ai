import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, UserRole } from '../services/api';
import { ShieldCheck, User, Award, Briefcase, ChevronRight } from 'lucide-react';
import './Login.css';

const ROLES: { id: UserRole; title: string; desc: string; defaultUser: string }[] = [
  { id: 'operator', title: 'Data Entry Operator', desc: 'Document ingestion, scanning & draft edits', defaultUser: 'OPERATOR_DESAI' },
  { id: 'verifier', title: 'Verification Officer (Patwari)', desc: 'Human-in-the-loop review & confidence validation', defaultUser: 'OFFICER_SHARMA' },
  { id: 'tehsildar', title: 'Tehsildar / SRO', desc: 'Digital signatures, statutory approval & sealing', defaultUser: 'TEHSILDAR_DESHMUKH' },
  { id: 'admin', title: 'System Administrator', desc: 'System integrations, APIs & audit compliance', defaultUser: 'SYSTEM_ADMIN' },
];

export const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [selectedRole, setSelectedRole] = useState<UserRole>('verifier');
  const [username, setUsername] = useState('OFFICER_SHARMA');
  const navigate = useNavigate();

  const handleRoleSelect = (role: UserRole, defaultUser: string) => {
    setSelectedRole(role);
    setUsername(defaultUser);
  };

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const session = await api.login(username, selectedRole);
      localStorage.setItem('auth', 'true');
      localStorage.setItem('username', session.username);
      localStorage.setItem('name', session.name);
      localStorage.setItem('role', session.role);
      localStorage.setItem('designation', session.designation);
      localStorage.setItem('department', session.department);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card card animate-fade-in">
        <div className="login-header">
          <div className="login-logo">
            <ShieldCheck size={44} color="var(--primary-color)" />
          </div>
          <h1>LRDS Portal</h1>
          <p className="portal-sub">Intelligent Land Record Digitization & Validation System</p>
          <div className="gov-badge">Local session stub • no identity provider configured</div>
        </div>

        <form onSubmit={handleLogin} className="login-form">
          <div className="role-selection-section">
            <label className="input-label">Select Administrative Role (RBAC)</label>
            <div className="role-cards-grid">
              {ROLES.map((role) => (
                <button
                  type="button"
                  key={role.id}
                  className={`role-option-card ${selectedRole === role.id ? 'active' : ''}`}
                  onClick={() => handleRoleSelect(role.id, role.defaultUser)}
                >
                  <div className="role-card-top">
                    <span className="role-title">{role.title}</span>
                    {selectedRole === role.id && <Award size={16} className="active-icon" />}
                  </div>
                  <span className="role-desc">{role.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Officer / Operator ID</label>
            <div className="input-with-icon">
              <User size={18} className="input-icon" />
              <input
                type="text"
                name="username"
                className="input-field"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter Official ID"
                required
              />
            </div>
          </div>

          <div className="role-auth-banner" style={{ borderColor: 'rgba(245, 158, 11, 0.35)' }}>
            <ShieldCheck size={16} />
            <span>
              No password is checked: this build has no user store or identity provider. Selecting a role only
              sets which panels the local UI shows.
            </span>
          </div>

          <div className="role-auth-banner">
            <Briefcase size={16} />
            <span>
              Authenticating as <strong>{ROLES.find(r => r.id === selectedRole)?.title}</strong>
            </span>
          </div>

          <button type="submit" className="btn btn-primary login-btn" disabled={loading}>
            {loading ? 'Opening local session...' : 'Continue to Portal'}
            <ChevronRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};
