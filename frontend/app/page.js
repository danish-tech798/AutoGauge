'use client';
'use client';
import LoginPage from './LoginPage';
import './LoginPage.css';

import React, { useState, useEffect } from 'react';
import {
  ChevronRight, Upload, Zap, TrendingUp, Download, Heart, LogOut,
  LayoutGrid, History as HistoryIcon, Bookmark, User, X,
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AuthAPI, EstimationAPI, SavedVehiclesAPI } from '../lib/api';
import jsPDF from 'jspdf';

// ============================================================================
// THEME -- lime/black console aesthetic
// ============================================================================

const THEME = {
  bgDark: '#050505',
  cardBg: '#0D0D0D',
  cardBorder: 'rgba(255,255,255,0.08)',
  accentGreen: '#CCFF00',
  accentVolt: '#00FFD9',
  textPrimary: '#FFFFFF',
  textSecondary: '#8A8F98',
  textTertiary: '#5A5F68',
  danger: '#FF4D4D',
};

const FONTS = {
  display: "'Unbounded', sans-serif",
  body: "'IBM Plex Sans', sans-serif",
};

const LUXURY_BRANDS = ['bmw', 'audi', 'mercedes-benz', 'mercedes', 'jaguar', 'land rover', 'porsche', 'volvo', 'lexus'];
const PREMIUM_BRANDS = ['toyota', 'honda', 'hyundai', 'skoda', 'volkswagen', 'kia', 'ford'];

// ============================================================================
// UTILITIES
// ============================================================================

const formatCurrency = (value) => {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', notation: 'compact', maximumFractionDigits: 0,
  }).format(value);
};

