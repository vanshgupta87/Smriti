'use client'

import React from 'react'
import { ShieldAlert, CheckCircle2, AlertTriangle, Send } from 'lucide-react'

interface AriaProtocolCardProps {
  patient: any
  onAuthorizeFhir: () => void
}

export default function AriaProtocolCard({
  patient,
  onAuthorizeFhir
}: AriaProtocolCardProps) {
  if (!patient) return null

  const isAmyloidPositive = (patient.pet?.centiloids || 0) >= 20.0
  const ariaRisk = patient.pet?.ariaRiskScore || 20

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Amyloid Burden Scale */}
        <div className="aws-card p-6 bg-white flex flex-col items-center justify-center text-center">
          <div className="text-xs font-bold text-[#565959] uppercase tracking-wider mb-1">
            Amyloid Centiloid Burden
          </div>
          <p className="text-xs text-[#565959] mb-5">
            Standardized Centiloid Scale (GE Vizamyl Standard)
          </p>

          <div className="w-36 h-36 rounded-full border-8 border-[#EAEDED] flex items-center justify-center relative shadow-inner">
            <div className="text-center">
              <div className="text-3xl font-extrabold text-[#007185] font-mono leading-none">
                {patient.pet?.centiloids}
              </div>
              <div className="text-[11px] text-[#565959] font-bold mt-1">Centiloids</div>
            </div>
          </div>

          <div className="mt-5">
            <span className={`inline-block text-xs px-3 py-1 rounded-full font-bold border ${
              isAmyloidPositive 
                ? 'aws-badge-red' 
                : 'aws-badge-green'
            }`}>
              {isAmyloidPositive ? 'Amyloid Positive (≥20 CL)' : 'Amyloid Negative (<20 CL)'}
            </span>
          </div>
        </div>

        {/* ARIA-E / ARIA-H Risk Breakdown */}
        <div className="aws-card p-6 bg-white space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-[#EAEDED]">
            <h4 className="text-xs font-bold text-[#0F1111] uppercase tracking-wider">
              ARIA-E / ARIA-H Safety Index
            </h4>
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-[#EAEDED] text-[#B12704] border border-[#D5DBDB]">
              {ariaRisk} / 100
            </span>
          </div>

          <p className="text-xs text-[#565959]">
            Evaluates edema and cerebral microhemorrhage risk prior to Monoclonal Antibody DMT initiation
          </p>

          <div className="space-y-2 text-xs">
            <div className="p-2.5 bg-[#F7FAFA] rounded border border-[#D5DBDB] flex justify-between">
              <span className="text-[#565959]">APOE-ε4 Homozygosity:</span>
              <span className="font-bold font-mono text-[#0F1111]">
                {patient.biomarkers?.apoe4 === 2 ? 'High Risk (ε4/ε4)' : `${patient.biomarkers?.apoe4} Allele`}
              </span>
            </div>

            <div className="p-2.5 bg-[#F7FAFA] rounded border border-[#D5DBDB] flex justify-between">
              <span className="text-[#565959]">Baseline WMH Volume:</span>
              <span className="font-bold font-mono text-[#0F1111]">
                {patient.mri?.wmhVolumeCm3} cm³
              </span>
            </div>

            <div className="p-2.5 bg-[#F7FAFA] rounded border border-[#D5DBDB] flex justify-between">
              <span className="text-[#565959]">Tau Braak Staging:</span>
              <span className="font-bold font-mono text-[#0F1111]">
                {patient.pet?.tauSuvr > 1.3 ? 'Stage III/IV (High)' : 'Stage I/II (Intermediate)'}
              </span>
            </div>
          </div>
        </div>

        {/* Monoclonal Antibody Protocol Decision */}
        <div className="aws-card p-6 bg-white flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-[#007185] uppercase tracking-wider mb-2">
              DMT Eligibility & Safety Directive
            </div>
            
            <h4 className="text-sm font-extrabold text-[#0F1111] mb-2">
              Lecanemab / Donanemab Readiness
            </h4>

            <p className="text-xs text-[#0F1111] leading-relaxed font-medium">
              {patient.pet?.dmtCandidate 
                ? "Candidate meets full clinical trial criteria for Anti-Amyloid Monoclonal Antibody therapy. Confirmed Amyloid+ with mild impairment and manageable ARIA safety profile."
                : "Candidate does not currently meet standard DMT criteria. Alternative symptomatic treatment protocol recommended."
              }
            </p>
          </div>

          <button
            onClick={onAuthorizeFhir}
            className="aws-btn-primary w-full mt-4 py-2.5 rounded-md text-xs font-extrabold flex items-center justify-center gap-1.5 shadow-sm"
          >
            <Send className="w-4 h-4" />
            <span>Transmit 3-Month Safety MRI Order via FHIR</span>
          </button>
        </div>

      </div>
    </div>
  )
}
