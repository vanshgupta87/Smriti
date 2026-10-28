'use client'

import { useEffect, useLayoutEffect, useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Brain,
  Check,
  ChevronRight,
  CircleHelp,
  ClipboardCheck,
  FlaskConical,
  Github,
  Mail,
  MessageSquare,
  Moon,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Sun,
  Target,
  Users,
  Video,
  Workflow,
} from 'lucide-react'

type Theme = 'light' | 'dark'

const stages = [
  {
    number: '01',
    title: 'Clinical screening',
    detail: 'Start with cognitive, demographic, and clinical context.',
    icon: ClipboardCheck,
    tint: 'blue',
    tag: 'Primary care',
  },
  {
    number: '02',
    title: 'Blood biomarkers',
    detail: 'Bring relevant plasma biomarkers into the care picture.',
    icon: FlaskConical,
    tint: 'violet',
    tag: 'Laboratory',
  },
  {
    number: '03',
    title: 'MRI morphometry',
    detail: 'Review structural imaging signals with volumetric context.',
    icon: ScanLine,
    tint: 'teal',
    tag: 'Radiology',
  },
  {
    number: '04',
    title: 'Molecular PET',
    detail: 'Complete the pathway with molecular imaging and safety context.',
    icon: Brain,
    tint: 'amber',
    tag: 'Specialist review',
  },
]

const platformSignals = [
  { label: 'Clinical', icon: ClipboardCheck, position: 'top-left' },
  { label: 'Blood', icon: FlaskConical, position: 'top-right' },
  { label: 'MRI & Tumor AI', icon: ScanLine, position: 'bottom-left' },
  { label: 'PET', icon: Brain, position: 'bottom-right' },
]

