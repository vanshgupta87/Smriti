'use client'

import React from 'react'
import { Activity, Brain, TestTube2, Scan, ShieldAlert, FileText, CheckCircle } from 'lucide-react'

interface PatientDossierProps {
  patient: any
  onInspectShap: () => void
  onAuthorizeFhir: () => void
}

export default function PatientDossier({
  patient,
  onInspectShap,
  onAuthorizeFhir
}: PatientDossierProps) {
  if (!patient) return null

  const steps = [
    {
      stage: 1,
      title: 'Stage 1: Primary Cognitive Intake',
      subtitle: 'MMSE, MoCA, CDR-SB, FAQ',
      value: `MMSE: ${patient.cognitive?.mmse} | CDR-SB: ${patient.cognitive?.cdrsb}`,
      gate: 'Cutoff T1: 0.074',
      status: patient.currentStage >= 1 ? 'Completed' : 'Pending'
    },
    {
      stage: 2,
      title: 'Stage 2: Blood Biomarkers & APOE',
      subtitle: 'Plasma p-tau217, Aβ42/40, NfL',
      value: `p-tau217: ${patient.biomarkers?.plasmaPtau217} pg/mL`,
      gate: 'Cutoff T2: 0.074',
      status: patient.currentStage >= 2 ? 'Completed' : 'Pending'
    },
    {
      stage: 3,
      title: 'Stage 3: 3D Brain MRI Volumetry',
      subtitle: 'Hippocampus ICV, Ventricles, WMH',
      value: `Hippo ICV: ${patient.mri?.hippocampalIcvRatio} | WMH: ${patient.mri?.wmhVolumeCm3}cc`,
      gate: 'Cutoff T3: 0.082',
      status: patient.currentStage >= 3 ? 'Completed' : 'Pending'
    },
    {
      stage: 4,
      title: 'Stage 4: Molecular PET & Safety',
      subtitle: 'Centiloids, Tau SUVR, ARIA Index',
      value: `Centiloids: ${patient.pet?.centiloids} CL | ARIA Risk: ${patient.pet?.ariaRiskScore}/100`,
      gate: 'Cutoff T4: 0.099',
      status: patient.currentStage >= 4 ? 'Completed' : 'Pending'
    }
  ]

  return (
    <div className="space-y-6">
      
      {/* Patient Header Banner - Amazon Product Header Style */}
      <div className="aws-card p-6 bg-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-lg bg-[#232F3E] text-white flex items-center justify-center font-bold text-xl shadow">
            {patient.name?.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-extrabold text-[#0F1111]">{patient.name}</h2>
              <span className="text-xs px-2.5 py-0.5 rounded bg-[#EAEDED] text-[#0F1111] border border-[#D5DBDB] font-mono font-bold">
                {patient.mrn}
              </span>
            </div>
            <p className="text-xs text-[#565959] mt-1 font-medium">
              {patient.age} Years • {patient.gender} • APOE-ε4 Carrier: <b className="text-[#0F1111]">({patient.biomarkers?.apoe4} Allele)</b> • Last Exam Date: {patient.lastVisit}
            </p>
          </div>
        </div>

        {/* 24-Month Progression Velocity Score */}
        <div className="text-left md:text-right border-t md:border-t-0 pt-3 md:pt-0">
          <div className="text-xs font-bold text-[#565959] uppercase tracking-wider">24-Month Rapid Progression Risk</div>
          <div className="text-3xl font-extrabold text-[#007185] font-mono mt-0.5">
            {(patient.riskScore * 100).toFixed(0)}%
          </div>
          <span className={`inline-block text-xs px-2.5 py-0.5 rounded font-bold mt-1 border ${
            patient.velocity === 'High Velocity' 
              ? 'aws-badge-red' 
              : 'aws-badge-green'
          }`}>
            {patient.velocity}
          </span>
        </div>
      </div>

      {/* 4-Stage Clinical Stepper Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {steps.map((st) => {
          const isCurrent = patient.currentStage === st.stage
          const isDone = patient.currentStage > st.stage
          return (
            <div
              key={st.stage}
              className={`aws-card p-4 transition ${
                isCurrent 
                  ? 'border-2 border-[#007185] bg-[#F0F9FF]' 
                  : isDone 
                  ? 'bg-white' 
                  : 'bg-[#F7FAFA] opacity-70'
              }`}
            >
              <div className="flex justify-between items-center mb-2">
                <span className={`w-6 h-6 rounded flex items-center justify-center font-bold text-xs ${
                  isCurrent ? 'bg-[#007185] text-white' : isDone ? 'bg-[#067D62] text-white' : 'bg-[#D5DBDB] text-[#565959]'
                }`}>
                  {st.stage}
                </span>
                <span className="text-[10px] font-mono font-bold text-[#565959] bg-[#EAEDED] px-1.5 py-0.5 rounded border border-[#D5DBDB]">
                  {st.gate}
                </span>
              </div>
              <h4 className="font-bold text-[#0F1111] text-xs">{st.title}</h4>
              <p className="text-[11px] text-[#565959] mt-0.5">{st.subtitle}</p>
              <div className="mt-2.5 pt-2 border-t border-[#EAEDED] text-[11px] font-mono font-bold text-[#007185]">
                {st.value}
              </div>
            </div>
          )
        })}
      </div>

      {/* Multimodal Metric Dossier Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        
        {/* Cognitive & EHR Intake */}
        <div className="aws-card p-5 bg-white">
          <h3 className="font-bold text-xs text-[#0F1111] uppercase tracking-wider flex items-center gap-2 mb-3 pb-2 border-b border-[#EAEDED]">
            <Brain className="w-4 h-4 text-[#007185]" />
            Cognitive & Functional Scores
          </h3>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">MMSE Total (0-30)</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.cognitive?.mmse}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">MoCA Total (0-30)</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.cognitive?.moca}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">CDR Sum of Boxes (0-18)</span>
              <span className="font-bold font-mono text-[#007185]">{patient.cognitive?.cdrsb}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#565959]">FAQ Functional Activity</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.cognitive?.faq}</span>
            </div>
          </div>
        </div>

        {/* Biofluid Biomarkers */}
        <div className="aws-card p-5 bg-white">
          <h3 className="font-bold text-xs text-[#0F1111] uppercase tracking-wider flex items-center gap-2 mb-3 pb-2 border-b border-[#EAEDED]">
            <TestTube2 className="w-4 h-4 text-[#007185]" />
            Harmonized Blood Biomarkers
          </h3>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">Plasma p-tau217 (Fujirebio)</span>
              <span className="font-bold font-mono text-[#007185]">{patient.biomarkers?.plasmaPtau217} pg/mL</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">Plasma Aβ42 / Aβ40 Ratio</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.biomarkers?.plasmaAbRatio}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">Neurofilament Light (NfL)</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.biomarkers?.nfl} pg/mL</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#565959]">Glial Fibrillary (GFAP)</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.biomarkers?.gfap} pg/mL</span>
            </div>
          </div>
        </div>

        {/* Imaging & Molecular Load */}
        <div className="aws-card p-5 bg-white">
          <h3 className="font-bold text-xs text-[#0F1111] uppercase tracking-wider flex items-center gap-2 mb-3 pb-2 border-b border-[#EAEDED]">
            <Scan className="w-4 h-4 text-[#007185]" />
            Imaging Volumetrics & Centiloids
          </h3>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">Hippocampus / ICV Ratio</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.mri?.hippocampalIcvRatio}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">White Matter Hyperintensity</span>
              <span className="font-bold font-mono text-[#B12704]">{patient.mri?.wmhVolumeCm3} cm³</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F7FAFA]">
              <span className="text-[#565959]">Amyloid Centiloid Score</span>
              <span className="font-bold font-mono text-[#007185]">{patient.pet?.centiloids} CL</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-[#565959]">Tau Meta-Temporal SUVR</span>
              <span className="font-bold font-mono text-[#0F1111]">{patient.pet?.tauSuvr}</span>
            </div>
          </div>
        </div>

      </div>

      {/* CDS Decision Directive Banner */}
      <div className="aws-card p-6 bg-gradient-to-r from-[#F0F9FF] to-white border-2 border-[#BAE6FD] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-xs font-bold text-[#007185] uppercase tracking-wider flex items-center gap-1.5 mb-1.5">
            <Activity className="w-4 h-4 text-[#007185]" />
            Automated Clinical Decision Support Recommendation
          </div>
          <p className="text-xs text-[#0F1111] font-semibold leading-relaxed">
            {patient.cdsRecommendation}
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={onInspectShap}
            className="aws-btn-secondary px-4 py-2 rounded-md text-xs font-bold shadow-xs hover:bg-[#F7FAFA]"
          >
            Inspect TreeSHAP
          </button>
          
          <button
            onClick={onAuthorizeFhir}
            className="aws-btn-primary px-5 py-2 rounded-md text-xs font-extrabold shadow-sm flex items-center gap-1.5"
          >
            ⚡ 1-Click FHIR Writeback
          </button>
        </div>
      </div>

    </div>
  )
}
