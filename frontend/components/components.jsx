/**
 * AutoGauge Components Library
 * Reusable, premium automotive-themed components
 */

import React, { useState } from 'react';
import { ChevronRight, Heart, Download, Share2, X } from 'lucide-react';

const THEME = {
  bgDark: '#0A0E27',
  cardBg: 'rgba(20, 25, 45, 0.6)',
  accentGreen: '#00FF41',
  accentVolt: '#00FFD9',
  textPrimary: '#FFFFFF',
  textSecondary: '#A0A8C0',
};

// ============================================================================
// HEADER COMPONENT
// ============================================================================

export const Header = ({ title, subtitle, onLogout }) => (
  <div className="border-b border-white/10 backdrop-blur-sm sticky top-0 z-50" style={{ background: THEME.bgDark }}>
    <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
      <div>
        <h1 className="text-3xl font-bold" style={{ color: THEME.textPrimary, fontFamily: "'Unbounded'" }}>
          {title}
        </h1>
        {subtitle && <p style={{ color: THEME.textSecondary }} className="text-sm mt-1">{subtitle}</p>}
      </div>
      {onLogout && (
        <button
          onClick={onLogout}
          className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all text-sm font-medium"
          style={{ color: THEME.textPrimary }}
        >
          Logout
        </button>
      )}
    </div>
  </div>
);

// ============================================================================
// PREMIUM CARD COMPONENTS
// ============================================================================

export const GlassCard = ({ children, className = '', hover = true, glow = false, onClick }) => (
  <div
    onClick={onClick}
    className={`
      backdrop-blur-xl rounded-2xl p-6 border border-white/10
      transition-all duration-500 cursor-pointer
      ${hover ? 'hover:border-white/20 hover:bg-white/[0.08]' : ''}
      ${glow ? 'shadow-[0_0_20px_rgba(0,255,65,0.1)]' : ''}
      ${className}
    `}
    style={{
      background: THEME.cardBg,
      backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 1px)`,
      backgroundSize: '40px 40px',
    }}
  >
    {children}
  </div>
);

export const StatCard = ({ icon: Icon, label, value, change, trend = 'up', onClick }) => (
  <GlassCard onClick={onClick} glow hover>
    <div className="flex justify-between items-start mb-4">
      <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 hover:from-green-500/20 transition-all">
        <Icon size={24} style={{ color: THEME.accentGreen }} />
      </div>
      {change && (
        <div className={`text-sm font-semibold flex items-center gap-1 ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
          {trend === 'up' ? '↑' : '↓'} {change}%
        </div>
      )}
    </div>
    <div className="text-sm" style={{ color: THEME.textSecondary }}>{label}</div>
    <div className="text-3xl font-bold mt-2" style={{ color: THEME.textPrimary, fontFamily: "'Unbounded'" }}>
      {value}
    </div>
  </GlassCard>
);

export const EstimationCard = ({ brand, model, year, price, condition, km, date, onSave, onDelete }) => (
  <GlassCard hover className="relative group">
    <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={onSave}
        className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all"
        title="Save vehicle"
      >
        <Heart size={16} style={{ color: THEME.accentGreen }} />
      </button>
      <button
        onClick={onDelete}
        className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all"
        title="Delete estimation"
      >
        <X size={16} className="text-red-400" />
      </button>
    </div>
    
    <div className="mb-4">
      <h3 className="text-lg font-bold" style={{ color: THEME.textPrimary }}>
        {brand} {model}
      </h3>
      <p style={{ color: THEME.textSecondary }} className="text-sm">
        {year} • {km.toLocaleString()} km
      </p>
    </div>
    
    <div className="grid grid-cols-2 gap-4 mb-4 pt-4 border-t border-white/10">
      <div>
        <p style={{ color: THEME.textSecondary }} className="text-xs uppercase tracking-wide mb-1">Price</p>
        <p className="text-xl font-bold" style={{ color: THEME.accentGreen }}>
          ₹{(price / 100000).toFixed(1)}L
        </p>
      </div>
      <div>
        <p style={{ color: THEME.textSecondary }} className="text-xs uppercase tracking-wide mb-1">Condition</p>
        <p className="text-xl font-bold" style={{ color: THEME.accentVolt }}>
          {(condition * 100).toFixed(0)}%
        </p>
      </div>
    </div>
    
    <p style={{ color: THEME.textTertiary }} className="text-xs">{date}</p>
  </GlassCard>
);