const formatFullCurrency = (value) => {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (num) => new Intl.NumberFormat('en-IN').format(num ?? 0);

const formatDate = (isoString) => {
  if (!isoString) return '';
  try {
    return new Date(isoString.replace(' ', 'T')).toLocaleDateString('en-GB');
  } catch {
    return isoString;
  }
};

const getBrandTier = (brand) => {
  const b = (brand || '').toLowerCase();
  if (LUXURY_BRANDS.includes(b)) return 'LUXURY';
  if (PREMIUM_BRANDS.includes(b)) return 'PREMIUM';
  return 'ECONOMY';
};

const titleCase = (s) => (s || '').replace(/(^|\s)\S/g, (t) => t.toUpperCase());

// ============================================================================
// SHARED COMPONENTS
// ============================================================================

const Panel = ({ children, className = '', style = {}, ...rest }) => (
  <div
    className={`rounded-xl border transition-all duration-300 ease-out ${className}`}
    style={{ background: THEME.cardBg, borderColor: THEME.cardBorder, ...style }}
    {...rest}
  >
    {children}
  </div>
);

const SectionLabel = ({ children }) => (
  <p
    className="text-xs font-semibold uppercase tracking-widest mb-2"
    style={{ color: THEME.accentGreen, fontFamily: FONTS.body }}
  >
    // {children}
  </p>
);

const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const baseStyles = 'font-bold uppercase tracking-wide rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:hover:scale-100 disabled:hover:shadow-none active:scale-95 cursor-pointer';
  const variants = {
    primary: `text-black hover:brightness-110 hover:scale-[1.04] hover:shadow-[0_0_24px_rgba(204,255,0,0.45)]`,
    secondary: `bg-white/5 hover:bg-white/10 text-white border border-white/10 hover:border-[#CCFF00]/60 hover:text-[#CCFF00] hover:scale-[1.03] hover:shadow-[0_0_16px_rgba(204,255,0,0.15)]`,
    ghost: `text-white hover:bg-white/10 hover:text-[#CCFF00]`,
  };
  const sizes = { sm: 'px-3 py-2 text-xs', md: 'px-4 py-3 text-sm', lg: 'px-6 py-4 text-base' };
  const style = variant === 'primary' ? { background: THEME.accentGreen, color: '#000' } : {};
  return (
    <button className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`} style={style} {...props}>
      {children}
    </button>
  );
};

const Input = ({ label, error, ...props }) => (
  <div className="w-full">
    {label && <label className="block text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>{label}</label>}
    <input
      className="w-full px-4 py-3 rounded-lg bg-white/5 border text-white placeholder-gray-600 focus:outline-none transition-all"
      style={{ borderColor: THEME.cardBorder }}
      onFocus={(e) => (e.target.style.borderColor = THEME.accentGreen)}
      onBlur={(e) => (e.target.style.borderColor = THEME.cardBorder)}
      {...props}
    />
    {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
  </div>
);

const Select = ({ label, children, ...props }) => (
  <div className="w-full">
    {label && <label className="block text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>{label}</label>}
    <select
      className="w-full px-4 py-3 rounded-lg bg-white/5 border text-white focus:outline-none"
      style={{ borderColor: THEME.cardBorder }}
      {...props}
    >
      {children}
    </select>
  </div>
);

// ============================================================================
// SHARED DETAIL MODAL
// ============================================================================

const DetailModal = ({ title, subtitle, fields, onClose }) => (
  <div
    className="fixed inset-0 z-50 flex items-center justify-center p-4"
    style={{ background: 'rgba(0,0,0,0.75)' }}
    onClick={onClose}
  >
    <div onClick={(e) => e.stopPropagation()} className="w-full max-w-lg">
      <Panel className="p-6 max-h-[85vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-xs font-semibold uppercase mb-1" style={{ color: THEME.accentGreen }}>// Detail</p>
            <h3 className="text-xl font-bold capitalize" style={{ fontFamily: FONTS.display }}>{title}</h3>
            {subtitle && <p className="text-sm mt-1" style={{ color: THEME.textSecondary }}>{subtitle}</p>}
          </div>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-white/10 transition-colors hover:text-[#CCFF00]">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-2.5 border-t pt-4" style={{ borderColor: THEME.cardBorder }}>
          {fields.map(([k, v]) => (
            <div key={k} className="flex justify-between text-sm gap-4">
              <span style={{ color: THEME.textTertiary }}>{k}</span>
              <span className="font-semibold text-right">{v}</span>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  </div>
);

// ============================================================================
// APP SHELL (sidebar layout)
// ============================================================================

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: LayoutGrid },
  { key: 'wizard', label: 'New Estimation', icon: Zap },
  { key: 'history', label: 'History', icon: HistoryIcon },
  { key: 'saved', label: 'Saved Vehicles', icon: Bookmark },
  { key: 'trends', label: 'Market Trends', icon: TrendingUp },
];

const Sidebar = ({ activePage, onNavigate, user, onLogout }) => (
  <div
    className="w-64 xl:w-72 shrink-0 flex flex-col justify-between border-r"
    style={{ background: THEME.bgDark, borderColor: THEME.cardBorder }}
  >
    <div>
      <div className="p-6 border-b" style={{ borderColor: THEME.cardBorder }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded border flex items-center justify-center" style={{ borderColor: THEME.accentGreen }}>
            <Zap size={16} style={{ color: THEME.accentGreen }} />
          </div>
          <div>
            <p className="font-bold text-lg leading-none" style={{ fontFamily: FONTS.display }}>AutoGauge</p>
            <p className="text-[10px] tracking-widest" style={{ color: THEME.textTertiary }}>EST · 2026</p>
          </div>
        </div>
      </div>

      <div className="p-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest mb-3 px-2" style={{ color: THEME.textTertiary }}>Console</p>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = activePage === item.key || (activePage === 'report' && item.key === 'wizard');
            return (
              <button
                key={item.key}
                onClick={() => onNavigate(item.key)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${active ? '' : 'text-[#8A8F98] hover:bg-white/5 hover:text-[#CCFF00] hover:translate-x-0.5'}`}
                style={active ? {
                  color: THEME.accentGreen,
                  background: 'rgba(204,255,0,0.08)',
                  borderLeft: `2px solid ${THEME.accentGreen}`,
                } : { borderLeft: '2px solid transparent' }}
              >
                <Icon size={16} /> {item.label}
              </button>
            );
          })}
        </nav>

        <p className="text-[10px] font-semibold uppercase tracking-widest mb-3 mt-8 px-2" style={{ color: THEME.textTertiary }}>Account</p>
        <button
          onClick={() => onNavigate('profile')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${activePage === 'profile' ? '' : 'text-[#8A8F98] hover:bg-white/5 hover:text-[#CCFF00] hover:translate-x-0.5'}`}
          style={activePage === 'profile' ? {
            color: THEME.accentGreen,
            background: 'rgba(204,255,0,0.08)',
            borderLeft: `2px solid ${THEME.accentGreen}`,
          } : { borderLeft: '2px solid transparent' }}
        >
          <User size={16} /> Profile
        </button>
      </div>
    </div>

    <div className="p-4 border-t" style={{ borderColor: THEME.cardBorder }}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded flex items-center justify-center font-bold text-black" style={{ background: THEME.accentGreen }}>
          {(user?.name || 'U').charAt(0).toUpperCase()}
        </div>
        <div className="overflow-hidden">
          <p className="text-sm font-semibold truncate">{user?.name || 'User'}</p>
          <p className="text-xs truncate" style={{ color: THEME.textTertiary }}>{user?.email || ''}</p>
        </div>
      </div>
      <Button variant="secondary" size="sm" className="w-full" onClick={onLogout}>
        <LogOut size={14} /> Logout
      </Button>
    </div>
  </div>
);

const AppShell = ({ activePage, onNavigate, user, onLogout, children }) => (
  <div className="h-screen flex overflow-hidden" style={{ background: THEME.bgDark, color: THEME.textPrimary, fontFamily: FONTS.body }}>
    <Sidebar activePage={activePage} onNavigate={onNavigate} user={user} onLogout={onLogout} />
    <div className="flex-1 overflow-y-auto h-screen">
      <div className="max-w-[1700px] mx-auto px-6 md:px-10 lg:px-16 py-8 lg:py-12">{children}</div>
    </div>
  </div>
);

// ============================================================================
// LOGIN / LANDING (split hero + auth)
// ============================================================================
// ============================================================================
// DASHBOARD
// ============================================================================

const StatBox = ({ label, value, sub }) => (
  <Panel className="p-5 cursor-default hover:border-[#CCFF00]/50 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(204,255,0,0.12)]">
    <p className="text-[10px] font-semibold uppercase tracking-widest mb-3" style={{ color: THEME.textTertiary }}>{label}</p>
    <p className="text-3xl font-bold" style={{ fontFamily: FONTS.display }}>{value}</p>
    {sub && <p className="text-xs mt-1" style={{ color: THEME.textSecondary }}>{sub}</p>}
  </Panel>
);

const DashboardPage = ({ user, onNavigate }) => {
  const [loading, setLoading] = useState(true);
  const [totalEstimations, setTotalEstimations] = useState(0);
  const [savedVehicles, setSavedVehicles] = useState(0);
  const [avgPrice, setAvgPrice] = useState(null);
  const [totalPortfolio, setTotalPortfolio] = useState(0);
  const [recent, setRecent] = useState([]);
  const [activityData, setActivityData] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const [statsRes, historyRes] = await Promise.all([
        EstimationAPI.getStatistics(),
        EstimationAPI.getEstimations(100, 0),
      ]);
      if (cancelled) return;

      if (statsRes.success) {
        setTotalEstimations(statsRes.data.total_estimations ?? 0);
        setSavedVehicles(statsRes.data.saved_vehicles ?? 0);
      }

      if (historyRes.success) {
        const items = historyRes.data.items || [];
        if (items.length > 0) {
          const total = items.reduce((s, e) => s + (e.predicted_price || 0), 0);
          setAvgPrice(total / items.length);
          setTotalPortfolio(total);
        }
        setRecent(items.slice(0, 5));

        // Real monthly activity, bucketed from actual created_at dates
        const buckets = {};
        items.forEach((e) => {
          if (!e.created_at) return;
          const d = new Date(e.created_at.replace(' ', 'T'));
          const key = d.toLocaleDateString('en-US', { month: 'short' });
          buckets[key] = (buckets[key] || 0) + 1;
        });
        setActivityData(Object.entries(buckets).map(([month, count]) => ({ month, count })));
      }
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const firstName = (user?.name || '').split(' ')[0] || 'there';

  return (
    <div>
      <Panel className="p-6 mb-8" style={{ borderColor: 'rgba(204,255,0,0.25)', background: 'linear-gradient(135deg, rgba(204,255,0,0.06), transparent)' }}>
        <p className="text-xs font-semibold mb-1" style={{ color: THEME.accentGreen }}>// {greeting.toUpperCase()}</p>
        <h2 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: FONTS.display }}>Welcome back, {firstName}!</h2>
        <p className="text-sm mt-1" style={{ color: THEME.textSecondary }}>Here's what's happening with your valuations.</p>
      </Panel>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatBox label="Total Estimations" value={loading ? '...' : totalEstimations} />
        <StatBox label="Saved Vehicles" value={loading ? '...' : savedVehicles} />
        <StatBox label="Avg Valuation" value={loading ? '...' : formatCurrency(avgPrice)} />
        <StatBox label="Total Portfolio" value={loading ? '...' : formatCurrency(totalPortfolio)} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Panel className="lg:col-span-2 p-6">
          <SectionLabel>Activity</SectionLabel>
          <h3 className="text-xl font-bold mb-6" style={{ fontFamily: FONTS.display }}>Estimation cadence</h3>
          {activityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="month" stroke={THEME.textTertiary} fontSize={11} />
                <YAxis stroke={THEME.textTertiary} fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#111', border: `1px solid ${THEME.accentGreen}` }} />
                <Line type="monotone" dataKey="count" stroke={THEME.accentGreen} strokeWidth={2} dot={{ fill: THEME.accentGreen, r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm py-12 text-center" style={{ color: THEME.textTertiary }}>
              {loading ? 'Loading...' : 'No activity yet.'}
            </p>
          )}
        </Panel>

        <Panel className="p-6">
          <SectionLabel>Quick Launch</SectionLabel>
          <h3 className="text-xl font-bold mb-6" style={{ fontFamily: FONTS.display }}>Shortcuts</h3>
          <div className="space-y-2">
            {[
              ['New Estimation', 'wizard'],
              ['View History', 'history'],
              ['Saved Vehicles', 'saved'],
              ['Market Trends', 'trends'],
            ].map(([label, key]) => (
              <button
                key={key}
                onClick={() => onNavigate(key)}
                className="w-full flex items-center justify-between px-4 py-3 rounded-lg text-sm border transition-all duration-200 hover:border-[#CCFF00]/60 hover:bg-[#CCFF00]/5 hover:translate-x-1 hover:shadow-[0_0_16px_rgba(204,255,0,0.1)]"
                style={{ borderColor: THEME.cardBorder }}
              >
                {label} <ChevronRight size={16} style={{ color: THEME.accentGreen }} />
              </button>
            ))}
          </div>
        </Panel>
      </div>

      <Panel className="p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <SectionLabel>Recent Runs</SectionLabel>
            <h3 className="text-xl font-bold" style={{ fontFamily: FONTS.display }}>Latest estimations</h3>
          </div>
          <button onClick={() => onNavigate('history')} className="text-xs font-semibold uppercase" style={{ color: THEME.accentGreen }}>
            View All →
          </button>
        </div>
        {recent.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-sm mb-4" style={{ color: THEME.textTertiary }}>
              {loading ? 'Loading...' : 'No estimations yet. Kick off your first valuation.'}
            </p>
            {!loading && <Button variant="primary" onClick={() => onNavigate('wizard')}>Start First Estimation</Button>}
          </div>
        ) : (
          <div className="space-y-2">
            {recent.map((e, idx) => (
              <div
                key={e.id ?? idx}
                className="flex justify-between items-center py-3 px-3 -mx-3 rounded-lg border-b last:border-0 cursor-pointer transition-all duration-200 hover:bg-[#CCFF00]/5 hover:border-transparent"
                style={{ borderColor: THEME.cardBorder }}
                onClick={() => onNavigate('history')}
              >
                <div>
                  <p className="font-semibold text-sm capitalize">{e.brand} {e.model}</p>
                  <p className="text-xs" style={{ color: THEME.textTertiary }}>{e.year} • {formatNumber(e.km_driven)} km</p>
                </div>
                <p className="font-bold" style={{ color: THEME.accentGreen }}>{formatCurrency(e.predicted_price)}</p>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
};

// ============================================================================
// WIZARD
// ============================================================================

const StepBox = ({ num, label, state }) => (
  <div className="flex items-center gap-2">
    <div
      className="w-8 h-8 rounded flex items-center justify-center text-xs font-bold border"
      style={{
        borderColor: state === 'pending' ? THEME.cardBorder : THEME.accentGreen,
        color: state === 'pending' ? THEME.textTertiary : THEME.accentGreen,
        background: state === 'active' ? 'rgba(204,255,0,0.1)' : 'transparent',
      }}
    >
      {num}
    </div>
    <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: state === 'pending' ? THEME.textTertiary : THEME.textPrimary }}>
      {label}
    </span>
  </div>
);

const UploadDropzone = ({ onFileSelect, count }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = React.useRef(null);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleDrop = (e) => {
    e.preventDefault(); setIsDragging(false);
    onFileSelect(Array.from(e.dataTransfer.files));
  };
  const handleClick = () => fileInputRef.current?.click();
  const handleFileInputChange = (e) => {
    onFileSelect(Array.from(e.target.files));
    e.target.value = '';
  };

  return (
    <Panel
      className="border-dashed cursor-pointer py-16 text-center"
      style={{ borderStyle: 'dashed', borderColor: isDragging ? THEME.accentGreen : THEME.cardBorder }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/jpg" multiple className="hidden" onChange={handleFileInputChange} />
      <Upload size={28} className="mx-auto mb-4" style={{ color: THEME.accentGreen }} />
      <h3 className="font-bold mb-1">Drop vehicle photos here</h3>
      <p className="text-xs" style={{ color: THEME.textTertiary }}>Or click to browse · JPG / PNG · Up to 6 photos</p>
      {count > 0 && <p className="text-xs mt-4" style={{ color: THEME.accentGreen }}>{count} photo(s) ready</p>}
    </Panel>
  );
};

const WizardPage = ({ onDone }) => {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    photos: [], brand: 'maruti', model: '', year: 2020, km: 45000,
    fuel: 'petrol', transmission: 'manual', city: 'pune', owners: 1,
    bodyType: 'hatchback', condition: 'good',
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [savingVehicle, setSavingVehicle] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  const stepState = (idx) => (idx < step ? 'done' : idx === step ? 'active' : 'pending');

  const handlePhotoUpload = (files) => setFormData({ ...formData, photos: [...formData.photos, ...files] });

  const handleStartAnalysis = async () => {
    setError(''); setIsAnalyzing(true); setStep(2);
    const response = await EstimationAPI.startEstimation(formData);
    setIsAnalyzing(false);
    if (response.success) { setResult(response.data); setStep(3); }
    else { setError(response.error || 'Estimation failed'); setStep(1); }
  };

  const handleSaveVehicle = async () => {
    if (!result?.estimation_id) { setSaveMessage('Cannot save: no estimation ID.'); return; }
    setSavingVehicle(true); setSaveMessage('');
    const vehicleName = `${formData.brand} ${formData.model}`.trim() || 'Unnamed vehicle';
    const response = await SavedVehiclesAPI.saveVehicle(result.estimation_id, vehicleName);
    setSavingVehicle(false);
    setSaveMessage(response.success ? 'Saved to your garage.' : `Save failed: ${response.error}`);
  };

  // jsPDF's built-in fonts (Helvetica) don't reliably render the Rupee
  // glyph (u20B9), which produces broken/garbled characters in the PDF.
  // "Rs." is used instead throughout the PDF export for clean, universally
  // supported ASCII text.
  const pdfMoney = (value) => {
    if (value == null) return 'N/A';
    return 'Rs. ' + Math.round(value).toLocaleString('en-IN');
  };

  const handleDownloadPdf = () => {
    if (!result) return;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    const marginL = 16;
    const marginR = pageWidth - 16;
    const black = [10, 10, 10];
    const lime = [180, 230, 0]; // slightly darker than screen lime for print contrast
    const gray = [110, 110, 110];
    let y = 0;

    const checkPageBreak = (needed = 10) => {
      if (y > 280 - needed) { doc.addPage(); y = 20; }
    };

    const sectionTitle = (text) => {
      checkPageBreak(16);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.setTextColor(...black);
      doc.text(text.toUpperCase(), marginL, y);
      doc.setDrawColor(...lime);
      doc.setLineWidth(0.8);
      doc.line(marginL, y + 2, marginR, y + 2);
      y += 10;
      doc.setFont('helvetica', 'normal');
    };

    const kvRow = (label, value) => {
      checkPageBreak();
      doc.setFontSize(10);
      doc.setTextColor(...gray);
      doc.text(label, marginL, y);
      doc.setTextColor(...black);
      doc.setFont('helvetica', 'bold');
      doc.text(String(value), marginL + 55, y);
      doc.setFont('helvetica', 'normal');
      y += 7;
    };

    // --- Header band ---
    doc.setFillColor(...black);
    doc.rect(0, 0, pageWidth, 26, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(18);
    doc.setTextColor(...lime);
    doc.text('AutoGauge', marginL, 16);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(230, 230, 230);
    doc.text('AI-Powered Vehicle Price Valuation Report', marginL, 22);
    y = 38;

    doc.setFontSize(9);
    doc.setTextColor(...gray);
    doc.text(`Generated: ${new Date().toLocaleString('en-IN')}`, marginL, y);
    y += 12;

    // --- Vehicle Details ---
    sectionTitle('Vehicle Details');
    kvRow('Brand', titleCase(formData.brand));
    kvRow('Model', formData.model || 'N/A');
    kvRow('Year', formData.year);
    kvRow('Kilometers Driven', formatNumber(formData.km) + ' km');
    kvRow('Fuel Type', titleCase(formData.fuel));
    kvRow('Transmission', titleCase(formData.transmission));
    kvRow('City', titleCase(formData.city));
    kvRow('Body Type', titleCase(formData.bodyType));
    kvRow('Previous Owners', formData.owners);
    y += 4;

    // --- Valuation Result ---
    sectionTitle('Valuation Result');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(20);
    doc.setTextColor(...black);
    doc.text(pdfMoney(result.price), marginL, y);
    y += 10;
    doc.setFont('helvetica', 'normal');
    kvRow('Condition Score', `${((result.condition ?? 0) * 100).toFixed(0)} / 100`);
    kvRow(
      'Damage Detected',
      (result.damage && result.damage.length > 0)
        ? result.damage.map((d) => titleCase(d.replace(/_/g, ' '))).join(', ')
        : 'None'
    );
    if (result.perfect_condition_price != null) {
      kvRow('If Perfect Condition', pdfMoney(result.perfect_condition_price));
    }
    y += 4;

    // --- Price Breakdown (zebra-striped table, no external plugin needed) ---
    if (result.breakdown && result.breakdown.length > 0) {
      sectionTitle('Price Breakdown (SHAP Explainability)');
      doc.setFontSize(9.5);
      result.breakdown.forEach((item, idx) => {
        checkPageBreak(9);
        if (idx % 2 === 0) {
          doc.setFillColor(245, 245, 245);
          doc.rect(marginL - 2, y - 5, (marginR - marginL) + 4, 8, 'F');
        }
        doc.setTextColor(...black);
        doc.setFont('helvetica', 'normal');
        doc.text(item.factor, marginL, y);

        const sign = item.impact >= 0 ? '+ ' : '- ';
        const valueText = sign + pdfMoney(Math.abs(item.impact)).replace('Rs. ', 'Rs ');
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(item.impact >= 0 ? 60 : 200, item.impact >= 0 ? 150 : 60, item.impact >= 0 ? 30 : 60);
        doc.text(valueText, marginR, y, { align: 'right' });
        y += 8;
      });
      y += 4;
    }

    // --- Footer ---
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFontSize(8);
      doc.setTextColor(...gray);
      doc.setFont('helvetica', 'italic');
      doc.text(
        'Generated by AutoGauge -- estimate based on an AI model trained on used-vehicle listings. Actual sale price may vary.',
        marginL, 291
      );
      doc.text(`Page ${i} of ${pageCount}`, marginR, 291, { align: 'right' });
    }

    const safeName = (formData.brand || 'vehicle').replace(/[^a-z0-9]/gi, '_');
    doc.save(`AutoGauge_${safeName}_report.pdf`);
  };

  if (isAnalyzing) {
    return (
      <div>
        <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// NEW VALUATION</p>
        <h1 className="text-3xl font-bold mb-8" style={{ fontFamily: FONTS.display }}>Vehicle Estimation Wizard</h1>
        <div className="flex gap-6 mb-10">
          <StepBox num="01" label="Photos" state="done" />
          <StepBox num="02" label="Details" state="done" />
          <StepBox num="03" label="Analysis" state="active" />
          <StepBox num="04" label="Complete" state="pending" />
        </div>
        <div className="text-center py-16">
          <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// ANALYZING</p>
          <h2 className="text-3xl font-bold mb-4" style={{ fontFamily: FONTS.display }}>AI in motion.</h2>
          <p className="text-sm mb-10" style={{ color: THEME.textSecondary }}>Running photo damage detection, SHAP explainability, and price fusion.</p>
          <div className="w-16 h-16 mx-auto rounded-full border-4 animate-spin" style={{ borderColor: 'rgba(255,255,255,0.1)', borderTopColor: THEME.accentGreen }} />
        </div>
      </div>
    );
  }

  if (step === 3 && result) {
    const perfectPrice = result.perfect_condition_price;
    const recoverable = perfectPrice != null ? perfectPrice - result.price : null;
    const marketLow = result.price * 0.93;
    const marketHigh = result.price * 1.07;
    const kmPerYear = formData.km && formData.year ? Math.round(formData.km / Math.max(1, 2026 - formData.year)) : 0;

    return (
      <div>
        <div className="flex justify-between items-center mb-8">
          <div>
            <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// COMPLETE</p>
            <h1 className="text-2xl font-bold" style={{ fontFamily: FONTS.display }}>Estimation Result</h1>
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" size="sm" onClick={handleSaveVehicle} disabled={savingVehicle}>
              <Heart size={14} /> {savingVehicle ? 'Saving...' : 'Save'}
            </Button>
            <Button variant="secondary" size="sm" onClick={handleDownloadPdf}><Download size={14} /> PDF</Button>
            <Button variant="primary" size="sm" onClick={() => { setStep(0); setFormData({ ...formData, photos: [] }); setResult(null); setSaveMessage(''); }}>
              New
            </Button>
          </div>
        </div>

        {saveMessage && (
          <p className={`text-sm mb-4 ${saveMessage.startsWith('Saved') ? 'text-green-400' : 'text-red-400'}`}>{saveMessage}</p>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Panel className="lg:col-span-2 p-8">
            <SectionLabel>Estimated Market Value</SectionLabel>
            <p className="text-sm capitalize mb-2" style={{ color: THEME.textSecondary }}>
              {formData.brand} {formData.model} · {formData.year} · {titleCase(formData.city)}
            </p>
            <p className="text-5xl font-bold mb-6" style={{ fontFamily: FONTS.display, color: THEME.accentGreen, textShadow: `0 0 30px ${THEME.accentGreen}40` }}>
              {formatFullCurrency(result.price)}
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t" style={{ borderColor: THEME.cardBorder }}>
              <div>
                <p className="text-[10px] uppercase" style={{ color: THEME.textTertiary }}>Market Low</p>
                <p className="font-bold">{formatCurrency(marketLow)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase" style={{ color: THEME.textTertiary }}>Market High</p>
                <p className="font-bold">{formatCurrency(marketHigh)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase" style={{ color: THEME.textTertiary }}>Tier</p>
                <p className="font-bold">{getBrandTier(formData.brand)}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase" style={{ color: THEME.textTertiary }}>Km / Year</p>
                <p className="font-bold">{formatNumber(kmPerYear)}</p>
              </div>
            </div>
          </Panel>

          <Panel className="p-6">
            <SectionLabel>Condition Score</SectionLabel>
            <p className="text-4xl font-bold mb-1" style={{ fontFamily: FONTS.display }}>
              {((result.condition ?? 0) * 100).toFixed(0)}<span className="text-lg" style={{ color: THEME.textTertiary }}>/100</span>
            </p>
            <div className="w-full h-1.5 rounded-full mt-3 mb-4" style={{ background: 'rgba(255,255,255,0.08)' }}>
              <div className="h-full rounded-full" style={{ width: `${(result.condition ?? 0) * 100}%`, background: THEME.accentGreen }} />
            </div>
            <p className="text-[10px] uppercase mb-2" style={{ color: THEME.textTertiary }}>Damage Detected</p>
            <div className="flex flex-wrap gap-2 mb-4">
              {(result.damage && result.damage.length > 0) ? result.damage.map((d, i) => (
                <span key={i} className="text-[10px] font-semibold px-2 py-1 rounded border" style={{ color: THEME.danger, borderColor: 'rgba(255,77,77,0.3)' }}>
                  ⚠ {d.replace(/_/g, ' ').toUpperCase()}
                </span>
              )) : <span className="text-xs" style={{ color: THEME.textTertiary }}>None detected</span>}
            </div>
            {perfectPrice != null && (
              <div className="pt-3 border-t" style={{ borderColor: THEME.cardBorder }}>
                <p className="text-[10px] uppercase mb-1" style={{ color: THEME.textTertiary }}>If in perfect condition</p>
                <p className="font-bold" style={{ color: THEME.accentGreen }}>{formatCurrency(perfectPrice)}</p>
                {recoverable > 0 && <p className="text-xs" style={{ color: THEME.textSecondary }}>+{formatCurrency(recoverable)} recoverable</p>}
              </div>
            )}
          </Panel>
        </div>

        <Panel className="p-6">
          <SectionLabel>Price Breakdown</SectionLabel>
          <h3 className="text-lg font-bold mb-4" style={{ fontFamily: FONTS.display }}>Factor contribution</h3>
          {result.breakdown && result.breakdown.length > 0 ? (
            <div className="space-y-3">
              {result.breakdown.map((item, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <span className="text-sm w-40 shrink-0" style={{ color: THEME.textSecondary }}>{item.factor}</span>
                  <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(100, Math.abs(item.impact) / 2000)}%`,
                        background: item.impact >= 0 ? THEME.accentGreen : THEME.danger,
                      }}
                    />
                  </div>
                  <span className="text-sm font-bold w-28 text-right" style={{ color: item.impact >= 0 ? THEME.accentGreen : THEME.danger }}>
                    {item.impact >= 0 ? '+' : '-'}{formatCurrency(Math.abs(item.impact))}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: THEME.textTertiary }}>Breakdown unavailable for this estimation.</p>
          )}
        </Panel>
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// NEW VALUATION</p>
      <h1 className="text-3xl font-bold mb-8" style={{ fontFamily: FONTS.display }}>Vehicle Estimation Wizard</h1>
      <div className="flex gap-6 mb-10">
        <StepBox num="01" label="Photos" state={stepState(0)} />
        <StepBox num="02" label="Details" state={stepState(1)} />
        <StepBox num="03" label="Analysis" state={stepState(2)} />
        <StepBox num="04" label="Complete" state={stepState(3)} />
      </div>

      {error && <Panel className="p-4 mb-6" style={{ borderColor: 'rgba(255,77,77,0.4)' }}><p className="text-red-400 text-sm">{error}</p></Panel>}

      {step === 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <UploadDropzone onFileSelect={handlePhotoUpload} count={formData.photos.length} />
          </div>
          <Panel className="p-6">
            <SectionLabel>Guidance</SectionLabel>
            <h3 className="font-bold mb-3">Better photos = better price</h3>
            <ul className="text-xs space-y-2" style={{ color: THEME.textSecondary }}>
              <li>• Front, rear, and both sides</li>
              <li>• Interior dashboard and seats</li>
              <li>• Any dents, scratches, or damage close-up</li>
              <li>• Odometer reading if possible</li>
            </ul>
          </Panel>
          <div className="lg:col-span-3 flex justify-between mt-2">
            <Button variant="secondary" onClick={() => setStep(1)}>Skip Photos</Button>
            <Button variant="primary" onClick={() => setStep(1)}>Next <ChevronRight size={16} /></Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Select label="Brand" value={formData.brand} onChange={(e) => setFormData({ ...formData, brand: e.target.value })}>
                <option value="maruti">Maruti</option><option value="hyundai">Hyundai</option><option value="honda">Honda</option>
                <option value="toyota">Toyota</option><option value="tata">Tata</option><option value="mahindra">Mahindra</option>
                <option value="volkswagen">Volkswagen</option><option value="ford">Ford</option><option value="bmw">BMW</option>
              </Select>
              <Input label="Model" value={formData.model} onChange={(e) => setFormData({ ...formData, model: e.target.value })} placeholder="e.g., Swift VXi" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>Year ({formData.year})</label>
                <input type="range" min="2000" max="2024" value={formData.year} onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })} className="w-full accent-lime-400" />
              </div>
              <Select label="Fuel Type" value={formData.fuel} onChange={(e) => setFormData({ ...formData, fuel: e.target.value })}>
                <option value="petrol">Petrol</option><option value="diesel">Diesel</option>
                <option value="petrol & cng">Petrol & CNG</option><option value="petrol & lpg">Petrol & LPG</option><option value="electric">Electric</option>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Select label="Transmission" value={formData.transmission} onChange={(e) => setFormData({ ...formData, transmission: e.target.value })}>
                <option value="manual">Manual</option><option value="automatic">Automatic</option>
              </Select>
              <Select label="Body Type" value={formData.bodyType} onChange={(e) => setFormData({ ...formData, bodyType: e.target.value })}>
                <option value="hatchback">Hatchback</option><option value="sedan">Sedan</option><option value="suv">SUV</option>
                <option value="luxury sedan">Luxury Sedan</option><option value="luxury suv">Luxury SUV</option>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Select label="City" value={formData.city} onChange={(e) => setFormData({ ...formData, city: e.target.value })}>
                <option value="pune">Pune</option><option value="mumbai">Mumbai</option><option value="new delhi">New Delhi</option>
                <option value="bengaluru">Bengaluru</option><option value="hyderabad">Hyderabad</option><option value="chennai">Chennai</option><option value="kolkata">Kolkata</option>
              </Select>
              <Input label="Kilometers Driven" type="number" value={formData.km} onChange={(e) => setFormData({ ...formData, km: e.target.value === '' ? 0 : parseInt(e.target.value) })} />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>Previous Owners ({formData.owners})</label>
              <input type="range" min="1" max="5" value={formData.owners} onChange={(e) => setFormData({ ...formData, owners: parseInt(e.target.value) })} className="w-full" />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: THEME.textSecondary }}>Overall Condition</label>
              <div className="grid grid-cols-4 gap-2">
                {['excellent', 'good', 'average', 'poor'].map((c) => (
                  <button
                    key={c}
                    onClick={() => setFormData({ ...formData, condition: c })}
                    className="py-2 rounded-lg text-xs font-semibold uppercase border capitalize"
                    style={{
                      borderColor: formData.condition === c ? THEME.accentGreen : THEME.cardBorder,
                      background: formData.condition === c ? 'rgba(204,255,0,0.08)' : 'transparent',
                      color: formData.condition === c ? THEME.accentGreen : THEME.textSecondary,
                    }}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <Panel className="p-6 h-fit">
            <SectionLabel>Summary</SectionLabel>
            <h3 className="font-bold text-lg mb-4 capitalize">{formData.brand} —</h3>
            <div className="space-y-2 text-sm">
              {[
                ['Year', formData.year], ['Fuel', titleCase(formData.fuel)], ['Transmission', titleCase(formData.transmission)],
                ['Body', titleCase(formData.bodyType)], ['City', titleCase(formData.city)], ['Km', formatNumber(formData.km)],
                ['Owners', formData.owners], ['Condition', titleCase(formData.condition)],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span style={{ color: THEME.textTertiary }}>{k}</span>
                  <span className="font-semibold">{v}</span>
                </div>
              ))}
            </div>
            {formData.photos.length > 0 && (
              <p className="text-xs mt-4" style={{ color: THEME.accentGreen }}>📷 {formData.photos.length} photo(s) ready</p>
            )}
          </Panel>

          <div className="lg:col-span-3 flex justify-between mt-2">
            <Button variant="secondary" onClick={() => setStep(0)}>Back</Button>
            <Button variant="primary" onClick={handleStartAnalysis}>Start Analysis <Zap size={16} /></Button>
          </div>
        </div>
      )}
    </div>
  );
};

