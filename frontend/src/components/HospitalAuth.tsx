'use client'

import { FormEvent, useEffect, useLayoutEffect, useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

type AuthMode = 'login' | 'signup'
type Theme = 'light' | 'dark'

export default function HospitalAuth({ mode }: { mode: AuthMode }) {
  const router = useRouter()
  const isSignup = mode === 'signup'
  const [theme, setTheme] = useState<Theme>('light')
  const [themeReady, setThemeReady] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useLayoutEffect(() => {
    const savedTheme = window.localStorage.getItem('smriti-theme')
    if (savedTheme === 'light' || savedTheme === 'dark') setTheme(savedTheme)
    setThemeReady(true)
  }, [])

  useEffect(() => {
    if (!themeReady) return
    window.localStorage.setItem('smriti-theme', theme)
    document.documentElement.style.colorScheme = theme
  }, [theme, themeReady])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = event.currentTarget
    const password = form.elements.namedItem('password')
    const confirmPassword = form.elements.namedItem('confirmPassword')

    if (
      isSignup &&
      password instanceof HTMLInputElement &&
      confirmPassword instanceof HTMLInputElement &&
      password.value !== confirmPassword.value
    ) {
      setMessage('Your passwords do not match. Please check them and try again.')
      confirmPassword.focus()
      return
    }

    setMessage('')
    setIsSubmitting(true)
    const formData = new FormData(form)
    const payload = Object.fromEntries(formData.entries())
    try {
      const response = await fetch(`/api/auth/${isSignup ? 'signup' : 'login'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload),
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) {
        const details = Array.isArray(body.detail)
          ? body.detail.map((issue: { msg?: string }) => issue.msg).filter(Boolean).join(' ')
          : ''
        setMessage(typeof body.detail === 'string'
          ? body.detail
          : details || `Could not ${isSignup ? 'create the account' : 'sign in'} (${response.status}).`)
        return
      }
      router.replace('/dashboard')
    } catch (requestError) {
      console.error('Hospital account request failed:', requestError)
      setMessage('Could not connect to the account service. Check that the backend is running.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className={`auth-page ${theme === 'dark' ? 'auth-dark' : ''}`}>
      <div className="auth-atmosphere" aria-hidden="true" />
      <header className="auth-topbar">
        <Link href="/" className="auth-brand" aria-label="Smriti home">
          <Image src="/smriti-logo.png" alt="" width={42} height={42} priority />
          <span>
            <strong>Smriti</strong>
            <small>CLINICAL INTELLIGENCE</small>
          </span>
        </Link>
        <div className="auth-top-actions">
          <button
            className="auth-theme-toggle"
            type="button"
            onClick={() => setTheme(current => current === 'light' ? 'dark' : 'light')}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            <span aria-hidden="true">{theme === 'light' ? '◐' : '☼'}</span>
            {theme === 'light' ? 'Dark mode' : 'Light mode'}
          </button>
          <Link className="auth-back-link" href="/">
            <ArrowLeft size={15} /> Home
          </Link>
        </div>
      </header>

      <div className="auth-layout">
        <section className="auth-story" aria-label="About Smriti">
          <div className="auth-story-orbit auth-story-orbit-one" aria-hidden="true" />
          <div className="auth-story-orbit auth-story-orbit-two" aria-hidden="true" />
          <div className="auth-story-content">
            <div className="auth-eyebrow"><span /> BUILT FOR CARE TEAMS</div>
            <h1>
              A clearer view
              <br />
              of the <em>care journey.</em>
            </h1>
            <p>
              Bring clinical context, biomarkers, and imaging into one thoughtful workspace for your hospital team.
            </p>
            <div className="auth-story-points">
              <span><ShieldCheck size={16} /> Clinician-led decision support</span>
              <span><Sparkles size={16} /> Connected patient context</span>
            </div>
            <div className="auth-brain-card" aria-hidden="true">
              <Image src="/smriti-logo.png" alt="" fill priority sizes="(max-width: 760px) 180px, 280px" />
              <span>SMRITI <i>·</i> PRECISION CARE</span>
            </div>
          </div>
          <div className="auth-story-foot">
            <span><i /> HOSPITAL WORKSPACE</span>
            <span>Care in context. Decisions with clinicians.</span>
          </div>
        </section>

        <section className="auth-panel-wrap">
          <div className="auth-panel">
            <div className="auth-panel-heading">
              <div className="auth-panel-icon"><LockKeyhole size={19} /></div>
              <span className="auth-overline">HOSPITAL ACCESS</span>
              <h2>{isSignup ? 'Create your workspace' : 'Welcome back'}</h2>
              <p>
                {isSignup
                  ? 'The first account sets up this installation for one hospital workspace.'
                  : 'Sign in to continue to your hospital workspace.'}
              </p>
            </div>

            <div className="auth-mode-switch" aria-label="Account access">
              <Link href="/login" className={!isSignup ? 'active' : ''}>Sign in</Link>
              <Link href="/signup" className={isSignup ? 'active' : ''}>Create account</Link>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
              {isSignup && (
                <>
                  <div className="auth-workspace-note">
                    This local workspace includes the project’s 50 fictional demo records. It is not a real hospital patient database.
                  </div>
                  <label className="auth-field">
                    <span>Hospital or organization</span>
                    <input
                      name="organization"
                      type="text"
                      autoComplete="organization"
                      placeholder="e.g. City Memory Care Hospital"
                      required
                      minLength={2}
                    />
                  </label>
                  <label className="auth-field">
                    <span>Your full name</span>
                    <input
                      name="full_name"
                      type="text"
                      autoComplete="name"
                      placeholder="Name of the workspace administrator"
                      required
                      minLength={2}
                    />
                  </label>
                  <label className="auth-field">
                    <span>Professional role</span>
                    <select name="role" defaultValue="" required>
                      <option value="" disabled>Select your role</option>
                      <option value="physician">Physician / clinician</option>
                      <option value="administrator">Hospital administrator</option>
                      <option value="researcher">Researcher</option>
                      <option value="it">IT / system administrator</option>
                      <option value="other">Other care-team member</option>
                    </select>
                  </label>
                </>
              )}

              <label className="auth-field">
                <span>Work email</span>
                <span className="auth-input-wrap">
                  <Mail size={16} aria-hidden="true" />
                  <input
                    name="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@hospital.org"
                    required
                  />
                </span>
              </label>

              <label className="auth-field">
                <span>Password</span>
                <span className="auth-input-wrap">
                  <LockKeyhole size={16} aria-hidden="true" />
                  <input
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete={isSignup ? 'new-password' : 'current-password'}
                    placeholder={isSignup ? 'At least 12 characters' : 'Enter your password'}
                    minLength={isSignup ? 12 : undefined}
                    required
                  />
                  <button
                    className="auth-password-toggle"
                    type="button"
                    onClick={() => setShowPassword(current => !current)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </span>
              </label>

              {isSignup && (
                <>
                  <label className="auth-field">
                    <span>Confirm password</span>
                    <span className="auth-input-wrap">
                      <LockKeyhole size={16} aria-hidden="true" />
                      <input
                        name="confirmPassword"
                        type={showConfirmPassword ? 'text' : 'password'}
                        autoComplete="new-password"
                        placeholder="Enter your password again"
                        minLength={12}
                        required
                      />
                      <button
                        className="auth-password-toggle"
                        type="button"
                        onClick={() => setShowConfirmPassword(current => !current)}
                        aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                      >
                        {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </span>
                  </label>
                  <label className="auth-consent">
                    <input type="checkbox" required />
                    <span>I’m authorized to request access for this organization and agree to the terms of use.</span>
                  </label>
                </>
              )}

              {!isSignup && (
                <div className="auth-form-meta">
                  <span><ShieldCheck size={14} /> Hospital team account</span>
                  <button type="button" onClick={() => setMessage('Password recovery is not configured for this local workspace. Contact the person managing your Smriti installation.')}>Forgot password?</button>
                </div>
              )}

              <button className="auth-submit" type="submit" disabled={isSubmitting}>
                {isSubmitting
                  ? (isSignup ? 'Creating workspace…' : 'Signing in…')
                  : (isSignup ? 'Create hospital account' : 'Sign in to workspace')}
                <ArrowRight size={17} />
              </button>

              {message && (
                <div className="auth-status" role="status" aria-live="polite">
                  <ShieldCheck size={16} />
                  <span>{message}</span>
                </div>
              )}

              <div className="auth-prototype-note">
                <ShieldCheck size={15} />
                <span>Local prototype account. Do not use a password used elsewhere; email and hospital authorization are not verified.</span>
              </div>
            </form>

            <div className="auth-panel-footer">
              {isSignup ? 'Already have an account?' : 'New to Smriti?'}
              {' '}
              <Link href={isSignup ? '/login' : '/signup'}>
                {isSignup ? 'Sign in' : 'Request hospital access'}
              </Link>
            </div>
          </div>
          <p className="auth-legal">Smriti supports clinical review and does not replace professional judgment.</p>
        </section>
      </div>
    </main>
  )
}