// ============================================================================
// FORM COMPONENTS
// ============================================================================

export const FormInput = ({ label, error, required, ...props }) => (
  <div className="w-full">
    {label && (
      <label className="block text-sm font-medium mb-2" style={{ color: THEME.textPrimary }}>
        {label} {required && <span className="text-red-400">*</span>}
      </label>
    )}
    <input
      className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-green-500/50 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all"
      style={{ color: THEME.textPrimary }}
      {...props}
    />
    {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
  </div>
);

export const FormSelect = ({ label, options, error, required, ...props }) => (
  <div className="w-full">
    {label && (
      <label className="block text-sm font-medium mb-2" style={{ color: THEME.textPrimary }}>
        {label} {required && <span className="text-red-400">*</span>}
      </label>
    )}
    <select
      className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white focus:border-green-500/50 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all"
      {...props}
    >
      <option value="">Select {label?.toLowerCase()}</option>
      {options?.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
    {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
  </div>
);

export const FormTextarea = ({ label, error, required, ...props }) => (
  <div className="w-full">
    {label && (
      <label className="block text-sm font-medium mb-2" style={{ color: THEME.textPrimary }}>
        {label} {required && <span className="text-red-400">*</span>}
      </label>
    )}
    <textarea
      className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-green-500/50 focus:outline-none focus:ring-2 focus:ring-green-500/20 transition-all resize-none"
      rows="4"
      style={{ color: THEME.textPrimary }}
      {...props}
    />
    {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
  </div>
);

export const FormSlider = ({ label, min, max, value, onChange, step = 1 }) => (
  <div className="w-full">
    <div className="flex justify-between items-center mb-2">
      <label className="text-sm font-medium" style={{ color: THEME.textPrimary }}>
        {label}
      </label>
      <span className="text-sm font-bold" style={{ color: THEME.accentGreen }}>
        {value}
      </span>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      onChange={onChange}
      step={step}
      className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-green-500"
      style={{
        background: `linear-gradient(to right, #00FF41 0%, #00FF41 ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) ${((value - min) / (max - min)) * 100}%, rgba(255,255,255,0.1) 100%)`,
      }}
    />
  </div>
);

// ============================================================================
// BUTTON COMPONENTS
// ============================================================================

export const Button = ({ children, variant = 'primary', size = 'md', className = '', loading = false, ...props }) => {
  const baseStyles = 'font-semibold rounded-lg transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: `bg-gradient-to-r from-green-500 to-green-600 text-black hover:shadow-[0_0_20px_rgba(0,255,65,0.3)] active:scale-95`,
    secondary: `bg-white/10 hover:bg-white/20 text-white border border-white/20 active:bg-white/30`,
    ghost: `text-white hover:bg-white/5 active:bg-white/10`,
    danger: `bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30`,
  };
  
  const sizes = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg',
    xl: 'px-8 py-5 text-lg',
  };
  
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={loading}
      {...props}
    >
      {loading ? (
        <>
          <div className="w-4 h-4 border-2 border-white/20 border-t-current rounded-full animate-spin" />
          Loading...
        </>
      ) : (
        children
      )}
    </button>
  );
};

// ============================================================================
// MODAL COMPONENT
// ============================================================================

export const Modal = ({ isOpen, title, children, onClose, footer }) => {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.7)' }}>
      <GlassCard className="w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold" style={{ color: THEME.textPrimary, fontFamily: "'Unbounded'" }}>
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 transition-all"
          >
            <X size={20} style={{ color: THEME.textSecondary }} />
          </button>
        </div>
        
        <div className="mb-6">{children}</div>
        
        {footer && <div className="flex gap-4">{footer}</div>}
      </GlassCard>
    </div>
  );
};

