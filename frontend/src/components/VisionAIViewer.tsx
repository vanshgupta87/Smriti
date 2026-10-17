'use client'

import React from 'react'
import { Eye, Layers, CheckCircle2, AlertCircle, ArrowRight } from 'lucide-react'

interface VisionAIViewerProps {
  mriPreset: string
  mriResult: any
  onSelectMriPreset: (preset: string) => void
  petPreset: string
  petResult: any
  onSelectPetPreset: (preset: string) => void
  onAutoPopulate: () => void
}

export default function VisionAIViewer({
  mriPreset,
  mriResult,
  onSelectMriPreset,
  petPreset,
  petResult,
  onAutoPopulate
}: VisionAIViewerProps) {
  return (
    <div className="space-y-6">
      
      {/* Top Banner - AWS SageMaker / Cloud AI Style */}
      <div className="aws-card p-6 bg-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#EAEDED]">
          <div>
            <h3 className="text-base font-extrabold text-[#0F1111] flex items-center gap-2">
              <Eye className="w-5 h-5 text-[#007185]" />
              Hybrid Deep Learning Scan-to-Volume Vision Engine
            </h3>
            <p className="text-xs text-[#565959] mt-0.5">
              Direct volumetric extraction from sagittal T1 MRI DICOM slices & 3D Amyloid PET tracer scans
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#565959]">Scan Preset:</span>
            {[
              { id: 'normal_case', label: '1. Normal Control' },
              { id: 'mci_case', label: '2. MCI Transition' },
              { id: 'ad_case', label: '3. Severe AD Dementia' }
            ].map((c) => (
              <button
                key={c.id}
                onClick={() => onSelectMriPreset(c.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-bold transition ${
                  mriPreset === c.id
                    ? 'aws-btn-primary shadow-xs'
                    : 'aws-btn-secondary hover:bg-[#F7FAFA]'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </div>

        {/* MRI Scan Visualization & Quantitative Volumes */}
        {mriResult && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-5">
            
            {/* Visual Canvas with Bounding Box Overlay */}
            <div className="col-span-1 bg-[#131921] p-5 rounded-lg text-white flex flex-col items-center justify-center relative shadow-sm">
              <div className="text-[11px] font-mono text-[#A6B0B0] mb-2 uppercase tracking-wider">
                Subject Central Slice (Sagittal T1)
              </div>

              <div className="w-56 h-56 bg-[#232F3E] border-2 border-[#37475A] rounded-md relative overflow-hidden flex items-center justify-center">
                {/* Brain Graphic Simulation */}
                <div className="text-7xl opacity-80 select-none">🧠</div>
                
                {/* Yellow Bounding Box Overlay (Matching Yatharth's Output) */}
                <div className="absolute inset-x-6 inset-y-6 border-2 border-[#FFD814] bg-[#007185]/20 rounded flex items-start justify-end p-1">
                  <span className="text-[9px] bg-[#FFD814] text-[#0F1111] font-bold px-1.5 py-0.5 rounded shadow-xs">
                    ROI: Medial Temporal
                  </span>
                </div>
              </div>

              <div className="mt-3 text-center">
                <div className="text-xs font-bold text-white">
                  Predicted: <span className="text-[#FF9900]">{mriResult.vision_classification?.predicted_class}</span>
                </div>
                <div className="text-[11px] text-[#A6B0B0] font-mono">
                  Confidence: <b>{(mriResult.vision_classification?.model_confidence * 100).toFixed(1)}%</b>
                </div>
              </div>
            </div>

            {/* Extracted Quantitative Volumetric Features */}
            <div className="col-span-2 space-y-4">
              <div className="text-xs font-bold text-[#565959] uppercase tracking-wider">
                Vision-Extracted Anatomical Metrics (cm³)
              </div>

              <div className="grid grid-cols-3 gap-3">
                
                <div className="p-3.5 bg-[#F7FAFA] rounded-md border border-[#D5DBDB]">
                  <div className="text-[11px] font-bold text-[#565959]">Hippocampal Volume</div>
                  <div className="text-2xl font-extrabold text-[#0F1111] font-mono mt-0.5">
                    {mriResult.predicted_volumes?.hippocampus_cm3} <span className="text-xs font-normal text-[#565959]">cm³</span>
                  </div>
                  <div className="text-[10px] text-[#565959] mt-0.5 font-medium">Norm: 7.2 - 8.0 cm³</div>
                </div>

                <div className="p-3.5 bg-[#F7FAFA] rounded-md border border-[#D5DBDB]">
                  <div className="text-[11px] font-bold text-[#565959]">Lateral Ventricles</div>
                  <div className="text-2xl font-extrabold text-[#0F1111] font-mono mt-0.5">
                    {mriResult.predicted_volumes?.ventricles_cm3} <span className="text-xs font-normal text-[#565959]">cm³</span>
                  </div>
                  <div className="text-[10px] text-[#565959] mt-0.5 font-medium">CSF Enlargement Index</div>
                </div>

                <div className="p-3.5 bg-[#F7FAFA] rounded-md border border-[#D5DBDB]">
                  <div className="text-[11px] font-bold text-[#565959]">HVR Ratio (Hippo/Ventricles)</div>
                  <div className="text-2xl font-extrabold text-[#007185] font-mono mt-0.5">
                    {mriResult.predicted_volumes?.hvr_ratio}
                  </div>
                  <div className="text-[10px] text-[#565959] mt-0.5 font-medium">&lt; 0.25 Indicates Atrophy</div>
                </div>

              </div>

              {/* Auto-Populate Action */}
              <div className="p-4 bg-[#F0F9FF] border border-[#BAE6FD] rounded-md flex items-center justify-between">
                <div>
                  <div className="text-xs font-extrabold text-[#0369A1] flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#007185]" />
                    Auto-Derived Hippocampal/ICV Ratio: {mriResult.predicted_volumes?.hippocampus_icv_ratio}
                  </div>
                  <p className="text-[11px] text-[#565959] mt-0.5 font-medium">
                    Automated injection eliminates manual radiologist data entry in Stage 3.
                  </p>
                </div>

                <button
                  onClick={onAutoPopulate}
                  className="aws-btn-primary px-4 py-2 rounded-md text-xs font-bold shadow-xs flex items-center gap-1.5 shrink-0"
                >
                  Auto-Populate Stage 3 Vector <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

            </div>

          </div>
        )}
      </div>

    </div>
  )
}
