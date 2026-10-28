'use client'

/**
 * Smriti Telemedicine — Dedicated Patient Video Consultation Portal
 * -------------------------------------------------------------------
 * Role: Patient (e.g. Shreya Khanna)
 * Accessed via: The direct 1-click link received in their invitation email.
 * Connects directly to Dr. Vansh Gupta via peer-to-peer WebRTC.
 */

import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import {
  Video, VideoOff, Mic, MicOff, PhoneOff, PhoneCall,
  ShieldCheck, MessageSquare, Send, X, HeartPulse,
  User, Stethoscope, AlertCircle, Sparkles, CheckCircle2,
  Maximize2, Minimize2, ArrowRight, ArrowLeft
} from 'lucide-react'

const ICE_SERVERS: RTCIceServer[] = [
  { urls: 'stun:stun.l.google.com:19302' },
  { urls: 'stun:stun1.l.google.com:19302' },
]

interface SessionData {
  room_id: string
  patient_name: string
  doctor_name: string
  call_reason: string
  custom_notes?: string
  status: string
}

interface ChatMessage {
  from: string
  text: string
  ts: string
  self?: boolean
}

function ConsultationInner() {
  const searchParams = useSearchParams()
  const roomId = searchParams.get('room') || ''

  const [session, setSession] = useState<SessionData | null>(null)
  const [loadingSession, setLoadingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')

  // Pre-join & call state
  const [hasJoined, setHasJoined] = useState(false)
  const [callStatus, setCallStatus] = useState<'idle' | 'connecting' | 'connected' | 'ended'>('idle')
  const [peerConnected, setPeerConnected] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  // Media
  const [micOn, setMicOn] = useState(true)
  const [camOn, setCamOn] = useState(true)
  const [fullscreen, setFullscreen] = useState(false)

  // Chat
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState('')

  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)
  const localStreamRef = useRef<MediaStream | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // 1. Fetch public consultation session details
  useEffect(() => {
    if (!roomId) {
      setSessionError('No consultation room code provided. Please use the direct link from your invitation email.')
      setLoadingSession(false)
      return
    }

    const fetchSession = async () => {
      try {
        const res = await fetch(`/api/telemedicine/public/session/${encodeURIComponent(roomId)}`)
        if (!res.ok) throw new Error('Could not load session details')
        const data = await res.json()
        setSession(data)
      } catch {
        setSessionError('Unable to load consultation details. Please ensure the Smriti backend server is active.')
      } finally {
        setLoadingSession(false)
      }
    }
    fetchSession()
  }, [roomId])

  // 2. Start local media preview before joining
  useEffect(() => {
    let mounted = true
    const initPreview = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        if (!mounted) {
          stream.getTracks().forEach(t => t.stop())
          return
        }
        localStreamRef.current = stream
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream
          localVideoRef.current.muted = true
        }
      } catch (err) {
        console.warn('Camera/mic preview error:', err)
      }
    }
    initPreview()

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const cleanup = useCallback(() => {
    localStreamRef.current?.getTracks().forEach(t => t.stop())
    localStreamRef.current = null
    pcRef.current?.close()
    pcRef.current = null
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  useEffect(() => () => cleanup(), [cleanup])

  // 3. Connect to WebRTC Consultation Room
  const joinCall = async () => {
    if (!roomId) return
    setHasJoined(true)
    setCallStatus('connecting')
    setErrorMsg('')

    try {
      let stream = localStreamRef.current
      if (!stream || !stream.active) {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        localStreamRef.current = stream
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream
          localVideoRef.current.muted = true
        }
      }

      const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS })
      pcRef.current = pc

      stream.getTracks().forEach(track => pc.addTrack(track, stream!))

      pc.ontrack = (event) => {
        if (remoteVideoRef.current && event.streams[0]) {
          remoteVideoRef.current.srcObject = event.streams[0]
          setPeerConnected(true)
          setCallStatus('connected')
        }
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/telemedicine/${roomId}`
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      const send = (obj: any) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify(obj))
        }
      }

      pc.onicecandidate = (event) => {
        if (event.candidate) {
          send({ type: 'ice_candidate', candidate: event.candidate })
        }
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
        const patientName = session?.patient_name || 'Patient'
        send({ type: 'join', name: patientName, role: 'patient' })
      }

      ws.onmessage = async (evt) => {
        let msg: any
        try { msg = JSON.parse(evt.data) } catch { return }

        switch (msg.type) {
          case 'peer_joined':
            setPeerConnected(true)
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
              text: 'The clinician has disconnected from this session.',
              ts: new Date().toISOString()
            }])
            break

          case 'chat':
            setChatMessages(prev => [...prev, {
              from: msg.from || 'Clinician',
              text: msg.text,
              ts: msg.ts,
              self: false
            }])
            if (!chatOpen) setChatOpen(true)
            break
        }
      }

      ws.onerror = () => {
        setErrorMsg('Signaling connection error. Please verify the backend is running.')
      }

    } catch (err: any) {
      setErrorMsg('Could not establish media devices: ' + (err.message || 'Permission denied'))
      setCallStatus('idle')
      setHasJoined(false)
    }
  }

  const endCall = () => {
    cleanup()
    setCallStatus('ended')
    setPeerConnected(false)
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
      from: 'You (Patient)',
      text: chatInput.trim(),
      ts: new Date().toISOString(),
      self: true
    }])
    setChatInput('')
  }

  if (loadingSession) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-white">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-300">Connecting to Smriti Patient TeleHealth Gateway...</p>
        </div>
      </div>
    )
  }

  if (sessionError) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-white">
        <div className="max-w-md w-full bg-slate-900 rounded-3xl shadow-xl border border-slate-800 p-8 text-center space-y-4">
          <div className="w-14 h-14 bg-rose-500/20 text-rose-400 rounded-2xl flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold text-white">Invalid Consultation Link</h2>
          <p className="text-xs text-slate-400">{sessionError}</p>
          <Link
            href="/dashboard"
            className="inline-block px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition"
          >
            Go to Doctor Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const patientName = session?.patient_name || 'Patient'
  const doctorName = session?.doctor_name || 'Dr. Vansh Gupta'

  return (
    <div className="min-h-screen bg-[#0A0F1D] text-slate-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
      {/* ── TOP NAV BAR ─────────────────────────────────────────────────── */}
      <header className="bg-slate-900/90 border-b border-slate-800 px-6 py-4 flex items-center justify-between backdrop-blur-md shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-md shadow-blue-500/20">
            <HeartPulse className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-black text-sm tracking-tight text-white flex items-center gap-2">
              Smriti Tele-Neurology Consultation
              <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-400/30 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                Patient Portal
              </span>
            </div>
            <div className="text-[11px] text-slate-400">
              Joining as Patient: <strong className="text-white">{patientName}</strong>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <div className="hidden sm:flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 rounded-xl px-3.5 py-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span className="text-slate-300 font-medium">HIPAA Encrypted Consultation</span>
          </div>

          <Link
            href="/dashboard"
            className="text-[11px] text-slate-400 hover:text-blue-400 bg-slate-800/60 hover:bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700/50 transition flex items-center gap-1"
          >
            <ArrowLeft className="w-3 h-3" />
            Doctor Login
          </Link>
        </div>
      </header>

      {/* ── PRE-JOIN LOBBY ──────────────────────────────────────────────── */}
      {!hasJoined && callStatus !== 'ended' && (
        <main className="flex-1 flex items-center justify-center p-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-950/40 via-slate-950 to-slate-950">
          <div className="max-w-2xl w-full grid md:grid-cols-2 gap-6 bg-slate-900/90 border border-slate-800 p-6 md:p-8 rounded-3xl shadow-2xl backdrop-blur-xl">

            {/* Left: Consultation Details */}
            <div className="flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full">
                  <Stethoscope className="w-3.5 h-3.5" />
                  Doctor has initiated your call
                </div>

                <div className="space-y-1">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Patient Consultation Room</div>
                  <h1 className="text-2xl font-black text-white">
                    Welcome, {patientName}
                  </h1>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Your attending doctor <strong className="text-blue-400">{doctorName}</strong> is waiting for you in this video call.
                  </p>
                </div>

                <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl p-4 space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold">
                      <Stethoscope className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-400 font-semibold uppercase">Attending Clinician</div>
                      <div className="text-sm font-black text-white">{doctorName}</div>
                    </div>
                  </div>

                  <div className="border-t border-slate-700/60 pt-2.5">
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Consultation Topic</div>
                    <div className="text-xs font-bold text-blue-300 mt-0.5">
                      {session?.call_reason || 'Diagnostic & Progression Evaluation'}
                    </div>
                  </div>

                  {session?.custom_notes && (
                    <div className="bg-slate-900/60 rounded-xl p-2.5 text-xs text-slate-300 border border-slate-700/40">
                      <span className="font-bold text-blue-400">Doctor's Note: </span>
                      {session.custom_notes}
                    </div>
                  )}
                </div>
              </div>

              {/* Ready check bullets */}
              <div className="space-y-1.5 text-xs text-slate-400">
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>No login or software download needed</span>
                </div>
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Direct secure connection to {doctorName}</span>
                </div>
              </div>
            </div>

            {/* Right: Camera Preview & Join Button */}
            <div className="flex flex-col items-center justify-between space-y-5 bg-slate-950/70 border border-slate-800/90 rounded-2xl p-5">
              <div className="w-full relative aspect-video bg-slate-900 rounded-xl overflow-hidden border border-slate-800 shadow-inner">
                <video
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {!camOn && (
                  <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                    <VideoOff className="w-8 h-8" />
                    Camera is Turned Off
                  </div>
                )}
                <div className="absolute bottom-2 left-2 bg-black/70 backdrop-blur-md px-2.5 py-1 rounded-md text-[10px] font-bold text-emerald-400 flex items-center gap-1">
                  <User className="w-3 h-3" />
                  You ({patientName})
                </div>
              </div>

              {/* Mic / Cam Toggles before joining */}
              <div className="flex items-center gap-3">
                <button
                  onClick={toggleMic}
                  className={`p-3 rounded-xl transition ${micOn ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-rose-600 text-white'}`}
                  title={micOn ? 'Mute' : 'Unmute'}
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

              {errorMsg && (
                <div className="text-xs text-rose-400 text-center font-medium">
                  {errorMsg}
                </div>
              )}

              {/* Big Join Call CTA */}
              <button
                onClick={joinCall}
                className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 hover:from-blue-500 hover:to-indigo-500 text-white font-black text-sm tracking-wide shadow-lg shadow-blue-600/30 transition transform active:scale-[0.99] flex items-center justify-center gap-3"
              >
                <PhoneCall className="w-5 h-5" />
                Join Video Call with {doctorName}
                <ArrowRight className="w-4 h-4 ml-1" />
              </button>
            </div>
          </div>
        </main>
      )}

      {/* ── ACTIVE LIVE VIDEO CALL ───────────────────────────────────────── */}
      {hasJoined && callStatus !== 'ended' && (
        <main className={`flex-1 flex flex-col ${fullscreen ? 'fixed inset-0 z-50 bg-black' : 'p-4 md:p-6'}`}>
          <div className="flex-1 bg-slate-950 border border-slate-800 rounded-3xl overflow-hidden relative flex flex-col shadow-2xl">

            {/* Video Main Area */}
            <div className="flex-1 relative bg-slate-900 flex items-center justify-center overflow-hidden">
              {/* Doctor's Remote Video */}
              <video
                ref={remoteVideoRef}
                autoPlay
                playsInline
                className="w-full h-full object-cover"
              />

              {/* If doctor hasn't connected stream yet */}
              {!peerConnected && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-slate-950/80 backdrop-blur-md p-6 text-center">
                  <div className="w-16 h-16 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin" />
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-white">
                      Connecting with {doctorName}...
                    </h3>
                    <p className="text-xs text-slate-400 max-w-sm">
                      Please stay on this screen. As soon as the clinician is ready, their video feed will appear automatically.
                    </p>
                  </div>
                </div>
              )}

              {/* Doctor's Status Overlay Tag */}
              <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md border border-slate-700/60 rounded-xl px-3.5 py-2 flex items-center gap-2.5">
                <span className={`w-2.5 h-2.5 rounded-full ${peerConnected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                <div>
                  <div className="text-xs font-bold text-white">
                    {doctorName}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {peerConnected ? 'Live Connection Active' : 'Waiting for Clinician'}
                  </div>
                </div>
              </div>

              {/* Patient Local Picture-in-Picture */}
              <div className="absolute bottom-20 right-4 w-40 sm:w-52 aspect-video rounded-2xl overflow-hidden border-2 border-emerald-500 shadow-2xl bg-slate-900">
                <video
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {!camOn && (
                  <div className="absolute inset-0 bg-slate-900 flex items-center justify-center text-slate-400">
                    <VideoOff className="w-6 h-6" />
                  </div>
                )}
                <div className="absolute bottom-1.5 left-2 bg-emerald-600/90 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-black text-white">
                  You ({patientName})
                </div>
              </div>

              {/* In-Call Chat Overlay */}
              {chatOpen && (
                <div className="absolute bottom-20 left-4 w-80 max-h-80 bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden backdrop-blur-xl">
                  <div className="px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 flex items-center gap-2">
                      <MessageSquare className="w-3.5 h-3.5 text-blue-400" />
                      In-Call Consultation Chat
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
                      placeholder="Type a message to doctor..."
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
            <div className="bg-slate-950 px-6 py-4 border-t border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button
                  onClick={toggleMic}
                  className={`p-3.5 rounded-2xl transition ${micOn ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-rose-600 text-white'}`}
                  title={micOn ? 'Mute Mic' : 'Unmute Mic'}
                >
                  {micOn ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
                </button>
                <button
                  onClick={toggleCam}
                  className={`p-3.5 rounded-2xl transition ${camOn ? 'bg-slate-800 hover:bg-slate-700 text-white' : 'bg-rose-600 text-white'}`}
                  title={camOn ? 'Turn off camera' : 'Turn on camera'}
                >
                  {camOn ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
                </button>
              </div>

              {/* End Call Button */}
              <button
                onClick={endCall}
                className="px-6 py-3.5 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs tracking-wider uppercase transition shadow-lg shadow-rose-600/30 flex items-center gap-2"
              >
                <PhoneOff className="w-4 h-4" />
                Leave Consultation
              </button>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setChatOpen(prev => !prev)}
                  className={`p-3.5 rounded-2xl transition relative ${chatOpen ? 'bg-blue-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-300'}`}
                  title="Toggle Chat"
                >
                  <MessageSquare className="w-5 h-5" />
                  {chatMessages.some(m => !m.self) && !chatOpen && (
                    <span className="absolute top-2 right-2 w-2 h-2 bg-blue-400 rounded-full" />
                  )}
                </button>
                <button
                  onClick={() => setFullscreen(prev => !prev)}
                  className="p-3.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  title="Fullscreen"
                >
                  {fullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* ── POST-CALL THANK YOU SCREEN ───────────────────────────────────── */}
      {callStatus === 'ended' && (
        <main className="flex-1 flex items-center justify-center p-6 bg-slate-950">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 p-8 rounded-3xl shadow-2xl text-center space-y-5">
            <div className="w-16 h-16 bg-blue-500/10 border border-blue-500/20 text-blue-400 rounded-2xl flex items-center justify-center mx-auto">
              <Sparkles className="w-8 h-8" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-black text-white">Consultation Completed</h2>
              <p className="text-xs text-slate-400 leading-relaxed">
                Thank you, <strong className="text-slate-200">{patientName}</strong>. Your video consultation with {doctorName} has concluded.
              </p>
            </div>
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3 text-[11px] text-slate-400">
              Any updated clinical prescriptions will be reflected in your electronic records.
            </div>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition"
            >
              Rejoin Session
            </button>
          </div>
        </main>
      )}
    </div>
  )
}

export default function ConsultationPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ConsultationInner />
    </Suspense>
  )
}