export default function LandingPage() {
  const [theme, setTheme] = useState<Theme>('light')
  const [themeReady, setThemeReady] = useState(false)

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

  return (
    <div className={`landing-page ${theme === 'dark' ? 'landing-dark' : 'landing-light'}`} id="top">
      <header className="landing-nav">
        <a className="landing-brand" href="#top" aria-label="Smriti home">
          <Image src="/smriti-logo.png" alt="" width={42} height={42} className="landing-brand-mark" priority />
          <span>
            <strong>Smriti</strong>
            <small>स्मरण</small>
          </span>
        </a>

        <nav className="landing-links" aria-label="Main navigation">
          <a href="#workflow">Workflow</a>
          <a href="#platform">Platform</a>
          <a href="#tumor-detection">Brain Tumor AI</a>
          <a href="#telemedicine">Telemedicine</a>
          <a href="#clinical-safety">Clinical approach</a>
        </nav>

        <div className="landing-nav-actions">
          <button
            type="button"
            className="landing-theme-toggle"
            onClick={() => setTheme(current => current === 'light' ? 'dark' : 'light')}
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          >
            {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
            <span>{theme === 'light' ? 'Dark' : 'Light'}</span>
          </button>
          <Link className="landing-nav-cta" href="/login">
            Hospital sign in <ArrowUpRight size={15} />
          </Link>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-grid" aria-hidden="true" />
          <div className="landing-orb landing-orb-one" aria-hidden="true" />
          <div className="landing-orb landing-orb-two" aria-hidden="true" />

          <div className="landing-hero-copy">
            <div className="landing-eyebrow"><span /> CLINICAL DECISION SUPPORT &amp; NEURO-AI</div>
            <h1>
              See the whole
              <br />
              <span>care journey.</span>
            </h1>
            <p className="landing-hero-description">
              Smriti brings clinical cognitive screening, multi-stage Alzheimer&apos;s progression modeling, plasma biomarkers, and YOLOv8 brain tumor detection into one thoughtful, precision care ecosystem.
            </p>
            <div className="landing-hero-actions">
              <Link className="landing-primary-button" href="/login">
                Hospital sign in <ArrowRight size={17} />
              </Link>
              <a className="landing-secondary-button" href="#workflow">
                Discover the pathway <ArrowDown size={16} />
              </a>
            </div>
            <div className="landing-hero-note">
              <ShieldCheck size={15} />
              <span>Designed to support clinical judgment—not replace it.</span>
            </div>
          </div>

          <div className="landing-visual" aria-label="Illustrative Smriti clinical dashboard preview">
            <div className="landing-visual-glow" />
            <div className="landing-window">
              <div className="landing-window-top">
                <div className="landing-window-brand">
                  <span className="landing-window-icon"><Brain size={17} /></span>
                  <span><strong>Smriti</strong><small>CLINICAL OVERVIEW</small></span>
                </div>
                <span className="landing-live"><i /> CARE PATHWAY</span>
              </div>
              <div className="landing-window-content">
                <div className="landing-preview-heading">
                  <div>
                    <span className="landing-kicker">PATIENT OVERVIEW</span>
                    <h2>Progress, in context.</h2>
                  </div>
                  <span className="landing-preview-avatar">SC</span>
                </div>
                <div className="landing-preview-stats">
                  <div><span>Current pathway</span><strong>Stage 2 <i>Blood biomarkers</i></strong></div>
                  <div><span>Clinical context</span><strong className="landing-context"><Check size={14} /> Updated</strong></div>
                </div>
                <div className="landing-chart-card">
                  <div className="landing-chart-heading">
                    <span>Illustrative risk trajectory</span>
                    <span className="landing-chart-legend"><i /> Trend</span>
                  </div>
                  <div className="landing-chart">
                    <div className="landing-chart-lines"><i /><i /><i /></div>
                    <svg viewBox="0 0 420 130" preserveAspectRatio="none" role="img" aria-label="Illustrative rising risk trend">
                      <defs>
                        <linearGradient id="landing-chart-fill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#76A7FF" stopOpacity=".28" />
                          <stop offset="100%" stopColor="#76A7FF" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      <path d="M0 104 C55 98 70 87 112 91 S174 70 212 78 S278 48 315 57 S375 28 420 24 L420 130 L0 130Z" fill="url(#landing-chart-fill)" />
                      <path d="M0 104 C55 98 70 87 112 91 S174 70 212 78 S278 48 315 57 S375 28 420 24" fill="none" stroke="#79A9FF" strokeWidth="3" strokeLinecap="round" />
                      <circle cx="315" cy="57" r="5" fill="#C4D8FF" stroke="#345E9F" strokeWidth="3" />
                      <circle cx="420" cy="24" r="5" fill="#C4D8FF" stroke="#345E9F" strokeWidth="3" />
                    </svg>
                  </div>
                  <div className="landing-chart-labels"><span>Screening</span><span>Biomarkers</span><span>Imaging</span><span>Review</span></div>
                </div>
                <div className="landing-window-footer">
                  <span><Sparkles size={14} /> Explainable insights</span>
                  <span><ShieldCheck size={14} /> Clinician in the loop</span>
                </div>
              </div>
            </div>
            <div className="landing-float-card landing-float-top">
              <span className="landing-float-icon"><Workflow size={16} /></span>
              <span><strong>One connected view</strong><small>Across four care stages</small></span>
            </div>
            <div className="landing-float-card landing-float-bottom">
              <span className="landing-float-dot" />
              <span><strong>Explainable by design</strong><small>Context clinicians can review</small></span>
            </div>
          </div>

          <a className="landing-scroll-cue" href="#workflow"><span /> SCROLL TO EXPLORE</a>
        </section>

        <section className="landing-intro" id="platform">
          <div className="landing-intro-aside">
            <div className="landing-intro-label"><span>01</span> THE PLATFORM</div>
            <div className="landing-platform-art" aria-hidden="true">
              <div className="landing-platform-orbit">
                <span className="landing-platform-orbit-line landing-platform-orbit-line-one" />
                <span className="landing-platform-orbit-line landing-platform-orbit-line-two" />
                <span className="landing-platform-orbit-line landing-platform-orbit-line-three" />
                <span className="landing-platform-orbit-line landing-platform-orbit-line-four" />
                <div className="landing-platform-core"><Workflow size={22} /></div>
                {platformSignals.map(({ label, icon: Icon, position }) => (
                  <div className={`landing-platform-signal ${position}`} key={label}>
                    <Icon size={16} />
                    <span>{label}</span>
                  </div>
                ))}
              </div>
              <div className="landing-platform-caption">
                <span>ONE PATIENT</span>
                <strong>Many signals.<br />One clearer picture.</strong>
              </div>
            </div>
          </div>
          <div className="landing-intro-content">
            <h2>Complex care deserves<br /><span>a clearer picture.</span></h2>
            <p>
              Smriti is a clinical decision-support platform for progressive Alzheimer&apos;s assessment and multimodal neuro-AI. It brings patient context, stage progression signals, and real-time YOLOv8 brain tumor detection together, while keeping research-only models distinct from clinical triage.
            </p>
            <div className="landing-intro-points">
              <span><Check size={15} /> 4-Stage Multimodal Alzheimer&apos;s Care</span>
              <span><Check size={15} /> Brain Tumor Detection</span>
              <span><Check size={15} /> 4-Stage PyTorch MLP Progression</span>
              <span><Check size={15} /> Clinician-Led Autonomous Escalation</span>
            </div>
          </div>
        </section>

        <section className="landing-workflow-section" id="workflow">
          <div className="landing-section-heading">
            <div>
              <div className="landing-section-label"><span>02</span> A PROGRESSIVE PATHWAY</div>
              <h2>Four stages.<br /><em>One connected story.</em></h2>
            </div>
            <p>Move from accessible first-line context toward specialist investigations through an organized, reviewable journey.</p>
          </div>

          <div className="landing-stage-grid">
            {stages.map((stage, index) => {
              const Icon = stage.icon
              return (
                <article className={`landing-stage-card stage-${stage.tint}`} key={stage.number}>
                  <div className="landing-stage-top">
                    <span className="landing-stage-number">{stage.number}</span>
                    <span className="landing-stage-icon"><Icon size={20} /></span>
                  </div>
                  <span className="landing-stage-tag">{stage.tag}</span>
                  <h3>{stage.title}</h3>
                  <p>{stage.detail}</p>
                  {index < stages.length - 1 && <ChevronRight className="landing-stage-arrow" size={18} aria-hidden="true" />}
                </article>
              )
            })}
          </div>
          <p className="landing-disclaimer">The pathway is a decision-support concept; diagnostic and treatment decisions remain with qualified clinicians.</p>
        </section>

        {/* --- BRAIN TUMOR DETECTION --- */}
        <section className="landing-workflow-section" id="tumor-detection">
          <div className="landing-section-heading">
            <div>
              <div className="landing-section-label"><span>03</span> BRAIN TUMOR · COMPUTER VISION</div>
              <h2>Real-time brain tumor detection.<br /><em>Localized with YOLOv8.</em></h2>
            </div>
            <p>Beyond neurodegenerative progression, Smriti equips clinical teams with an independent computer vision demonstration for rapid intracranial mass detection on MRI and CT imaging.</p>
          </div>

          <div className="landing-stage-grid">
            <article className="landing-stage-card stage-rose">
              <div className="landing-stage-top">
                <span className="landing-stage-number">01</span>
                <span className="landing-stage-icon" style={{ background: '#ffe4e6', color: '#e11d48' }}>
                  <Target size={20} />
                </span>
              </div>
              <span className="landing-stage-tag" style={{ color: '#e11d48' }}>Class: Glioma</span>
              <h3>Infiltrative Glial Neoplasms</h3>
              <p>Automated localization of low-grade and high-grade gliomas with high-confidence bounding box boundaries.</p>
            </article>

            <article className="landing-stage-card stage-amber">
              <div className="landing-stage-top">
                <span className="landing-stage-number">02</span>
                <span className="landing-stage-icon">
                  <ScanLine size={20} />
                </span>
              </div>
              <span className="landing-stage-tag">Class: Meningioma</span>
              <h3>Extra-Axial Dural Lesions</h3>
              <p>Detects classic dural-tail and convex meningiomas to differentiate structural lesions from cognitive decline.</p>
            </article>

            <article className="landing-stage-card stage-violet">
              <div className="landing-stage-top">
                <span className="landing-stage-number">03</span>
                <span className="landing-stage-icon">
                  <Brain size={20} />
                </span>
              </div>
              <span className="landing-stage-tag">Class: Pituitary</span>
              <h3>Sellar &amp; Parasellar Masses</h3>
              <p>Pinpoints pituitary adenomas and macroadenomas near the optic chiasm with sub-second inference latency.</p>
            </article>

            <article className="landing-stage-card stage-blue">
              <div className="landing-stage-top">
                <span className="landing-stage-number">YOLOv8</span>
                <span className="landing-stage-icon">
                  <Workflow size={20} />
                </span>
              </div>
              <span className="landing-stage-tag">Dual Architecture</span>
              <h3>Nano &amp; Medium Models</h3>
              <p>Interactive toggle between YOLOv8-Nano for ultra-fast edge triage and YOLOv8-Medium for maximum sensitivity.</p>
            </article>
          </div>

          <div className="mt-8 rounded-2xl border p-6 flex flex-col md:flex-row items-center justify-between gap-6" style={{ background: 'var(--landing-surface)', borderColor: 'var(--landing-line)' }}>
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                  🧠 Brain Tumor Detection
                </span>
                <span className="text-[11px] opacity-60">Interactive Clinical Workspace</span>
              </div>
              <h3 className="text-base font-bold">Try the Interactive Tumor Detection Workspace</h3>
              <p className="text-xs opacity-75 max-w-xl">
                Upload real-world brain MRI or CT scans directly into Smriti&apos;s brain tumor detection workspace to inspect bounding box coordinates, class detections, and confidence ratings in real time.
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <Link href="/login" className="landing-primary-button" style={{ padding: '10px 18px', fontSize: '12px' }}>
                Open Tumor Detection <ArrowRight size={15} />
              </Link>
            </div>
          </div>

          <p className="landing-disclaimer">Brain tumor YOLOv8 detection is an educational and research prototype demonstration. It operates completely decoupled from Alzheimer&apos;s progression stages and does not constitute a primary radiological diagnosis.</p>
        </section>

        <section className="landing-telemedicine-section" id="telemedicine">
          <div className="landing-telemedicine-shell">
            <div className="landing-telemedicine-copy">
              <div className="landing-section-label"><span>04</span> CARE, CONNECTED</div>
              <h2>Bring the next conversation<br /><em>closer to the patient.</em></h2>
              <p className="landing-telemedicine-intro">
                Start an invitation-based video consultation from the clinician workspace. Keep the patient context and the conversation connected in one place.
              </p>

              <div className="landing-telemedicine-features">
                <article>
                  <span className="landing-telemedicine-feature-icon"><Users size={17} /></span>
                  <div>
                    <h3>Choose from your patient registry</h3>
                    <p>Search patients and narrow the list by care stage.</p>
                  </div>
                </article>
                <article>
                  <span className="landing-telemedicine-feature-icon"><Mail size={17} /></span>
                  <div>
                    <h3>Send a one-click invitation</h3>
                    <p>Share a consultation link by email with an optional agenda.</p>
                  </div>
                </article>
                <article>
                  <span className="landing-telemedicine-feature-icon"><MessageSquare size={17} /></span>
                  <div>
                    <h3>Meet and discuss in context</h3>
                    <p>Use live video, in-call chat, and consultation notes.</p>
                  </div>
                </article>
              </div>

              <Link href="/login" className="landing-primary-button">
                Open telemedicine workspace <ArrowRight size={16} />
              </Link>
              <p className="landing-telemedicine-note"><ShieldCheck size={14} /> Clinician-led conversations. Sign-in required.</p>
            </div>

            <div className="landing-telemedicine-preview" aria-label="Illustration of an invitation-based video consultation">
              <div className="landing-telemedicine-preview-top">
                <span className="landing-telemedicine-preview-brand"><Video size={15} /> TELEMEDICINE</span>
                <span className="landing-telemedicine-live"><i /> READY TO CONNECT</span>
              </div>
              <div className="landing-telemedicine-visit">
                <div className="landing-telemedicine-visit-icon"><Video size={24} /></div>
                <span className="landing-telemedicine-eyebrow">VIDEO CONSULTATION</span>
                <h3>A more connected<br />care conversation.</h3>
                <p>Invite a patient to join a private consultation from their device.</p>
                <div className="landing-telemedicine-visit-meta">
                  <span><Mail size={14} /> Email invitation</span>
                  <span><MessageSquare size={14} /> Live chat</span>
                </div>
              </div>
              <div className="landing-telemedicine-invite">
                <span className="landing-telemedicine-invite-icon"><Mail size={16} /></span>
                <span><strong>Patient invitation</strong><small>Secure one-click join link</small></span>
                <span className="landing-telemedicine-invite-check"><Check size={14} /></span>
              </div>
              <span className="landing-telemedicine-orb" aria-hidden="true" />
            </div>
          </div>
        </section>

        <section className="landing-capabilities">
          <div className="landing-capabilities-copy">
            <div className="landing-section-label"><span>05</span> BUILT FOR CLINICAL CLARITY</div>
            <h2>From raw signals<br />to <em>reasoned review.</em></h2>
            <p>Purposeful tools help care teams explore the information behind a recommendation—not just the result.</p>
            <Link href="/dashboard" className="landing-text-link">See the workspace <ArrowRight size={16} /></Link>
          </div>
          <div className="landing-capability-list">
            <article>
              <span className="landing-capability-icon capability-blue"><Brain size={19} /></span>
              <div><h3>Multimodal patient view</h3><p>Bring clinical, laboratory, MRI, and PET context into a single patient journey.</p></div>
              <span className="landing-capability-index">01</span>
            </article>
            <article>
              <span className="landing-capability-icon capability-violet"><Sparkles size={19} /></span>
              <div><h3>Explainable AI insights</h3><p>Explore contributing signals and model context alongside the patient record.</p></div>
              <span className="landing-capability-index">02</span>
            </article>
            <article>
              <span className="landing-capability-icon capability-teal"><Workflow size={19} /></span>
              <div><h3>Operational overview</h3><p>Review worklists, pathway progression, and service-level context.</p></div>
              <span className="landing-capability-index">03</span>
            </article>
            <article>
              <span className="landing-capability-icon capability-violet"><Brain size={19} /></span>
              <div><h3>Deep learning progression triage</h3><p>Evaluate 4-stage PyTorch MLP progression models with calibrated decision thresholds.</p></div>
              <span className="landing-capability-index">04</span>
            </article>
            <article>
              <span className="landing-capability-icon capability-blue"><Target size={19} /></span>
              <div><h3>Brain tumor detection</h3><p>Real-time computer vision object detection on MRI scans for Glioma, Meningioma, and Pituitary tumors.</p></div>
              <span className="landing-capability-index">05</span>
            </article>
          </div>
        </section>

        <section className="landing-safety" id="clinical-safety">
          <div className="landing-safety-mark"><ShieldCheck size={25} /></div>
          <div className="landing-safety-copy">
            <div className="landing-section-label"><span>06</span> THE CLINICIAN STAYS CENTRAL</div>
            <h2>Support the decision.<br /><em>Respect the expertise.</em></h2>
            <p>
              Smriti is designed to organize information and support clinical review. It is not a diagnosis, and it does not replace professional judgment, confirm disease, or prescribe treatment.
            </p>
          </div>
          <div className="landing-safety-note">
            <CircleHelp size={18} />
            <span>Every insight is a prompt for qualified clinical review.</span>
          </div>
        </section>

        <section className="landing-final-cta">
          <div className="landing-cta-glow" aria-hidden="true" />
          <div className="landing-section-label"><span>YOUR NEXT STEP</span></div>
          <h2>Make the care journey<br /><em>easier to see.</em></h2>
          <p>Explore Smriti&apos;s clinical workspace and see the pathway in action.</p>
          <Link href="/login" className="landing-primary-button">
            Sign in to workspace <ArrowUpRight size={17} />
          </Link>
          <Link href="/signup" className="landing-primary-button landing-cta-access-link">
            Request hospital access <ArrowRight size={14} />
          </Link>
        </section>
      </main>

      <footer className="landing-footer">
        <a className="landing-footer-brand" href="#top"><Image src="/smriti-logo.png" alt="" width={28} height={28} /> <span>Smriti</span></a>
        <div className="landing-footer-socials" aria-label="Social links">
          <a href="https://github.com" target="_blank" rel="noreferrer" aria-label="GitHub"><Github size={17} /></a>
          <a href="https://x.com" target="_blank" rel="noreferrer" aria-label="X"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 2H22l-6.8 7.8L23.2 22h-6.3L12 14.6 5.5 22H2.3l7.3-8.4L1.8 2h6.4l4.5 6.8L18.9 2Zm-1.1 17.9h1.7L7.3 4H5.5l12.3 15.9Z" /></svg></a>
        </div>
      </footer>
    </div>
  )
}
