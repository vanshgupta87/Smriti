'use client'

import React from 'react'
import { BarChart3, Copy, Check, FileText } from 'lucide-react'

interface TreeShapWaterfallProps {
  patient: any
}

export default function TreeShapWaterfall({ patient }: TreeShapWaterfallProps) {
  const [copied, setCopied] = React.useState(false)

  if (!patient) return null

  const handleCopyNote = () => {
    setCopied(true)
    setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Waterfall Plot Card */}
        <div className="col-span-2 aws-card p-6 bg-white">
          <div className="flex justify-between items-center pb-4 border-b border-[#EAEDED] mb-4">
            <div>
              <h3 className="text-base font-extrabold text-[#0F1111] flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-[#007185]" />
                Dual-Head Attribution & TreeSHAP Waterfall
              </h3>
              <p className="text-xs text-[#565959] mt-0.5">
                Exact mathematical feature contributions driving 24-month progression velocity
              </p>
            </div>

            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-[#EAEDED] text-[#0F1111] border border-[#D5DBDB]">
              Base Log-Odds: 0.120
            </span>
          </div>

          {/* Horizontal Attribution Bars */}
          <div className="space-y-4 my-6">
            {patient.shapDrivers?.map((d: any, idx: number) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-[#0F1111]">{d.feature}</span>
                  <span className={`font-mono font-bold ${d.type === 'risk' ? 'text-[#B12704]' : 'text-[#067D62]'}`}>
                    {d.type === 'risk' ? `+${d.impact}` : `-${d.impact}`}
                  </span>
                </div>
                <div className="w-full bg-[#EAEDED] h-2.5 rounded-full overflow-hidden flex">
                  <div
                    className={`h-full rounded-full ${d.type === 'risk' ? 'bg-[#B12704]' : 'bg-[#067D62]'}`}
                    style={{ width: `${Math.min(100, d.impact * 260)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="p-3.5 bg-[#F7FAFA] rounded-md border border-[#D5DBDB] flex justify-between items-center text-xs font-medium">
            <span className="text-[#565959]">
              Calibrated Rapid Progression Risk: <b className="text-[#007185] font-mono">{(patient.riskScore * 100).toFixed(1)}%</b>
            </span>
            <span className="text-[#565959] text-[11px]">
              Isotonic Probability Calibrator Active
            </span>
          </div>
        </div>

        {/* AI Neurologist Clinical CDS Note */}
        <div className="aws-card p-6 bg-white flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-[#007185] uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-[#007185]" />
              Automated Clinical EHR Summary
            </div>
            
            <div className="p-4 bg-[#F7FAFA] border border-[#D5DBDB] rounded-md text-xs text-[#0F1111] font-mono leading-relaxed space-y-2 select-text">
              <p><b>PATIENT:</b> {patient.name} ({patient.mrn})</p>
              <p><b>DIAGNOSIS TIER:</b> {patient.stageName}</p>
              <p><b>24M VELOCITY RISK:</b> <b>{(patient.riskScore * 100).toFixed(0)}%</b> ({patient.velocity}). Primary drivers: plasma p-tau217 ({patient.biomarkers?.plasmaPtau217} pg/mL) and hippocampal ratio ({patient.mri?.hippocampalIcvRatio}).</p>
              <p><b>SAFETY PROFILE:</b> ARIA-E score: <b>{patient.pet?.ariaRiskScore}/100</b> ({patient.biomarkers?.apoe4} APOE4 allele).</p>
              <p><b>RECOMMENDATION:</b> {patient.cdsRecommendation}</p>
            </div>
          </div>

          <button
            onClick={handleCopyNote}
            className="aws-btn-secondary w-full mt-4 py-2.5 rounded-md text-xs font-bold flex items-center justify-center gap-2 shadow-xs"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-[#067D62]" />
                <span className="text-[#067D62]">Copied to EHR Clipboard!</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 text-[#565959]" />
                <span>Copy Clinical Note to Clipboard</span>
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  )
}
