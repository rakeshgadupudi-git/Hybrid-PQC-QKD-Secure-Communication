import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import LiveHandshake from './pages/LiveHandshake';
import SideBySide from './pages/SideBySide';
import AttackLab from './pages/AttackLab';
import Bb84Lab from './pages/Bb84Lab';
import CompareModes from './pages/CompareModes';
import Benchmarks from './pages/Benchmarks';
import About from './pages/About';
import HonestLimits from './components/HonestLimits';

const NAV = [
  { to: '/', label: '🔐 Live Handshake' },
  { to: '/side-by-side', label: '⚔️ Side-by-Side' },
  { to: '/attack-lab', label: '🧪 Attack Lab' },
  { to: '/bb84-lab', label: '🔬 BB84 Lab' },
  { to: '/compare', label: '📊 Compare' },
  { to: '/benchmarks', label: '⏱️ Benchmarks' },
  { to: '/about', label: 'ℹ️ About' },
];

function App() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    document.documentElement.classList.toggle('light', !dark);
  }, [dark]);

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        {/* Navigation */}
        <nav className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-border">
          <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
            <div className="flex items-center gap-1 mr-6">
              <span className="text-lg font-bold bg-gradient-to-r from-alice to-pqc bg-clip-text text-transparent">
                Hybrid QKD-PQC
              </span>
            </div>
            <div className="flex items-center gap-1 overflow-x-auto">
              {NAV.map((n) => (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === '/'}
                  className={({ isActive }) =>
                    isActive ? 'nav-link-active whitespace-nowrap' : 'nav-link whitespace-nowrap'
                  }
                >
                  {n.label}
                </NavLink>
              ))}
            </div>
            <button
              className="ml-4 btn-secondary text-xs"
              onClick={() => setDark((d) => !d)}
            >
              {dark ? '☀️ Light' : '🌙 Dark'}
            </button>
          </div>
        </nav>

        {/* Content */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<LiveHandshake />} />
            <Route path="/side-by-side" element={<SideBySide />} />
            <Route path="/attack-lab" element={<AttackLab />} />
            <Route path="/bb84-lab" element={<Bb84Lab />} />
            <Route path="/compare" element={<CompareModes />} />
            <Route path="/benchmarks" element={<Benchmarks />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </main>

        <HonestLimits />
      </div>
    </BrowserRouter>
  );
}

export default App;
