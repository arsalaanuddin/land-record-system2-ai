import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  CheckSquare, 
  List, 
  Map as MapIcon, 
  FileText, 
  LogOut, 
  KeyRound, 
  Shield, 
  Menu 
} from 'lucide-react';
import './Layout.css';

interface SidebarProps {
  onToggleCollapse?: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onToggleCollapse }) => {
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const role = (localStorage.getItem('role') || 'verifier').toUpperCase();
  const name = localStorage.getItem('name') || 'Officer V. Sharma';
  const designation = localStorage.getItem('designation') || 'Verification Officer';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const handleToggle = () => {
    const next = !isCollapsed;
    setIsCollapsed(next);
    if (onToggleCollapse) onToggleCollapse(next);
  };

  const navItems = [
    { to: '/dashboard', icon: <LayoutDashboard size={20} />, label: 'Central Dashboard' },
    { to: '/dashboard/upload', icon: <Upload size={20} />, label: 'Multilingual Ingestion' },
    { to: '/dashboard/review', icon: <CheckSquare size={20} />, label: 'HITL Review Queue' },
    { to: '/dashboard/records', icon: <List size={20} />, label: 'All Digitized Records' },
    { to: '/dashboard/map', icon: <MapIcon size={20} />, label: 'Cadastral GIS Map' },
    { to: '/dashboard/reports', icon: <FileText size={20} />, label: 'Repository & Audit Logs' },
    { to: '/dashboard/apis', icon: <KeyRound size={20} />, label: 'GovTech APIs & Integrations' },
  ];

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-icon-wrap">
          <Shield size={22} className="logo-shield" />
        </div>
        {!isCollapsed && (
          <div className="logo-titles">
            <h2>LRDS Portal</h2>
            <span className="sub-title">Land Records AI · Telangana</span>
          </div>
        )}
        <button className="collapse-btn" onClick={handleToggle} title="Toggle Sidebar">
          <Menu size={18} />
        </button>
      </div>

      {!isCollapsed && (
        <div className="user-profile-badge">
          <div className="avatar-circle">
            {name.charAt(0)}
          </div>
          <div className="profile-info">
            <span className="officer-name">{name}</span>
            <span className="officer-role-tag">{role}</span>
            <span className="officer-desc">{designation}</span>
          </div>
        </div>
      )}

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink 
            key={item.to} 
            to={item.to}
            end={item.to === '/dashboard'}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            title={item.label}
          >
            {item.icon}
            {!isCollapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="nav-item logout-btn" onClick={handleLogout} title="Logout">
          <LogOut size={20} />
          {!isCollapsed && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
};

