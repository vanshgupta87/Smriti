'use client'

import React from 'react'
import { Activity, Shield, Search, Globe, User, Bell, ChevronDown } from 'lucide-react'

interface NavbarProps {
  role: string
  setRole: (r: string) => void
  indiaCalibration: boolean
  setIndiaCalibration: (v: boolean) => void
  searchQuery: string
  setSearchQuery: (q: string) => void
  selectedPatient: any
}

export default function Navbar({
  role,
  setRole,
  indiaCalibration,
  setIndiaCalibration,
  searchQuery,
  setSearchQuery,
  selectedPatient
}: NavbarProps) {
  return (
    <header className="bg-[#131921] text-white select-none sticky top-0 z-50 shadow-md">
      {/* Primary Top Bar */}
      <div className="h-14 px-4 flex items-center justify-between gap-4">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 cursor-pointer">
            <div className="w-8 h-8 rounded bg-[#007185] flex items-center justify-center font-bold text-white text-sm shadow">
              GE
            </div>
            <div>
              <div className="font-extrabold text-base tracking-tight text-white flex items-center gap-1.5 leading-none">
                StepWise
                <span className="text-[10px] font-semibold bg-[#FF9900] text-[#0F1111] px-1.5 py-0.5 rounded">CDS v2.0</span>
              </div>
              <div className="text-[10px] text-[#A6B0B0] mt-0.5">Precision Care Clinical Center</div>
            </div>
          </div>
        </div>

        {/* Search Bar - Amazon style */}
        <div className="flex-1 max-w-2xl mx-4">
          <div className="relative flex items-center">
            <div className="absolute left-3 text-[#565959] pointer-events-none">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              placeholder="Search patient records by name, MRN (e.g. GE-HC-1002), or PTID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white text-[#0F1111] placeholder-[#565959] text-xs rounded-md pl-9 pr-24 py-2 border border-[#D5DBDB] focus:outline-none focus:ring-2 focus:ring-[#FF9900] transition"
            />
            <div className="absolute right-1 flex items-center">
              <span className="text-[10px] bg-[#EAEDED] text-[#565959] px-2 py-1 rounded font-mono border border-[#D5DBDB]">
                ESC to clear
              </span>
            </div>
          </div>
        </div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-3 shrink-0 text-xs">
          
          {/* India LASI-DAD Recalibration Switch */}
          <button
            onClick={() => setIndiaCalibration(!indiaCalibration)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md border transition ${
              indiaCalibration 
                ? 'bg-[#007185] border-[#007185] text-white shadow-xs font-semibold' 
                : 'bg-[#232F3E] border-[#37475A] text-[#D5DBDB] hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5 text-[#FF9900]" />
            <span>🇮🇳 India LASI-DAD</span>
            <span className={`w-2 h-2 rounded-full ${indiaCalibration ? 'bg-[#FF9900] animate-pulse' : 'bg-slate-500'}`} />
          </button>

          {/* Role Context Selector */}
          <div className="flex items-center gap-1 bg-[#232F3E] p-1 rounded-md border border-[#37475A]">
            {['Neurologist', 'Primary Care'].map((r) => (
              <button
                key={r}
                onClick={() => setRole(r)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                  role === r ? 'bg-[#007185] text-white shadow-xs' : 'text-[#A6B0B0] hover:text-white'
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          {/* Active Patient Pill */}
          {selectedPatient && (
            <div className="hidden lg:flex items-center gap-2 bg-[#232F3E] px-3 py-1.5 rounded-md border border-[#37475A]">
              <User className="w-3.5 h-3.5 text-[#A6B0B0]" />
              <span className="text-[#A6B0B0]">MRN:</span>
              <span className="font-mono font-bold text-white">{selectedPatient.mrn}</span>
              <span className="text-slate-500">|</span>
              <span className="text-white font-medium">{selectedPatient.age}y {selectedPatient.gender}</span>
            </div>
          )}

          {/* System Status Pill */}
          <div className="hidden xl:flex items-center gap-1.5 bg-[#067D62]/20 border border-[#067D62]/50 text-[#067D62] text-[11px] font-bold px-2.5 py-1 rounded-md">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-emerald-300">Models Online</span>
          </div>

        </div>

      </div>
    </header>
  )
}