// ============================================================================
// ALERT COMPONENT
// ============================================================================

export const Alert = ({ type = 'info', title, message, onClose }) => {
  const colors = {
    success: 'from-green-500/10 to-transparent border-green-500/30',
    error: 'from-red-500/10 to-transparent border-red-500/30',
    warning: 'from-yellow-500/10 to-transparent border-yellow-500/30',
    info: 'from-blue-500/10 to-transparent border-blue-500/30',
  };
  
  const textColors = {
    success: 'text-green-400',
    error: 'text-red-400',
    warning: 'text-yellow-400',
    info: 'text-blue-400',
  };
  
  return (
    <div className={`bg-gradient-to-r ${colors[type]} border rounded-lg p-4 mb-4 flex justify-between items-start`}>
      <div>
        {title && <p className={`font-bold mb-1 ${textColors[type]}`}>{title}</p>}
        {message && <p style={{ color: THEME.textSecondary }} className="text-sm">{message}</p>}
      </div>
      {onClose && (
        <button onClick={onClose} className="p-1 hover:bg-white/10 rounded transition-all">
          <X size={16} style={{ color: THEME.textSecondary }} />
        </button>
      )}
    </div>
  );
};

// ============================================================================
// LOADING & EMPTY STATES
// ============================================================================

export const LoadingSpinner = ({ size = 'md', message = 'Loading...' }) => {
  const sizeMap = { sm: '40px', md: '60px', lg: '80px' };
  
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div
        className="border-4 border-white/10 border-t-green-500 rounded-full animate-spin mb-4"
        style={{ width: sizeMap[size], height: sizeMap[size] }}
      />
      <p style={{ color: THEME.textSecondary }}>{message}</p>
    </div>
  );
};

export const EmptyState = ({ icon: Icon, title, message, action }) => (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <div className="mb-4 p-4 rounded-xl bg-green-500/10">
      <Icon size={40} style={{ color: THEME.accentGreen }} />
    </div>
    <h3 className="text-lg font-bold mb-2" style={{ color: THEME.textPrimary }}>
      {title}
    </h3>
    <p style={{ color: THEME.textSecondary }} className="mb-6 max-w-sm">
      {message}
    </p>
    {action && action}
  </div>
);

// ============================================================================
// BADGE & TAG COMPONENTS
// ============================================================================

export const Badge = ({ children, variant = 'default', size = 'md' }) => {
  const variants = {
    default: 'bg-green-500/20 text-green-400 border border-green-500/30',
    success: 'bg-green-500/20 text-green-400 border border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    error: 'bg-red-500/20 text-red-400 border border-red-500/30',
  };
  
  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };
  
  return (
    <span className={`rounded-full font-semibold inline-block ${variants[variant]} ${sizes[size]}`}>
      {children}
    </span>
  );
};

// ============================================================================
// PROGRESS BAR COMPONENT
// ============================================================================

export const ProgressBar = ({ value, max = 100, showLabel = true, color = 'green' }) => {
  const percentage = (value / max) * 100;
  const colorMap = {
    green: 'bg-gradient-to-r from-green-500 to-green-600',
    yellow: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
    red: 'bg-gradient-to-r from-red-500 to-red-600',
  };
  
  return (
    <div className="w-full">
      <div className="bg-white/10 rounded-full h-2 overflow-hidden mb-2">
        <div
          className={`${colorMap[color]} h-full transition-all duration-500 rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="flex justify-between items-center text-xs" style={{ color: THEME.textSecondary }}>
          <span>{value}</span>
          <span>{percentage.toFixed(0)}%</span>
          <span>{max}</span>
        </div>
      )}
    </div>
  );
};

export default {
  Header,
  GlassCard,
  StatCard,
  EstimationCard,
  FormInput,
  FormSelect,
  FormTextarea,
  FormSlider,
  Button,
  Modal,
  Alert,
  LoadingSpinner,
  EmptyState,
  Badge,
  ProgressBar,
};
