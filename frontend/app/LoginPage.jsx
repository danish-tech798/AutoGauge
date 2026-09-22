'use client';

import React, { useRef, useState } from 'react';
import './LoginPage.css';

const NAV_ITEMS = [
    { key: 'home', label: 'Home' },
    { key: 'about', label: 'About' },
    { key: 'contact', label: 'Contact Us' },
    { key: 'services', label: 'Services' },
];

const SERVICES = [
    {
        title: 'Vehicle valuation',
        description: 'Estimate a used vehicle’s price from its details.',
    },
    {
        title: 'Photo damage analysis',
        description:
            'Identify visible damage and assess vehicle condition.',
    },
    {
        title: 'Price explanations',
        description:
            'Understand how individual factors affect the estimate.',
    },
    {
        title: 'Saved vehicles and reports',
        description:
            'Review previous estimates and download valuation reports.',
    },
];

export default function LoginPage({
    onLogin,
    authAPI,
    artworkSrc = '/images/autogauge-login-art.png',
    contactEmail = 'danish.z7787@gmail.com',
}) {
    const [mode, setMode] = useState('login');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [infoTab, setInfoTab] = useState('home');

    const submitting = useRef(false);
    const navigationRefs = useRef({});

    const contactAddress = (contactEmail || '').trim();

    const changeMode = (nextMode) => {
        if (submitting.current) return;

        setMode(nextMode);
        setError('');
    };

    const closeInfoPanel = () => {
        navigationRefs.current[infoTab]?.focus();
        setInfoTab('home');
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (submitting.current) return;

        setError('');

        const authMethod =
            mode === 'login' ? authAPI?.login : authAPI?.signup;

        if (typeof authMethod !== 'function') {
            setError('Authentication is unavailable. Please try again later.');
            return;
        }

        submitting.current = true;
        setLoading(true);

        try {
            const response =
                mode === 'login'
                    ? await authAPI.login(email, password)
                    : await authAPI.signup(email, password, fullName, '');

            if (response?.success && response.data?.user) {
                onLogin(response.data.user);
            } else {
                setError(
                    response?.error ||
                    `${mode === 'login' ? 'Login' : 'Signup'} failed`
                );
            }
        } catch {
            setError('Unable to connect. Please try again.');
        } finally {
            submitting.current = false;
            setLoading(false);
        }
    };

    return (
        <main className="ag-login">
            {/* Navigation above the branding and hero */}
            <nav
                className="ag-top-nav"
                aria-label="Login page navigation"
            >
                {NAV_ITEMS.map(({ key, label }) => (
                    <button
                        key={key}
                        ref={(element) => {
                            navigationRefs.current[key] = element;
                        }}
                        type="button"
                        className={infoTab === key ? 'is-active' : ''}
                        aria-pressed={infoTab === key}
                        onClick={() => setInfoTab(key)}
                    >
                        {label}
                    </button>
                ))}
            </nav>

            {/* Left column: branding and authentication */}
            <section className="ag-auth" aria-label="Account access">
                <div className="ag-auth-card">
                    <div className="ag-brand">
                        <span className="ag-brand-icon" aria-hidden="true">
                            <svg
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.8"
                                strokeLinejoin="round"
                                focusable="false"
                            >
                                <path d="M13 2 4 14h7l-1 8 10-13h-7l1-7Z" />
                            </svg>
                        </span>

                        <div>
                            <p className="ag-brand-name">AutoGauge</p>
                            <p className="ag-brand-tagline">
                                PRECISION VEHICLE VALUATION
                            </p>
                        </div>
                    </div>

                    {/* About, services, and contact content */}
                    {infoTab !== 'home' && (
                        <section
                            className="ag-info-panel"
                            aria-labelledby="ag-info-title"
                            onKeyDown={(event) => {
                                if (event.key === 'Escape') {
                                    event.preventDefault();
                                    closeInfoPanel();
                                }
                            }}
                        >
                            <div className="ag-info-header">
                                <h3 id="ag-info-title">
                                    {infoTab === 'about'
                                        ? 'About AutoGauge'
                                        : infoTab === 'services'
                                            ? 'Our services'
                                            : 'Contact us'}
                                </h3>

                                <button
                                    type="button"
                                    className="ag-info-close"
                                    aria-label="Close information"
                                    onClick={closeInfoPanel}
                                >
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.8"
                                        strokeLinecap="round"
                                        aria-hidden="true"
                                        focusable="false"
                                    >
                                        <path d="m6 6 12 12M18 6 6 18" />
                                    </svg>
                                </button>
                            </div>

                            {infoTab === 'about' && (
                                <p>
                                    AutoGauge combines machine learning and vehicle
                                    photo analysis to estimate used-car prices, assess
                                    visible damage, and explain the factors behind
                                    each valuation.
                                </p>
                            )}

                            {infoTab === 'services' && (
                                <ul className="ag-service-list">
                                    {SERVICES.map(({ title, description }) => (
                                        <li key={title}>
                                            <strong>{title}</strong>
                                            <span>{description}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}

                            {infoTab === 'contact' && (
                                <>
                                    <p>
                                        Have a question about AutoGauge or want to
                                        share feedback?
                                    </p>

                                    {contactAddress ? (
                                        <a
                                            className="ag-contact-link"
                                            href={`mailto:${contactAddress}?subject=${encodeURIComponent(
                                                'AutoGauge enquiry'
                                            )}`}
                                        >
                                            Email us
                                            <svg
                                                width="15"
                                                height="15"
                                                viewBox="0 0 24 24"
                                                fill="none"
                                                stroke="currentColor"
                                                strokeWidth="1.8"
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                                aria-hidden="true"
                                                focusable="false"
                                            >
                                                <path d="m9 5 7 7-7 7" />
                                            </svg>
                                        </a>
                                    ) : (
                                        <p className="ag-contact-note">
                                            Contact details will be available soon.
                                        </p>
                                    )}
                                </>
                            )}
                        </section>
                    )}

                    <div className="ag-auth-heading">
                        <p className="ag-eyebrow">// ACCESS TERMINAL</p>

                        <h2>
                            {mode === 'login' ? 'Sign in' : 'Create account'}
                            <span>.</span>
                        </h2>

                        <p className="ag-description">
                            Enter your credentials to continue.
                        </p>
                    </div>

                    <div className="ag-tabs" aria-label="Account mode">
                        <button
                            type="button"
                            aria-pressed={mode === 'login'}
                            disabled={loading}
                            onClick={() => changeMode('login')}
                        >
                            LOGIN
                        </button>

                        <button
                            type="button"
                            aria-pressed={mode === 'signup'}
                            disabled={loading}
                            onClick={() => changeMode('signup')}
                        >
                            SIGN UP
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} aria-busy={loading}>
                        {mode === 'signup' && (
                            <label className="ag-field">
                                <span>FULL NAME</span>
                                <input
                                    name="name"
                                    type="text"
                                    autoComplete="name"
                                    required
                                    value={fullName}
                                    onChange={(event) =>
                                        setFullName(event.target.value)
                                    }
                                    placeholder="Your name"
                                    disabled={loading}
                                />
                            </label>
                        )}

                        <label className="ag-field">
                            <span>EMAIL</span>
                            <input
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="you@garage.in"
                                disabled={loading}
                            />
                        </label>

                        <label className="ag-field">
                            <span>PASSWORD</span>
                            <input
                                name="password"
                                type="password"
                                autoComplete={
                                    mode === 'login'
                                        ? 'current-password'
                                        : 'new-password'
                                }
                                required
                                value={password}
                                onChange={(event) =>
                                    setPassword(event.target.value)
                                }
                                placeholder="••••••••"
                                disabled={loading}
                            />
                        </label>

                        {error && (
                            <p className="ag-error" role="alert">
                                {error}
                            </p>
                        )}

                        <button
                            type="submit"
                            className="ag-submit"
                            disabled={loading}
                        >
                            {loading
                                ? 'Please wait...'
                                : mode === 'login'
                                    ? 'SIGN IN'
                                    : 'CREATE ACCOUNT'}
                        </button>
                    </form>
                </div>
            </section>

            {/* Right column: headline, statistics, and artwork */}
            <section className="ag-hero" aria-label="AI vehicle valuation">
                <div className="ag-hero-copy">
                    <h1>
                        Know the true value of
                        <br className="ag-desktop-break" /> any{' '}
                        <span>used vehicle.</span>
                    </h1>

                    <p className="ag-hero-description">
                        Photo-driven damage detection, market-calibrated
                        pricing, and
                        <br className="ag-desktop-break" /> transparent
                        breakdowns — all in real time.
                    </p>

                    <div className="ag-metrics">
                        <div className="ag-metric">
                            <strong>94%</strong>
                            <span>ACCURACY</span>
                        </div>

                        <div className="ag-metric">
                            <strong>7.4K+</strong>
                            <span>VEHICLES IN MODEL</span>
                        </div>

                        <div className="ag-metric">
                            <strong>13</strong>
                            <span>CITIES</span>
                        </div>
                    </div>
                </div>

                <svg
                    className="ag-car-art"
                    viewBox="604 478 1068 463"
                    aria-hidden="true"
                    focusable="false"
                >
                    <image
                        href={artworkSrc}
                        width="1672"
                        height="941"
                    />
                </svg>

                <svg
                    className="ag-scan-art"
                    viewBox="1450 320 190 158"
                    aria-hidden="true"
                    focusable="false"
                >
                    <image
                        href={artworkSrc}
                        width="1672"
                        height="941"
                    />
                </svg>
            </section>

            {/* Fixed bottom-right label, positioned by your CSS */}
            <p className="ag-engine-label">
        // AI PRICING ENGINE · v3.2
            </p>
        </main>
    );
}