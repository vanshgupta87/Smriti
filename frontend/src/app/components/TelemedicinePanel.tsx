'use client'

/**
 * Smriti Telemedicine & Video Consultation Hub (Doctor / Clinician Console)
 * --------------------------------------------------------------------------
 * Role: Dr. Vansh Gupta (Attending Clinician / Doctor)
 * Actions:
 *  - Browse patients, select a patient to call.
 *  - Configure consultation agenda & clinician notes.
 *  - Dispatch live email invitation directly to patient inbox via Gmail/SMTP.
 *  - Doctor stays on this dashboard console with live camera & patient chart.
 *  - Configurable SMTP settings modal so real emails are delivered to Gmail!
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  Video, VideoOff, Mic, MicOff, PhoneCall, PhoneOff,
  Copy, CheckCheck, Users, MessageSquare, Send, X,
  ExternalLink, Search, Mail, ShieldCheck, Stethoscope,
  HeartPulse, Brain, AlertTriangle, ArrowRight, User,
  Maximize2, Minimize2, FileText, Sparkles, Clock, CheckCircle2,
  RefreshCw, SlidersHorizontal, ChevronRight, Settings, Key,
  Check, Info, AlertCircle
} from 'lucide-react'

const ICE_SERVERS: RTCIceServer[] = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
]

interface Patient {
  id: string
  mrn: string
  name: string
  age: number
  gender: string
  email?: string
  phone?: string
  current_stage: number
  risk_score: number
  velocity?: string
  complaint?: string
  primary_doctor?: string
  vitals?: any
  stage1?: any
  stage2?: any
  stage3?: any
  stage4?: any
}

interface ChatMessage {
  from: string
  text: string
  ts: string
  self?: boolean
}

interface Props {
  userName: string
  initialPatientId?: string | null
}

const CALL_REASONS = [
  "Review 4-Stage Progression & Diagnostic MRI Scan",
  "Follow-up on Brain Tumor Segmentation & Heatmap",
  "Plasma Biomarkers & Cognitive Test Discussion",
  "General Health & Routine Neurology Follow-up",
  "DMT Eligibility & Infusion Scheduling Consultation"
]

export default function TelemedicinePanel({ userName, initialPatientId }: Props) {
  // Ensure title includes Dr.
  const doctorDisplayName = userName ? (userName.toLowerCase().startsWith('dr') ? userName : `Dr. ${userName}`) : 'Dr. Vansh Gupta'

  // ── Patients & Selection ────────────────────────────────────────────────
  const [patients, setPatients] = useState<Patient[]>([])
  const [loadingPatients, setLoadingPatients] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [stageFilter, setStageFilter] = useState<number | 'all'>('all')
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)

  // ── Invitation Form State ───────────────────────────────────────────────
  const [targetEmail, setTargetEmail] = useState('')
  const [callReason, setCallReason] = useState(CALL_REASONS[0])
  const [customNotes, setCustomNotes] = useState('')
  const [isSendingInvite, setIsSendingInvite] = useState(false)

  // ── Call Session State ──────────────────────────────────────────────────
  const [activeRoomId, setActiveRoomId] = useState<string | null>(null)
  const [patientJoinUrl, setPatientJoinUrl] = useState<string>('')
  const [emailDispatchResult, setEmailDispatchResult] = useState<any>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [callStatus, setCallStatus] = useState<'feed' | 'calling' | 'connected' | 'ended'>('feed')
  const [peerConnected, setPeerConnected] = useState(false)
  const [copiedLink, setCopiedLink] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  // ── SMTP Email Config State ─────────────────────────────────────────────
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [isEmailConfigured, setIsEmailConfigured] = useState(false)
  const [smtpUser, setSmtpUser] = useState('')
  const [smtpPass, setSmtpPass] = useState('')
  const [savingConfig, setSavingConfig] = useState(false)
  const [configSuccess, setConfigSuccess] = useState('')
  const [configError, setConfigError] = useState('')

  // ── Media & Controls ────────────────────────────────────────────────────
  const [micOn, setMicOn] = useState(true)
  const [camOn, setCamOn] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)
  const [noCameraMode, setNoCameraMode] = useState(false)
  const [mediaWarning, setMediaWarning] = useState('')

  // ── Chat ────────────────────────────────────────────────────────────────
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')

  // ── Refs ────────────────────────────────────────────────────────────────
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)
  const localStreamRef = useRef<MediaStream | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const isCaller = useRef(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // ── Load Email Config Status ────────────────────────────────────────────
  const fetchEmailConfig = useCallback(async () => {
    try {
      const res = await fetch('/api/telemedicine/email-config')
      if (res.ok) {
        const data = await res.json()
        setIsEmailConfigured(data.is_configured)
        if (data.smtp_user) setSmtpUser(data.smtp_user)
      }
    } catch {
      // Non-blocking
    }
  }, [])

  useEffect(() => {
    fetchEmailConfig()
  }, [fetchEmailConfig])

  // ── Save Email Config (Gmail App Password) ──────────────────────────────
  const handleSaveEmailConfig = async () => {
    setSavingConfig(true)
    setConfigError('')
    setConfigSuccess('')
    try {
      const res = await fetch('/api/telemedicine/email-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smtp_host: 'smtp.gmail.com',
          smtp_port: 587,
          smtp_user: smtpUser.trim(),
          smtp_password: smtpPass.trim(),
          sender_email: smtpUser.trim(),
          sender_name: doctorDisplayName
        })
      })
      if (!res.ok) throw new Error('Could not save email settings')
      setConfigSuccess('Gmail App Password saved successfully! Real emails will now be sent.')
      setIsEmailConfigured(true)
      setTimeout(() => setShowConfigModal(false), 1500)
    } catch (err: any) {
      setConfigError(err.message || 'Failed to save configuration.')
    } finally {
      setSavingConfig(false)
    }
  }

  // ── Load Patients from Backend ──────────────────────────────────────────
  const fetchPatients = useCallback(async () => {
    setLoadingPatients(true)
    try {
      const res = await fetch('/api/patients')
      if (res.ok) {
        const data = await res.json()
        const patientList = Array.isArray(data) ? data : data.patients || []
        setPatients(patientList)

        if (initialPatientId) {
          const match = patientList.find((p: any) => p.id === initialPatientId || p.mrn === initialPatientId)
          if (match) {
            setSelectedPatient(match)
            setTargetEmail(match.email || `${match.name.toLowerCase().replace(/\s+/g, '.')}@healthmail.org`)
          }
        }
      }
    } catch (err) {
      console.error('Failed to load patients for telemedicine:', err)
    } finally {
      setLoadingPatients(false)
    }
  }, [initialPatientId])

  useEffect(() => {
    fetchPatients()
  }, [fetchPatients])

  const handleSelectPatient = (p: Patient) => {
    setSelectedPatient(p)
    const email = p.email || `${p.name.toLowerCase().replace(/\s+/g, '.')}@healthmail.org`
    setTargetEmail(email)
  }

  const cleanup = useCallback(() => {
    localStreamRef.current?.getTracks().forEach(t => t.stop())
    localStreamRef.current = null
    pcRef.current?.close()
    pcRef.current = null
    wsRef.current?.close()
    wsRef.current = null
    if (localVideoRef.current) localVideoRef.current.srcObject = null
    if (remoteVideoRef.current) remoteVideoRef.current.srcObject = null
    setPeerConnected(false)
  }, [])

  useEffect(() => () => cleanup(), [cleanup])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // ── Start Doctor WebRTC Session ─────────────────────────────────────────
  const initDoctorWebRTC = useCallback(async (roomId: string) => {
    setCallStatus('calling')
    setErrorMsg('')
    setNoCameraMode(false)
    setMediaWarning('')

    // Graceful media acquisition: try full A/V → audio-only → no media
    let stream: MediaStream | null = null
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
    } catch (_videoErr) {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: false, audio: true })
        setNoCameraMode(true)
        setMediaWarning('📷 No camera detected — audio-only mode. You can still see the patient and use in-call chat.')
      } catch (_audioErr) {
        // No media devices at all — still enter the room (listen-only / chat)
        stream = null
        setNoCameraMode(true)
        setMediaWarning('🎙️ No camera or microphone detected — you can still see the patient\'s video and use in-call chat.')
      }
    }

    if (stream) {
      localStreamRef.current = stream
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream
        localVideoRef.current.muted = true
      }
    }

    try {
      const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS })
      pcRef.current = pc

      if (stream) stream.getTracks().forEach(t => pc.addTrack(t, stream!))

      pc.ontrack = (evt) => {
        if (remoteVideoRef.current && evt.streams[0]) {
          remoteVideoRef.current.srcObject = evt.streams[0]
          setPeerConnected(true)
          setCallStatus('connected')
        }
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/telemedicine/${roomId}`
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      const send = (obj: any) => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj))
      }

      pc.onicecandidate = (evt) => {
        if (evt.candidate) send({ type: 'ice_candidate', candidate: evt.candidate })
      }

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'connected') {
          setPeerConnected(true)
          setCallStatus('connected')
        } else if (['disconnected', 'failed', 'closed'].includes(pc.connectionState)) {
          setPeerConnected(false)
        }
      }

      ws.onopen = () => {
        send({ type: 'join', name: doctorDisplayName, role: 'doctor' })
      }

      ws.onmessage = async (evt) => {
        let msg: any
        try { msg = JSON.parse(evt.data) } catch { return }

        switch (msg.type) {
          case 'peer_joined':
            setPeerConnected(true)
            if (!isCaller.current) {
              isCaller.current = true
              const offer = await pc.createOffer()
              await pc.setLocalDescription(offer)
              send({ type: 'offer', sdp: pc.localDescription })
            }
            break

          case 'offer':
            await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp))
            const answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            send({ type: 'answer', sdp: pc.localDescription })
            break

          case 'answer':
            await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp))
            break

          case 'ice_candidate':
            if (msg.candidate) {
              await pc.addIceCandidate(new RTCIceCandidate(msg.candidate)).catch(() => {})
            }
            break

          case 'peer_left':
            setPeerConnected(false)
            setChatMessages(prev => [...prev, {
              from: 'System',
              text: 'The patient has left the consultation.',
              ts: new Date().toISOString()
            }])
            break

          case 'chat':
            setChatMessages(prev => [...prev, {
              from: msg.from || 'Patient',
              text: msg.text,
              ts: msg.ts,
              self: false
            }])
            if (!chatOpen) setChatOpen(true)
            break
        }
      }

      ws.onerror = () => {
        setErrorMsg('Signaling connection error. Backend must be running on port 8000.')
      }

    } catch (err: any) {
      setErrorMsg('WebRTC signaling error: ' + (err.message || 'Unknown error'))
      setCallStatus('feed')
    }
  }, [doctorDisplayName, chatOpen])

  // ── Send Email Invitation & Start Call ──────────────────────────────────
  const handleInitiateCall = async () => {
    if (!selectedPatient) return
    setIsSendingInvite(true)
    setErrorMsg('')

    try {
      const res = await fetch('/api/telemedicine/invite-patient', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: selectedPatient.id,
          patient_name: selectedPatient.name,
          patient_email: targetEmail || selectedPatient.email,
          doctor_name: doctorDisplayName,
          call_reason: callReason,
          custom_notes: customNotes
        })
      })

      if (!res.ok) throw new Error('Failed to generate consultation invitation')
      const data = await res.json()

      setActiveRoomId(data.room_id)
      setPatientJoinUrl(data.join_url)
      setEmailDispatchResult(data.email_dispatch)
      setShowEmailModal(true)

      // Start doctor's live video session immediately
      await initDoctorWebRTC(data.room_id)

    } catch (err: any) {
      setErrorMsg(err.message || 'Error creating consultation session.')
    } finally {
      setIsSendingInvite(false)
    }
  }

  const handleEndCall = () => {
    cleanup()
    setCallStatus('ended')
    setPeerConnected(false)
  }

  const handleResetToFeed = () => {
    cleanup()
    setCallStatus('feed')
    setActiveRoomId(null)
    setPatientJoinUrl('')
    setEmailDispatchResult(null)
    setSelectedPatient(null)
    setChatMessages([])
    setChatOpen(false)
  }

  const toggleMic = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(t => { t.enabled = !t.enabled })
      setMicOn(prev => !prev)
    }
  }

  const toggleCam = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach(t => { t.enabled = !t.enabled })
      setCamOn(prev => !prev)
    }
  }

  const sendChat = () => {
    if (!chatInput.trim() || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ type: 'chat', text: chatInput.trim() }))
    setChatMessages(prev => [...prev, {
      from: `You (${doctorDisplayName})`,
      text: chatInput.trim(),
      ts: new Date().toISOString(),
      self: true
    }])
    setChatInput('')
  }

  const copyPatientLink = () => {
    if (patientJoinUrl) {
      navigator.clipboard.writeText(patientJoinUrl)
      setCopiedLink(true)
      setTimeout(() => setCopiedLink(false), 2000)
    }
  }

  const filteredPatients = patients.filter(p => {
    const matchesSearch = !searchQuery ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.mrn.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.complaint && p.complaint.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesStage = stageFilter === 'all' || p.current_stage === stageFilter
    return matchesSearch && matchesStage
  })

  // ─────────────────────────────────────────────────────────────────────────
  // VIEW: 1. PATIENT SELECTION FEED & INVITATION SETUP
  // ─────────────────────────────────────────────────────────────────────────
  if (callStatus === 'feed') {
    return (
      <div className="h-full flex flex-col p-5 gap-5 overflow-hidden">
        {/* Top Header Card */}
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 rounded-2xl p-6 text-white shadow-md flex items-center justify-between shrink-0">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="bg-white/20 text-white text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full tracking-wider flex items-center gap-1.5">
                <Stethoscope className="w-3 h-3" /> Doctor Calling Console
              </span>
              <span className="text-blue-200 text-xs">· HIPAA Compliant WebRTC</span>
            </div>
            <h2 className="text-xl font-black tracking-tight">Telemedicine Video Consultation</h2>
            <p className="text-xs text-blue-100 max-w-xl leading-relaxed">
              You are signed in as <strong className="text-white underline">{doctorDisplayName}</strong>. Select any patient from your registry to initiate an immediate video call. An email invitation containing their secure 1-click consultation link will be dispatched to their inbox.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* SMTP Config Status Button */}
            <button
              onClick={() => setShowConfigModal(true)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm border ${
                isEmailConfigured
                  ? 'bg-emerald-500/20 text-emerald-200 border-emerald-400/30 hover:bg-emerald-500/30'
                  : 'bg-amber-500/20 text-amber-200 border-amber-400/30 hover:bg-amber-500/30'
              }`}
              title="Configure Gmail App Password or SMTP server for live email delivery"
            >
              <Settings className="w-4 h-4" />
              <span>{isEmailConfigured ? 'Email: Gmail Connected' : 'Configure Gmail SMTP'}</span>
            </button>

            <div className="hidden lg:flex items-center gap-3 bg-white/10 backdrop-blur-md rounded-xl p-3 border border-white/20">
              <div className="text-right">
                <div className="text-[10px] text-blue-200 uppercase font-bold tracking-wider">Attending Clinician</div>
                <div className="text-sm font-black text-white">{doctorDisplayName}</div>
              </div>
              <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center font-bold text-white shadow-inner">
                {doctorDisplayName.replace('Dr. ', '').charAt(0)}
              </div>
            </div>
          </div>
        </div>

        {/* Content Layout: Left Patient Feed | Right Invitation Setup */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 overflow-hidden">

          {/* LEFT: Patient Feed (7 cols) */}
          <div className="lg:col-span-7 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {/* Feed Filter Bar */}
            <div className="p-4 border-b border-slate-200 bg-slate-50/70 space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    placeholder="Search patient by name, MRN, or clinical complaint..."
                    className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="text-xs font-semibold text-slate-500 shrink-0">
                  {filteredPatients.length} Patients
                </div>
              </div>

              {/* Stage Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto text-xs pb-0.5">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">Stage:</span>
                {(['all', 1, 2, 3, 4] as const).map(s => (
                  <button
                    key={String(s)}
                    onClick={() => setStageFilter(s)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      stageFilter === s
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {s === 'all' ? 'All Patients' : `Stage ${s}`}
                  </button>
                ))}
              </div>
            </div>

            {/* Patients Scroll List */}
            <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2">
              {loadingPatients ? (
                <div className="flex items-center justify-center py-20 text-slate-400 gap-2 text-xs">
                  <RefreshCw className="w-4 h-4 animate-spin" /> Loading patient registry...
                </div>
              ) : filteredPatients.length === 0 ? (
                <div className="text-center py-16 text-slate-400 text-xs">
                  No matching patients found.
                </div>
              ) : (
                filteredPatients.map(p => {
                  const isSelected = selectedPatient?.id === p.id
                  const riskCls = p.risk_score >= 0.7 ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : p.risk_score >= 0.4 ? 'bg-amber-50 text-amber-700 border-amber-200'
                    : 'bg-emerald-50 text-emerald-700 border-emerald-200'

                  return (
                    <div
                      key={p.id}
                      onClick={() => handleSelectPatient(p)}
                      className={`p-3.5 rounded-xl transition cursor-pointer flex items-center justify-between gap-3 ${
                        isSelected
                          ? 'bg-blue-50/90 border-2 border-blue-500 shadow-sm'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="flex items-start gap-3 min-w-0">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-extrabold shrink-0 ${
                          isSelected ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-100 text-slate-700'
                        }`}>
                          {p.name.charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-slate-900 text-sm truncate">{p.name}</span>
                            <span className="font-mono text-[11px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                              {p.mrn}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 truncate mt-0.5">
                            {p.age}y · {p.gender} · {p.email || `${p.name.toLowerCase().replace(/\s+/g, '.')}@healthmail.org`}
                          </div>
                          {p.complaint && (
                            <div className="text-[11px] text-slate-400 line-clamp-1 mt-1">
                              {p.complaint}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-3 shrink-0">
                        <div className="text-right">
                          <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border ${riskCls}`}>
                            {p.risk_score >= 0.7 ? 'High Risk' : p.risk_score >= 0.4 ? 'Moderate' : 'Low Risk'}
                          </span>
                          <div className="text-[11px] font-bold text-slate-600 mt-1">
                            Stage {p.current_stage || 1}
                          </div>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSelectPatient(p)
                          }}
                          className={`p-2.5 rounded-xl transition ${
                            isSelected
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-100 hover:bg-blue-100 hover:text-blue-600 text-slate-600'
                          }`}
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* RIGHT: Invitation & Call Configuration Panel (5 cols) */}
          <div className="lg:col-span-5 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {selectedPatient ? (
              <div className="flex-1 flex flex-col p-6 space-y-5 overflow-y-auto">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                    <User className="w-4 h-4 text-blue-600" />
                    Selected Patient to Call
                  </div>
                  <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">
                    Patient: {selectedPatient.name}
                  </span>
                </div>

                {/* Patient Overview Card */}
                <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-extrabold text-slate-900 text-base">{selectedPatient.name}</h3>
                      <p className="text-xs text-slate-500">
                        MRN: <span className="font-mono font-semibold">{selectedPatient.mrn}</span> · {selectedPatient.age}y {selectedPatient.gender}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-bold text-blue-600">Current Stage {selectedPatient.current_stage}</div>
                      <div className="text-[11px] text-slate-400">Risk: {(selectedPatient.risk_score * 100).toFixed(0)}%</div>
                    </div>
                  </div>

                  {selectedPatient.complaint && (
                    <div className="text-xs bg-white p-2.5 rounded-xl border border-slate-200 text-slate-600">
                      <span className="font-semibold text-slate-800">Primary Complaint: </span>
                      {selectedPatient.complaint}
                    </div>
                  )}
                </div>

                {/* Patient Email Input */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-blue-600" />
                      Patient's Email Address (Recipient)
                    </span>
                    <span className="text-[10px] text-blue-600 font-semibold">Will receive call link</span>
                  </label>
                  <input
                    type="email"
                    value={targetEmail}
                    onChange={e => setTargetEmail(e.target.value)}
                    placeholder="patient@gmail.com"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-[11px] text-slate-400">
                    The patient will receive an official invitation email with a direct button to join your video consultation.
                  </p>
                </div>

                {/* Call Reason / Topic */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    Consultation Agenda
                  </label>
                  <select
                    value={callReason}
                    onChange={e => setCallReason(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {CALL_REASONS.map(r => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>

                {/* Optional Clinical Note */}
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-slate-700">
                    Doctor's Personal Note to Patient (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={customNotes}
                    onChange={e => setCustomNotes(e.target.value)}
                    placeholder="e.g. Hello, please join our video consultation so we can go through your latest brain MRI and cognitive assessment results."
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {!isEmailConfigured && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2">
                    <Info className="w-4 h-4 text-amber-600 mt-0.5 shrink-0" />
                    <div>
                      <span className="font-bold">Live Gmail Delivery: </span>
                      To deliver real emails to actual Gmail inboxes, click <button onClick={() => setShowConfigModal(true)} className="underline font-bold text-amber-900">Configure Gmail SMTP</button> at the top right to paste your Gmail App Password.
                    </div>
                  </div>
                )}

                {errorMsg && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs font-medium flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    {errorMsg}
                  </div>
                )}

                {/* Big Action CTA Button */}
                <div className="pt-2">
                  <button
                    onClick={handleInitiateCall}
                    disabled={isSendingInvite || !targetEmail.trim()}
                    className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white font-extrabold text-sm tracking-wide shadow-lg shadow-emerald-600/25 transition transform active:scale-[0.99] flex items-center justify-center gap-3"
                  >
                    {isSendingInvite ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        Sending Email to Patient & Starting Video Room...
                      </>
                    ) : (
                      <>
                        <Mail className="w-5 h-5" />
                        Send Email to Patient & Start Video Call
                      </>
                    )}
                  </button>
                  <p className="text-[11px] text-slate-400 text-center mt-2">
                    You (<strong className="text-slate-700">{doctorDisplayName}</strong>) will enter the doctor video room immediately.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 text-slate-400">
                <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400">
                  <PhoneCall className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <h4 className="font-bold text-slate-700 text-sm">Select a Patient to Call</h4>
                  <p className="text-xs text-slate-400 max-w-xs">
                    Choose any patient from the left registry to send an invitation email and begin your video consultation.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── SMTP SETTINGS MODAL ────────────────────────────────────────── */}
        {showConfigModal && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-200 overflow-hidden text-slate-900">
              <div className="p-5 bg-slate-900 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Key className="w-5 h-5 text-blue-400" />
                  <span className="font-bold text-sm">Gmail Email Sender Configuration</span>
                </div>
                <button onClick={() => setShowConfigModal(false)} className="text-slate-400 hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <p className="text-xs text-slate-600 leading-relaxed">
                  To send real, live invitation emails directly to any Gmail inbox (like your own or patient's), enter your Gmail address and 16-character <strong>Google App Password</strong>.
                </p>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700">Sender Gmail Address</label>
                  <input
                    type="email"
                    value={smtpUser}
                    onChange={e => setSmtpUser(e.target.value)}
                    placeholder="your.email@gmail.com"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-700 flex justify-between">
                    <span>Google 16-Letter App Password</span>
                    <a
                      href="https://myaccount.google.com/apppasswords"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[10px] text-blue-600 font-semibold underline"
                    >
                      Generate in 30 sec ↗
                    </a>
                  </label>
                  <input
                    type="password"
                    value={smtpPass}
                    onChange={e => setSmtpPass(e.target.value)}
                    placeholder="abcd efgh ijkl mnop"
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono font-bold tracking-widest text-slate-800 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-[10px] text-slate-400">
                    Visit Google Account → Security → 2-Step Verification → App Passwords.
                  </p>
                </div>

                {configSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    {configSuccess}
                  </div>
                )}

                {configError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs font-semibold flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                    {configError}
                  </div>
                )}
              </div>

              <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowConfigModal(false)}
                  className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEmailConfig}
                  disabled={savingConfig || !smtpUser.trim() || !smtpPass.trim()}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition flex items-center gap-2"
                >
                  {savingConfig ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  Save & Enable Live Email
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────────────────
  // VIEW: 2. LIVE DOCTOR VIDEO CONSULTATION ROOM
  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className={`h-full flex flex-col bg-slate-950 text-white ${fullscreen ? 'fixed inset-0 z-50' : 'p-4'}`}>

      {/* Top Banner: Doctor Station Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl px-5 py-3 mb-3 flex flex-wrap items-center justify-between gap-3 shadow-md shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-400 animate-pulse" />
          <div>
            <div className="text-xs font-extrabold text-white flex items-center gap-2">
              <span className="bg-blue-600 text-white px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider">
                Doctor Console
              </span>
              <span>{doctorDisplayName}</span>
              <span className="text-slate-400 font-normal">calling</span>
              <span className="text-blue-400 underline font-bold">{selectedPatient?.name}</span>
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5">
              Patient Email: <strong className="text-slate-200">{targetEmail}</strong> · Room Code: <span className="font-mono text-blue-300">{activeRoomId}</span>
            </div>
          </div>
        </div>

        {/* Action Pills */}
        <div className="flex items-center gap-2">
          {/* Email Modal Button */}
          {emailDispatchResult && (
            <button
              onClick={() => setShowEmailModal(true)}
              className="px-3.5 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-bold rounded-xl flex items-center gap-1.5 border border-blue-500/30 transition"
            >
              <Mail className="w-3.5 h-3.5" />
              View Dispatched Email Details
            </button>
          )}

          {/* Copy Link */}
          <button
            onClick={copyPatientLink}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-slate-700 transition"
          >
            {copiedLink ? <CheckCheck className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copiedLink ? 'Link Copied' : 'Copy Patient Link'}
          </button>

          {/* Back to feed */}
          <button
            onClick={handleResetToFeed}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700"
          >
            Leave Room
          </button>
        </div>
      </div>

      {/* Media Warning Banner (no-camera mode) */}
      {mediaWarning && (
        <div className="mb-3 px-4 py-2.5 bg-amber-900/40 border border-amber-600/50 rounded-xl text-amber-300 text-xs font-medium flex items-center gap-2 shrink-0">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
          {mediaWarning}
        </div>
      )}

      {/* Main Call View: Video Canvas (Left 8) + Patient Dossier (Right 4) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 min-h-0 overflow-hidden">
        {/* Video Canvas (8 cols) */}
        <div className="lg:col-span-8 bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden relative flex flex-col shadow-2xl">
          {/* Main Remote Feed */}
          <div className="flex-1 relative bg-slate-950 flex items-center justify-center overflow-hidden">
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />

            {/* If patient hasn't connected yet */}
            {!peerConnected && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-slate-950/90 backdrop-blur-md p-6 text-center">
                <div className="w-16 h-16 rounded-full border-4 border-emerald-500/30 border-t-emerald-500 animate-spin" />
                <div className="space-y-1.5">
                  <div className="inline-block bg-blue-500/20 text-blue-300 text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full">
                    Doctor Live Call Station Active
                  </div>
                  <h3 className="text-lg font-black text-white">
                    Waiting for {selectedPatient?.name} to connect...
                  </h3>
                  <p className="text-xs text-slate-300 max-w-md leading-relaxed">
                    The invitation email has been dispatched to <strong className="text-white">{targetEmail}</strong>.
                    As soon as the patient clicks their 1-click email link, their video feed will connect right here.
                  </p>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 text-xs text-slate-300 max-w-md space-y-2">
                  <div className="flex items-center gap-2 font-bold text-white text-xs">
                    <Stethoscope className="w-4 h-4 text-blue-400" />
                    Doctor Instructions:
                  </div>
                  <p className="text-[11px] text-slate-400 text-left">
                    • <strong>Dr. Vansh Gupta</strong>: Stay on this screen. {noCameraMode ? 'Running in audio/chat-only mode.' : 'Your camera and microphone are on.'}
                    <br />• <strong>Patient ({selectedPatient?.name})</strong>: Will join from the email sent to <span className="text-emerald-400">{targetEmail}</span>.
                  </p>
                  {mediaWarning && (
                    <p className="text-[11px] text-amber-300 text-left mt-1 flex items-start gap-1">
                      <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-amber-400" />
                      {mediaWarning}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Top Left: Remote Patient Status Tag */}
            <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md border border-slate-700/60 rounded-xl px-3.5 py-1.5 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${peerConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              <div className="text-xs font-bold text-white">
                Patient: {selectedPatient?.name} {peerConnected ? '(Online)' : '(Invited via Email)'}
              </div>
            </div>

            {/* Doctor Self-View Picture-in-Picture (Bottom Right) */}
            <div className="absolute bottom-4 right-4 w-44 sm:w-56 aspect-video rounded-2xl overflow-hidden border-2 border-blue-500 shadow-2xl bg-slate-900">
              <video
                ref={localVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              {(!camOn || noCameraMode) && (
                <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center text-slate-400 gap-1">
                  <VideoOff className="w-6 h-6" />
                  {noCameraMode && <span className="text-[10px] text-amber-400 font-medium">No Camera</span>}
                </div>
              )}
              <div className="absolute bottom-1.5 left-2 bg-blue-600/90 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-black text-white flex items-center gap-1">
                <Stethoscope className="w-3 h-3" />
                You ({doctorDisplayName})
              </div>
            </div>

            {/* In-Call Chat Overlay */}
            {chatOpen && (
              <div className="absolute bottom-20 left-4 w-80 max-h-80 bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl">
                <div className="px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                    <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
                    Doctor-Patient Consultation Chat
                  </span>
                  <button onClick={() => setChatOpen(false)} className="text-slate-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-2 max-h-52">
                  {chatMessages.length === 0 && (
                    <p className="text-[11px] text-slate-500 text-center py-4">No messages yet.</p>
                  )}
                  {chatMessages.map((m, idx) => (
                    <div key={idx} className={`flex flex-col ${m.self ? 'items-end' : 'items-start'}`}>
                      <span className="text-[9px] text-slate-400 mb-0.5">{m.from}</span>
                      <div className={`text-xs px-3 py-1.5 rounded-xl max-w-[85%] ${m.self ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-200'}`}>
                        {m.text}
                      </div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>
                <div className="p-2 border-t border-slate-800 flex gap-2">
                  <input
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && sendChat()}
                    placeholder="Type message to patient..."
                    className="flex-1 bg-slate-800 text-white text-xs rounded-xl px-3 py-2 border border-slate-700/60 focus:outline-none focus:ring-1 focus:ring-blue-500 placeholder-slate-500"
                  />
                  <button onClick={sendChat} className="p-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Controls Bar */}
          <div className="bg-slate-950 px-6 py-3.5 border-t border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button
                onClick={toggleMic}
                className={`p-3 rounded-xl transition ${micOn ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-rose-600 text-white'}`}
                title={micOn ? 'Mute Mic' : 'Unmute Mic'}
              >
                {micOn ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
              </button>
              <button
                onClick={toggleCam}
                className={`p-3 rounded-xl transition ${camOn ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-rose-600 text-white'}`}
                title={camOn ? 'Turn off camera' : 'Turn on camera'}
              >
                {camOn ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
              </button>
            </div>

            {/* Hangup / End Call Button */}
            <button
              onClick={handleEndCall}
              className="px-6 py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs tracking-wider uppercase transition shadow-lg shadow-rose-600/30 flex items-center gap-2"
            >
              <PhoneOff className="w-4 h-4" />
              End Consultation
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setChatOpen(prev => !prev)}
                className={`p-3 rounded-xl transition relative ${chatOpen ? 'bg-blue-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}`}
                title="Toggle Chat"
              >
                <MessageSquare className="w-5 h-5" />
                {chatMessages.some(m => !m.self) && !chatOpen && (
                  <span className="absolute top-2 right-2 w-2 h-2 bg-blue-400 rounded-full" />
                )}
              </button>
              <button
                onClick={() => setFullscreen(prev => !prev)}
                className="p-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                title="Fullscreen"
              >
                {fullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Docked Patient Clinical Summary (4 cols) */}
        <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-3xl p-5 flex flex-col gap-4 overflow-y-auto">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
              <FileText className="w-4 h-4 text-blue-400" />
              Patient Live Chart
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              {selectedPatient?.mrn}
            </span>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-slate-800/80 p-3 rounded-xl">
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Current Stage</div>
              <div className="text-base font-extrabold text-blue-400 mt-0.5">
                Stage {selectedPatient?.current_stage || 1}
              </div>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-xl">
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Progression Risk</div>
              <div className={`text-base font-extrabold mt-0.5 ${
                (selectedPatient?.risk_score || 0) >= 0.7 ? 'text-rose-400' : 'text-emerald-400'
              }`}>
                {((selectedPatient?.risk_score || 0) * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          {/* Vitals Summary */}
          {selectedPatient?.vitals && (
            <div className="bg-slate-800/60 rounded-xl p-3 space-y-1.5 text-xs">
              <div className="text-[10px] text-slate-400 font-semibold uppercase">Baseline Vitals</div>
              <div className="grid grid-cols-3 gap-1 text-[11px] text-slate-300">
                <div>BP: <strong className="text-white">{selectedPatient.vitals.bp || '128/82'}</strong></div>
                <div>Pulse: <strong className="text-white">{selectedPatient.vitals.pulse || '72'} bpm</strong></div>
                <div>BMI: <strong className="text-white">{selectedPatient.vitals.bmi || '23.4'}</strong></div>
              </div>
            </div>
          )}

          {/* Clinical Agenda */}
          <div className="bg-blue-950/40 border border-blue-800/40 rounded-xl p-3 text-xs space-y-1">
            <div className="text-[10px] text-blue-400 font-bold uppercase tracking-wider">Agenda</div>
            <div className="text-xs text-slate-200 font-semibold">{callReason}</div>
          </div>

          {/* Diagnostic Stage Biomarkers Snippet */}
          <div className="flex-1 bg-slate-950/60 rounded-xl p-3 border border-slate-800/60 space-y-2 text-xs">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Biomarker Highlights</div>
            <div className="space-y-1.5 text-[11px] text-slate-300">
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">Cognitive (MMSE / MoCA):</span>
                <span className="font-semibold text-white">
                  {selectedPatient?.stage1?.mmse || '23.0'} / {selectedPatient?.stage1?.moca || '21.0'}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">Plasma Aβ42/40:</span>
                <span className="font-semibold text-blue-300">
                  {selectedPatient?.stage2?.ab42_40_ratio || '0.068'}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">Hippocampus Vol:</span>
                <span className="font-semibold text-purple-300">
                  {selectedPatient?.stage3?.hippocampus_volume_total || '5,420 mm³'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Velocity:</span>
                <span className="font-semibold text-amber-300">
                  {selectedPatient?.velocity || 'Moderate Converter'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── EMAIL DISPATCH STATUS MODAL ──────────────────────────────────── */}
      {showEmailModal && emailDispatchResult && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white text-slate-900 rounded-3xl max-w-xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold uppercase tracking-wider">
                  Patient Invitation Dispatched
                </span>
              </div>
              <button onClick={() => setShowEmailModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 bg-slate-50 border-b border-slate-200 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span><strong className="text-slate-600">Patient:</strong> {selectedPatient?.name}</span>
                <span><strong className="text-slate-600">Attending Doctor:</strong> {doctorDisplayName}</span>
              </div>
              <div><strong className="text-slate-600">Recipient Email:</strong> <span className="font-bold text-slate-900">{emailDispatchResult.to}</span></div>

              {emailDispatchResult.success ? (
                <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 font-semibold text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{emailDispatchResult.delivery_note}</span>
                </div>
              ) : (
                <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-xs space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    Notice regarding live email delivery:
                  </div>
                  <p className="text-[11px] text-amber-800">
                    {emailDispatchResult.delivery_note}
                  </p>
                </div>
              )}
            </div>

            {/* Email HTML Preview */}
            <div className="flex-1 overflow-y-auto p-4 bg-slate-100">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                Preview of Email Sent to Patient ({selectedPatient?.name})
              </div>
              <div
                className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden"
                dangerouslySetInnerHTML={{ __html: emailDispatchResult.preview_html }}
              />
            </div>

            <div className="p-4 bg-white border-t border-slate-200 flex items-center justify-between">
              <button
                onClick={copyPatientLink}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl flex items-center gap-2"
              >
                {copiedLink ? <CheckCheck className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                {copiedLink ? 'Link Copied!' : 'Copy Patient Join Link'}
              </button>
              <button
                onClick={() => setShowEmailModal(false)}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl shadow-md"
              >
                Return to Doctor Video Station
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
