'use client'

import React from 'react'
import { Calculator, DollarSign, Clock, Users, ArrowDownRight } from 'lucide-react'

interface RoiSimulatorProps {
  simData: any
  setSimData: (d: any) => void
  simResults: any
  onRecalculate: () => void
}

export default function RoiSimulator({
  simData,
  setSimData,
  simResults,
  onRecalculate
}: RoiSimulatorProps) {
  return (
    <div className="space-y-6">
      
      {/* AWS Calculator Style Header */}
      <div className="aws-card p-6 bg-white">
        <div className="pb-4 border-b border-[#EAEDED] mb-6">
          <h3 className="text-base font-extrabold text-[#0F1111] flex items-center gap-2">
            <Calculator className="w-5 h-5 text-[#007185]" />
            Hospital Economic ROI & Diagnostic Scanner Capacity Sandbox
          </h3>
          <p className="text-xs text-[#565959] mt-0.5">
            Simulate operational wait-time reduction, scanner capacity unlocks, and annual cost savings when replacing traditional direct referrals with StepWise staged gating
          </p>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6">
          
          <div className="space-y-2">
            <label className="text-xs font-bold text-[#0F1111] flex justify-between">
              <span>Annual Cognitive Complaints:</span>
              <span className="font-mono text-[#007185] font-extrabold">{simData.annual_screened_patients}</span>
            </label>
            <input
              type="range"
              min="1000"
              max="15000"
              step="500"
              value={simData.annual_screened_patients}
              onChange={(e) => {
                setSimData({ ...simData, annual_screened_patients: Number(e.target.value) })
                onRecalculate()
              }}
              className="w-full accent-[#FF9900]"
            />
            <div className="text-[10px] text-[#565959] flex justify-between">
              <span>1,000</span>
              <span>15,000</span>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-[#0F1111] flex justify-between">
              <span>Weekly Brain MRI Slots:</span>
              <span className="font-mono text-[#007185] font-extrabold">{simData.mri_weekly_capacity}</span>
            </label>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={simData.mri_weekly_capacity}
              onChange={(e) => {
                setSimData({ ...simData, mri_weekly_capacity: Number(e.target.value) })
                onRecalculate()
              }}
              className="w-full accent-[#FF9900]"
            />
            <div className="text-[10px] text-[#565959] flex justify-between">
              <span>10 slots/wk</span>
              <span>100 slots/wk</span>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-[#0F1111] flex justify-between">
              <span>Weekly Amyloid PET Slots:</span>
              <span className="font-mono text-[#007185] font-extrabold">{simData.pet_weekly_capacity}</span>
            </label>
            <input
              type="range"
              min="5"
              max="40"
              step="1"
              value={simData.pet_weekly_capacity}
              onChange={(e) => {
                setSimData({ ...simData, pet_weekly_capacity: Number(e.target.value) })
                onRecalculate()
              }}
              className="w-full accent-[#FF9900]"
            />
            <div className="text-[10px] text-[#565959] flex justify-between">
              <span>5 slots/wk</span>
              <span>40 slots/wk</span>
            </div>
          </div>

        </div>

        {/* Results Banner - Amazon/AWS Style Key Metric Cards */}
        {simResults && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-[#EAEDED]">
            
            <div className="p-4 bg-[#ECFDF5] border border-[#A7F3D0] rounded-md">
              <div className="text-[11px] font-bold text-[#067D62] uppercase tracking-wider">Annual Cost Savings</div>
              <div className="text-3xl font-extrabold text-[#067D62] font-mono mt-1">
                ${(simResults.roi_impact?.total_annual_savings_usd / 1000000).toFixed(2)}M
              </div>
              <div className="text-[11px] text-[#067D62] font-semibold mt-1">
                {simResults.roi_impact?.savings_percentage}% Diagnostic Cost Reduction
              </div>
            </div>

            <div className="p-4 bg-[#F0F9FF] border border-[#BAE6FD] rounded-md">
              <div className="text-[11px] font-bold text-[#0369A1] uppercase tracking-wider">MRI Capacity Unlocked</div>
              <div className="text-3xl font-extrabold text-[#0369A1] font-mono mt-1">
                {simResults.roi_impact?.mri_capacity_unlocked_pct}%
              </div>
              <div className="text-[11px] text-[#565959] mt-1 font-medium">
                {simResults.traditional_pathway?.mri_scans_ordered - simResults.stepwise_pathway?.mri_scans_ordered} Scans Filtered
              </div>
            </div>

            <div className="p-4 bg-[#F0F9FF] border border-[#BAE6FD] rounded-md">
              <div className="text-[11px] font-bold text-[#0369A1] uppercase tracking-wider">Unnecessary PET Saved</div>
              <div className="text-3xl font-extrabold text-[#0369A1] font-mono mt-1">
                {simResults.roi_impact?.pet_unnecessary_scan_reduction_pct}%
              </div>
              <div className="text-[11px] text-[#565959] mt-1 font-medium">
                {simResults.traditional_pathway?.pet_scans_ordered - simResults.stepwise_pathway?.pet_scans_ordered} PET Scans Spared
              </div>
            </div>

            <div className="p-4 bg-[#FAF5FF] border border-[#E9D5FF] rounded-md">
              <div className="text-[11px] font-bold text-[#6B21A8] uppercase tracking-wider">Wait Time Reduction</div>
              <div className="text-3xl font-extrabold text-[#6B21A8] font-mono mt-1">
                {simResults.roi_impact?.wait_time_reduction_months} Mo
              </div>
              <div className="text-[11px] text-[#565959] mt-1 font-medium">
                Faster Treatment Initiation
              </div>
            </div>

          </div>
        )}
      </div>

    </div>
  )
}