// ============================================================================
// HISTORY
// ============================================================================

const buildEstimationFields = (e) => ([
  ['Brand', titleCase(e.brand)],
  ['Model', e.model || 'N/A'],
  ['Year', e.year],
  ['Kilometers Driven', formatNumber(e.km_driven) + ' km'],
  ['Fuel Type', titleCase(e.fuel_type)],
  ['Transmission', titleCase(e.transmission)],
  ['City', titleCase(e.city)],
  ['Body Type', titleCase(e.body_type)],
  ['Owners', e.owner_count ?? 'N/A'],
  ['Condition', titleCase(e.condition) || 'N/A'],
  ['Condition Score', `${((e.condition_score ?? 0) * 100).toFixed(0)} / 100`],
  ['Damage Detected', (e.damage_detected && e.damage_detected.length > 0) ? e.damage_detected.map((d) => titleCase(String(d).replace(/_/g, ' '))).join(', ') : 'None'],
  ['Predicted Price', formatFullCurrency(e.predicted_price)],
  ['Date', formatDate(e.created_at)],
]);

const HistoryPage = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const response = await EstimationAPI.getEstimations(50, 0);
      if (cancelled) return;
      if (response.success) setItems(response.data.items || []);
      else setError(response.error || 'Failed to load history');
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  return (
    <div>
      <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// LOG</p>
      <h1 className="text-3xl font-bold mb-8" style={{ fontFamily: FONTS.display }}>Estimation History</h1>

      {loading && <p className="text-sm" style={{ color: THEME.textTertiary }}>Loading...</p>}
      {!loading && error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && items.length === 0 && <p className="text-sm" style={{ color: THEME.textTertiary }}>No estimations yet.</p>}

      <div className="space-y-3">
        {items.map((e, idx) => (
          <Panel
            key={e.id ?? idx}
            onClick={() => setSelected(e)}
            className="p-5 flex items-center justify-between gap-6 cursor-pointer hover:border-[#CCFF00]/50 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(204,255,0,0.12)]"
          >
            <div className="flex items-center gap-4 min-w-0">
              <span className="text-xs font-mono shrink-0" style={{ color: THEME.textTertiary }}>#{String(items.length - idx).padStart(3, '0')}</span>
              <div className="min-w-0">
                <p className="font-bold capitalize truncate">{e.brand} {e.model}</p>
                <p className="text-xs" style={{ color: THEME.textTertiary }}>{e.year} · {titleCase(e.fuel_type)} · {titleCase(e.transmission)}</p>
              </div>
            </div>
            <div className="text-sm shrink-0" style={{ color: THEME.textSecondary }}>{titleCase(e.city)}<br />{formatNumber(e.km_driven)} km</div>
            <div className="w-40 shrink-0">
              <p className="text-[10px] uppercase mb-1" style={{ color: THEME.textTertiary }}>Condition</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.08)' }}>
                  <div className="h-full rounded-full" style={{ width: `${(e.condition_score ?? 0) * 100}%`, background: THEME.accentGreen }} />
                </div>
                <span className="text-xs font-bold">{((e.condition_score ?? 0) * 100).toFixed(0)}</span>
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="font-bold" style={{ color: THEME.accentGreen }}>{formatCurrency(e.predicted_price)}</p>
              <p className="text-xs" style={{ color: THEME.textTertiary }}>{formatDate(e.created_at)}</p>
            </div>
          </Panel>
        ))}
      </div>

      {selected && (
        <DetailModal
          title={`${selected.brand} ${selected.model}`}
          subtitle={`Estimation #${selected.id}`}
          fields={buildEstimationFields(selected)}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
};

// ============================================================================
// SAVED VEHICLES (real data)
// ============================================================================

const SavedVehiclesPage = () => {
  const [items, setItems] = useState([]);
  const [estimationsById, setEstimationsById] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      // Fetch both saved vehicles and the full estimation history, then
      // cross-reference by estimation_id -- this gives a rich detail view
      // even though the saved_vehicles table itself only stores a name/note.
      const [savedRes, historyRes] = await Promise.all([
        SavedVehiclesAPI.getSavedVehicles(),
        EstimationAPI.getEstimations(200, 0),
      ]);
      if (cancelled) return;

      if (historyRes.success) {
        const map = {};
        (historyRes.data.items || []).forEach((e) => { map[e.id] = e; });
        setEstimationsById(map);
      }

      if (savedRes.success) setItems(savedRes.data.items || []);
      else setError(savedRes.error || 'Failed to load saved vehicles');
      setLoading(false);
    })();
    return () => { cancelled = true; };
  }, []);

  const openDetail = (v) => {
    const matched = estimationsById[v.estimation_id];
    setSelected({ vehicle: v, estimation: matched || null });
  };

  return (
    <div>
      <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// GARAGE</p>
      <h1 className="text-3xl font-bold mb-8" style={{ fontFamily: FONTS.display }}>Saved Vehicles</h1>

      {loading && <p className="text-sm" style={{ color: THEME.textTertiary }}>Loading...</p>}
      {!loading && error && <p className="text-sm text-red-400">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="text-sm" style={{ color: THEME.textTertiary }}>
          Nothing saved yet. Save a vehicle from its price report to see it here.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((v, idx) => (
          <Panel
            key={v.id ?? idx}
            onClick={() => openDetail(v)}
            className="p-5 cursor-pointer hover:border-[#CCFF00]/50 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(204,255,0,0.12)]"
          >
            <p className="text-xs font-semibold uppercase mb-2" style={{ color: THEME.accentGreen }}>// Saved</p>
            <h3 className="font-bold text-lg capitalize mb-1">{v.vehicle_name || 'Vehicle'}</h3>
            {v.notes && <p className="text-xs mb-3" style={{ color: THEME.textTertiary }}>{v.notes}</p>}
            <p className="text-xs" style={{ color: THEME.textTertiary }}>{formatDate(v.created_at || v.saved_at)}</p>
          </Panel>
        ))}
      </div>

      {selected && (
        selected.estimation ? (
          <DetailModal
            title={`${selected.estimation.brand} ${selected.estimation.model}`}
            subtitle={selected.vehicle.notes || 'Saved vehicle'}
            fields={buildEstimationFields(selected.estimation)}
            onClose={() => setSelected(null)}
          />
        ) : (
          <DetailModal
            title={selected.vehicle.vehicle_name || 'Vehicle'}
            subtitle="Saved vehicle (full estimation record not found)"
            fields={[
              ['Notes', selected.vehicle.notes || 'None'],
              ['Saved On', formatDate(selected.vehicle.created_at || selected.vehicle.saved_at)],
            ]}
            onClose={() => setSelected(null)}
          />
        )
      )}
    </div>
  );
};

