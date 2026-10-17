'use client'

import React from 'react'
import { SlidersHorizontal, CheckSquare, Square, Zap, CheckCircle2, AlertTriangle } from 'lucide-react'

interface DynamicLabProps {
  labStage: number
  setLabStage: (s: number) => void
  availableFields: Record<string, boolean>
  setAvailableFields: (f: Record<string, boolean>) => void
  labInput: any
  setLabInput: (i: any) => void
  labResult: any
  labLoading: boolean
  onRunInference: () => void
  indiaCalibration: boolean
}

export default function DynamicLab({
  labStage,
  setLabStage,
  availableFields,
  setAvailableFields,
  labInput,
  setLabInput,
  labResult,
  labLoading,
  onRunInference,
  indiaCalibration
}: DynamicLabProps) {
  
  const toggleField = (key: string) => {
    setAvailableFields({
      ...availableFields,
      [key]: !availableFields[key]
    })
  }

  return (
    <div className="space-y-6">
      <div className="aws-card p-6 bg-white">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#EAEDED] mb-5">
          <div>
            <h3 className="text-base font-extrabold text-[#0F1111] flex items-center gap-2">
              <SlidersHorizontal className="w-5 h-5 text-[#007185]" />
              Dynamic Diagnostic Feature Playground (Native NaN Ingestion)
            </h3>
            <p className="text-xs text-[#565959] mt-0.5">
              Select available clinical tests using checkboxes. Unchecked features are automatically passed as <code className="bg-[#EAEDED] px-1 rounded font-mono text-[#B12704]">NaN</code> to test XGBoost native missing-value split routing without defaulting to zero.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <span className="text-xs font-bold text-[#565959]">Active Stage:</span>
            {[1, 2, 3, 4].map((s) => (
              <button
                key={s}
                onClick={() => setLabStage(s)}
                className={`px-3 py-1.5 rounded-md text-xs font-bold transition ${
                  labStage === s
                    ? 'aws-btn-primary shadow-xs'
                    : 'aws-btn-secondary hover:bg-[#F7FAFA]'
                }`}
              >
                Stage {s}
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Checkbox Grid - AWS Console Style */}
        <div className="p-4 bg-[#F7FAFA] rounded-md border border-[#D5DBDB] mb-6">
          <div className="text-xs font-bold text-[#0F1111] uppercase tracking-wider mb-3">
            Clinical Diagnostics Selector (Check Available Tests):
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            {Object.keys(availableFields).map((k) => (
              <label
                key={k}
                onClick={() => toggleField(k)}
                className="flex items-center gap-2.5 cursor-pointer select-none p-2 bg-white rounded border border-[#D5DBDB] hover:border-[#007185] transition"
              >
                <input
                  type="checkbox"
                  checked={availableFields[k]}
                  onChange={() => {}}
                  className="w-4 h-4 accent-[#FF9900] rounded"
                />
                <span className="font-semibold text-[#0F1111] text-[11px]">
                  {k.toUpperCase().replace('_', ' ')}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Input Parameters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs my-4">
          
          <div>
            <label className="block text-[#565959] font-bold mb-1">Patient Age</label>
            <input
              type="number"
              value={labInput.age}
              onChange={(e) => setLabInput({ ...labInput, age: e.target.value })}
              className="w-full bg-[#F7FAFA] border border-[#D5DBDB] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
            />
          </div>

          <div>
            <label className="block text-[#565959] font-bold mb-1">Formal Education (Years)</label>
            <input
              type="number"
              value={labInput.education_years}
              onChange={(e) => setLabInput({ ...labInput, education_years: e.target.value })}
              className="w-full bg-[#F7FAFA] border border-[#D5DBDB] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
            />
          </div>

          {availableFields.mmse && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">MMSE Total Score (0-30)</label>
              <input
                type="number"
                value={labInput.mmse}
                onChange={(e) => setLabInput({ ...labInput, mmse: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

          {availableFields.moca && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">MoCA Total Score (0-30)</label>
              <input
                type="number"
                value={labInput.moca}
                onChange={(e) => setLabInput({ ...labInput, moca: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

          {availableFields.cdrsb && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">CDR Sum of Boxes (0-18)</label>
              <input
                type="number"
                step="0.5"
                value={labInput.cdrsb}
                onChange={(e) => setLabInput({ ...labInput, cdrsb: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

          {availableFields.apoe4 && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">APOE-ε4 Allele Count (0, 1, 2)</label>
              <input
                type="number"
                value={labInput.apoe4_count}
                onChange={(e) => setLabInput({ ...labInput, apoe4_count: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

          {availableFields.plasma_ptau217 && labStage >= 2 && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">Plasma p-tau217 (pg/mL)</label>
              <input
                type="number"
                step="0.05"
                value={labInput.plasma_ptau217}
                onChange={(e) => setLabInput({ ...labInput, plasma_ptau217: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

          {availableFields.centiloids && labStage >= 4 && (
            <div>
              <label className="block text-[#007185] font-bold mb-1">Amyloid Centiloids (CL)</label>
              <input
                type="number"
                value={labInput.centiloids}
                onChange={(e) => setLabInput({ ...labInput, centiloids: e.target.value })}
                className="w-full bg-white border-2 border-[#BAE6FD] rounded-md px-3 py-1.5 text-[#0F1111] font-mono focus:outline-none focus:ring-1 focus:ring-[#FF9900]"
              />
            </div>
          )}

        </div>

        {/* Action Trigger Button */}
        <button
          onClick={onRunInference}
          disabled={labLoading}
          className="aws-btn-primary w-full py-3 rounded-md text-xs font-extrabold shadow-sm flex items-center justify-center gap-2 mt-4 transition"
        >
          <Zap className="w-4 h-4" />
          <span>{labLoading ? 'Evaluating Native XGBoost NaN Decision Paths...' : 'Execute Dynamic Dual-Head Model Inference'}</span>
        </button>

        {/* Dual-Head Output Result Card */}
        {labResult && (
          <div className="mt-6 p-5 bg-[#F7FAFA] rounded-md border border-[#D5DBDB] space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-[#D5DBDB]">
              <div>
                <h4 className="text-sm font-extrabold text-[#0F1111]">
                  Dual-Head Stage {labResult.stage} Diagnostic Output
                </h4>
                <p className="text-[11px] text-[#565959]">
                  Computed across available features with missing attributes safely evaluated via learned NaN branches
                </p>
              </div>

              <span className={`text-xs px-3 py-1 rounded font-bold border ${
                labResult.gating_decision?.escalation_recommended 
                  ? 'aws-badge-red' 
                  : 'aws-badge-green'
              }`}>
                {labResult.gating_decision?.escalation_recommended ? 'ESCALATION RECOMMENDED' : 'PRIMARY CARE SURVEILLANCE'}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              
              <div className="p-3 bg-white rounded border border-[#D5DBDB]">
                <span className="text-[11px] text-[#565959] font-bold block">Current 3-Class Diagnosis:</span>
                <span className="text-sm font-extrabold text-[#0F1111] mt-0.5 block">
                  {labResult.dual_head?.current_diagnosis}
                </span>
              </div>

              <div className="p-3 bg-white rounded border border-[#D5DBDB]">
                <span className="text-[11px] text-[#565959] font-bold block">24m Rapid Progression Risk:</span>
                <span className="text-sm font-extrabold text-[#007185] font-mono mt-0.5 block">
                  {(labResult.dual_head?.progression_24m_risk * 100).toFixed(1)}%
                </span>
              </div>

              <div className="p-3 bg-white rounded border border-[#D5DBDB]">
                <span className="text-[11px] text-[#565959] font-bold block">Gate Cutoff (T{labResult.stage}):</span>
                <span className="text-sm font-extrabold text-[#0F1111] font-mono mt-0.5 block">
                  {(labResult.gating_decision?.optimal_threshold * 100).toFixed(1)}%
                </span>
              </div>

            </div>

            <div className="p-3 bg-[#F0F9FF] border border-[#BAE6FD] rounded text-xs text-[#0369A1] font-semibold">
              <b>CDS Directive:</b> {labResult.cds_recommendation}
            </div>

          </div>
        )}

      </div>
    </div>
  )
}
