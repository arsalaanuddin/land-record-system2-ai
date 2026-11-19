import { useNavigate } from 'react-router-dom';
import { Check } from 'lucide-react';
import './Splash.css';

export const Splash = () => {
  const navigate = useNavigate();

  const handleStart = () => {
    navigate('/login');
  };

  return (
    <div className="splash-container">
      <div className="splash-content">
        <div className="tick-wrapper">
          <Check size={80} className="golden-tick" strokeWidth={3} />
        </div>
        <h1 className="splash-title">LRDS Portal</h1>
      </div>
      <div className="splash-footer">
        <button className="capsule-btn" onClick={handleStart}>
          Proceed to Login
        </button>
      </div>
    </div>
  );
};