// ============================================================================
// MARKET TRENDS (mock -- no backend for this yet)
// ============================================================================

const MarketTrendsPage = () => {
  const segments = [
    { label: 'Avg Sedan (India)', value: '₹9.13 L', change: '+3.2%' },
    { label: 'Avg SUV (India)', value: '₹12.40 L', change: '+5.1%' },
    { label: 'Avg Hatch (India)', value: '₹6.52 L', change: '+1.4%' },
    { label: 'Depreciation YoY', value: '12.8%', change: '-0.6%' },
  ];
  const movers = [
    ['Toyota Innova', '₹14,50,000', '+8.4%'],
    ['Maruti Baleno', '₹6,20,000', '+5.2%'],
    ['Hyundai Creta', '₹11,20,000', '+4.1%'],
    ['Tata Nexon EV', '₹11,80,000', '-2.8%'],
    ['Honda City', '₹8,90,000', '-1.4%'],
  ];

  return (
    <div>
      <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// MARKET INTELLIGENCE</p>
      <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: FONTS.display }}>Market Trends</h1>
      <p className="text-sm mb-2" style={{ color: THEME.textTertiary }}>Aggregated used-car market pulse across India.</p>
      <p className="text-xs mb-8" style={{ color: THEME.textTertiary }}>
        (Illustrative figures — not yet backed by a live market-data endpoint.)
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {segments.map((s) => (
          <Panel
            key={s.label}
            className="p-5 cursor-default hover:border-[#CCFF00]/50 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgba(204,255,0,0.12)]"
          >
            <p className="text-[10px] uppercase mb-2" style={{ color: THEME.textTertiary }}>{s.label}</p>
            <p className="text-2xl font-bold mb-1" style={{ fontFamily: FONTS.display }}>{s.value}</p>
            <p className="text-xs" style={{ color: s.change.startsWith('+') ? THEME.accentGreen : THEME.danger }}>{s.change} vs LY</p>
          </Panel>
        ))}
      </div>

      <Panel className="p-6">
        <SectionLabel>Top Movers</SectionLabel>
        <h3 className="text-lg font-bold mb-4" style={{ fontFamily: FONTS.display }}>This month</h3>
        <div className="space-y-1">
          {movers.map(([name, price, change], idx) => (
            <div
              key={name}
              className="flex items-center justify-between py-3 px-3 -mx-3 rounded-lg border-b last:border-0 transition-all duration-200 hover:bg-[#CCFF00]/5 hover:border-transparent"
              style={{ borderColor: THEME.cardBorder }}
            >
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono" style={{ color: THEME.textTertiary }}>#{String(idx + 1).padStart(2, '0')}</span>
                <span className="font-semibold">{name}</span>
              </div>
              <div className="flex items-center gap-6">
                <span style={{ color: THEME.textSecondary }}>{price}</span>
                <span className="font-semibold" style={{ color: change.startsWith('+') ? THEME.accentGreen : THEME.danger }}>{change}</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
};

// ============================================================================
// PROFILE (real data)
// ============================================================================

const ProfilePage = ({ user, onUserUpdate }) => {
  const [fullName, setFullName] = useState(user?.name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const response = await AuthAPI.getCurrentUser();
      if (cancelled) return;
      if (response.success) {
        setFullName(response.data.user.name || '');
        setPhone(response.data.user.phone || '');
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleUpdate = async () => {
    setSaving(true); setMessage('');
    const response = await AuthAPI.updateProfile(fullName, phone);
    setSaving(false);
    if (response.success) {
      setMessage('Profile updated.');
      onUserUpdate?.(response.data.user);
    } else {
      setMessage(`Update failed: ${response.error}`);
    }
  };

  return (
    <div>
      <p className="text-xs font-semibold mb-2" style={{ color: THEME.accentGreen }}>// OPERATOR</p>
      <h1 className="text-3xl font-bold mb-8" style={{ fontFamily: FONTS.display }}>Profile</h1>

      <Panel className="p-8 max-w-2xl">
        <div className="flex items-center gap-4 pb-6 mb-6 border-b" style={{ borderColor: THEME.cardBorder }}>
          <div className="w-16 h-16 rounded flex items-center justify-center text-2xl font-bold text-black" style={{ background: THEME.accentGreen }}>
            {(fullName || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-bold text-lg">{fullName || 'User'}</p>
            <p className="text-sm" style={{ color: THEME.textTertiary }}>{user?.email}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <Input label="Full Name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input label="Email" value={user?.email || ''} disabled />
        </div>
        <Input label="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 ..." />

        {message && <p className={`text-sm mt-4 ${message.startsWith('Profile') ? 'text-green-400' : 'text-red-400'}`}>{message}</p>}

        <Button variant="primary" className="mt-6" onClick={handleUpdate} disabled={saving}>
          {saving ? 'Saving...' : 'Update Profile'}
        </Button>
      </Panel>
    </div>
  );
};

// ============================================================================
// MAIN APP
// ============================================================================

export default function AutoGaugeApp() {
  const [page, setPage] = useState('login');
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => { setUser(userData); setPage('dashboard'); };
  const handleLogout = () => { setUser(null); setPage('login'); };
  const handleNavigate = (key) => setPage(key);

  if (page === 'login') {
    return <LoginPage onLogin={handleLogin} authAPI={AuthAPI} />;
  }

  return (
    <AppShell activePage={page} onNavigate={handleNavigate} user={user} onLogout={handleLogout}>
      {page === 'dashboard' && <DashboardPage user={user} onNavigate={handleNavigate} />}
      {page === 'wizard' && <WizardPage onDone={() => setPage('dashboard')} />}
      {page === 'history' && <HistoryPage />}
      {page === 'saved' && <SavedVehiclesPage />}
      {page === 'trends' && <MarketTrendsPage />}
      {page === 'profile' && <ProfilePage user={user} onUserUpdate={setUser} />}
    </AppShell>
  );
}