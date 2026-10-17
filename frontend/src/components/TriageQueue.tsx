'use client'

import React from 'react'
import { ArrowUpDown, ChevronRight, AlertTriangle, CheckCircle2, Clock, Sparkles } from 'lucide-react'

interface TriageQueueProps {
  patients: any[]
  selectedPatient: any
  setSelectedPatient: (p: any) => void
  onOpenDossier: (p: any) => void
  stageFilter: string
  setStageFilter: (s: string) => void
  velocityFilter: string
  setVelocityFilter: (v: string) => void
}

export default function TriageQueue({
  patients,
  selectedPatient,
  setSelectedPatient,
  onOpenDossier,
  stageFilter,
  setStageFilter,
  velocityFilter,
  setVelocityFilter
}: TriageQueueProps) {
  
  const highVelocityCount = patients.filter(p => p.velocity === 'High Velocity').length
  const stage34Count = patients.filter(p => p.currentStage >= 3).length
  const dmtCount = patients.filter(p => p.pet?.dmtCandidate).length

  return (
    <div className="space-y-5">
      {/* Top Enterprise Stats Summary - Amazon/AWS Style */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        <div className="aws-card p-4 bg-white border-l-4 border-l-[#007185]">
          <div className="text-[11px] font-bold text-[#565959] uppercase tracking-wider">Active Queue Capacity</div>
          <div className="text-2xl font-extrabold text-[#0F1111] mt-1">
            {patients.length} <span className="text-xs font-normal text-[#565959]">Patients Screened</span>
          </div>
          <div className="text-[11px] text-[#007185] font-semibold mt-0.5">Ranked by 24m Velocity Score</div>
        </div>

        <div className="aws-card p-4 bg-white border-l-4 border-l-[#B12704]">
          <div className="text-[11px] font-bold text-[#565959] uppercase tracking-wider">High Velocity Progressors</div>
          <div className="text-2xl font-extrabold text-[#B12704] mt-1">
            {highVelocityCount}
          </div>
          <div className="text-[11px] text-[#565959] mt-0.5">Urgent Specialty Escalation</div>
        </div>

        <div className="aws-card p-4 bg-white border-l-4 border-l-[#FF9900]">
          <div className="text-[11px] font-bold text-[#565959] uppercase tracking-wider">Advanced Imaging (Stages 3/4)</div>
          <div className="text-2xl font-extrabold text-[#8C52FF] text-[#0F1111] mt-1">
            {stage34Count}
          </div>
          <div className="text-[11px] text-[#565959] mt-0.5">Targeted Scanner Capacity Routing</div>
        </div>

        <div className="aws-card p-4 bg-white border-l-4 border-l-[#067D62]">
          <div className="text-[11px] font-bold text-[#565959] uppercase tracking-wider">Confirmed DMT Candidates</div>
          <div className="text-2xl font-extrabold text-[#067D62] mt-1">
            {dmtCount}
          </div>
          <div className="text-[11px] text-[#565959] mt-0.5">Lecanemab/Donanemab Protocol</div>
        </div>

      </div>

      {/* Filter and Category Strip */}
      <div className="aws-card p-3.5 bg-white flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="text-xs font-bold text-[#0F1111]">Filters:</span>
          
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="bg-[#F7FAFA] border border-[#D5DBDB] text-[#0F1111] text-xs rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
          >
            <option value="all">All Diagnostic Stages (1-4)</option>
            <option value="1">Stage 1: Primary Cognitive Intake</option>
            <option value="2">Stage 2: Blood Biomarkers (p-tau217)</option>
            <option value="3">Stage 3: 3D Volumetric Brain MRI</option>
            <option value="4">Stage 4: Molecular Amyloid PET</option>
          </select>

          <select
            value={velocityFilter}
            onChange={(e) => setVelocityFilter(e.target.value)}
            className="bg-[#F7FAFA] border border-[#D5DBDB] text-[#0F1111] text-xs rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
          >
            <option value="all">All Velocity Tiers</option>
            <option value="high velocity">High Velocity</option>
            <option value="moderate">Moderate</option>
            <option value="stable">Stable</option>
          </select>
        </div>

        <div className="text-xs text-[#565959] font-medium">
          Showing <b className="text-[#0F1111] font-bold">{patients.length}</b> clinical records
        </div>
      </div>

      {/* Enterprise Patient Table */}
      <div className="aws-card bg-white overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#F0F2F2] border-b border-[#D5DBDB] text-[11px] font-bold text-[#565959] uppercase">
                <th className="py-3 px-4">Patient Name / MRN</th>
                <th className="py-3 px-4">Age / Gender</th>
                <th className="py-3 px-4">24-Month Risk Score</th>
                <th className="py-3 px-4">Decline Velocity</th>
                <th className="py-3 px-4">Current Diagnostic Stage</th>
                <th className="py-3 px-4">Biomarker Highlights</th>
                <th className="py-3 px-4">Clinical Action Status</th>
                <th className="py-3 px-4 text-right">Dossier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EAEDED]">
              {patients.map((p) => {
                const isSelected = selectedPatient?.id === p.id
                return (
                  <tr
                    key={p.id}
                    onClick={() => setSelectedPatient(p)}
                    className={`cursor-pointer transition ${
                      isSelected 
                        ? 'bg-[#F0F9FF] border-l-4 border-l-[#007185]' 
                        : 'hover:bg-[#F7FAFA]'
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="font-bold text-[#0F1111] text-xs">{p.name}</div>
                      <div className="text-[11px] text-[#565959] font-mono">{p.mrn} • {p.id}</div>
                    </td>
                    
                    <td className="py-3 px-4 text-[#0F1111] font-medium">
                      {p.age}y <span className="text-slate-400">•</span> {p.gender}
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-[#EAEDED] h-2 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              p.riskScore > 0.65 ? 'bg-[#B12704]' : p.riskScore > 0.35 ? 'bg-[#FF9900]' : 'bg-[#067D62]'
                            }`}
                            style={{ width: `${p.riskScore * 100}%` }}
                          />
                        </div>
                        <span className="font-mono font-bold text-xs text-[#0F1111]">
                          {(p.riskScore * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <span className={`inline-block text-[10px] px-2 py-0.5 rounded font-bold border ${
                        p.velocity === 'High Velocity'
                          ? 'aws-badge-red'
                          : p.velocity === 'Moderate'
                          ? 'bg-amber-50 text-amber-900 border-amber-300'
                          : 'aws-badge-green'
                      }`}>
                        {p.velocity}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-[#0F1111]">
                        Stage {p.currentStage}: {
                          p.currentStage === 1 ? 'Cognitive Intake' :
                          p.currentStage === 2 ? 'Plasma Biomarkers' :
                          p.currentStage === 3 ? '3D Brain MRI' : 'Amyloid PET'
                        }
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono text-[#0F1111]">
                      <span>MMSE: <b>{p.cognitive?.mmse}</b></span>
                      {p.biomarkers?.plasmaPtau217 && (
                        <span className="ml-2 text-[#007185]">p-tau: <b>{p.biomarkers.plasmaPtau217}</b></span>
                      )}
                      {p.pet?.centiloids > 0 && (
                        <span className="ml-2 text-[#B12704]">CL: <b>{p.pet.centiloids}</b></span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-[#565959] font-medium">
                      {p.status}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onOpenDossier(p)
                        }}
                        className="aws-btn-secondary px-3 py-1 rounded text-xs font-bold shadow-xs hover:bg-[#F7FAFA]"
                      >
                        Open Dossier →
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
