'use client'

import React from 'react'
import { 
  Users, 
  Layers, 
  Eye, 
  BarChart3, 
  ShieldCheck, 
  Calculator, 
  SlidersHorizontal 
} from 'lucide-react'

interface SubNavbarProps {
  activeTab: string
  setActiveTab: (t: string) => void
  patientCount: number
  selectedStage?: number
}

export default function SubNavbar({
  activeTab,
  setActiveTab,
  patientCount,
  selectedStage = 1
}: SubNavbarProps) {
  const tabs = [
    { id: 'triage', label: 'Triage Worklist', icon: Users, badge: `${patientCount}` },
    { id: 'dossier', label: '4-Stage Patient Dossier', icon: Layers, badge: `Stage ${selectedStage}` },
    { id: 'vision', label: 'Scan-to-Volume Vision AI', icon: Eye, badge: 'ResNet' },
    { id: 'explain', label: 'TreeSHAP & CDS Notes', icon: BarChart3, badge: 'Dual-Head' },
    { id: 'aria', label: 'ARIA Safety & DMT Protocol', icon: ShieldCheck, badge: 'FHIR R4' },
    { id: 'roi', label: 'Hospital ROI Sandbox', icon: Calculator, badge: 'Economics' },
    { id: 'dynamic_lab', label: 'Dynamic Diagnostic Lab', icon: SlidersHorizontal, badge: 'NaN' }
  ]

  return (
    <div className="bg-[#232F3E] text-white border-b border-[#37475A] px-4 select-none sticky top-14 z-40">
      <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition ${
                isActive 
                  ? 'border-[#FF9900] text-white bg-[#37475A]/60' 
                  : 'border-transparent text-[#D5DBDB] hover:text-white hover:bg-[#37475A]/30'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#FF9900]' : 'text-[#A6B0B0]'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                  isActive ? 'bg-[#FF9900] text-[#0F1111] font-bold' : 'bg-[#131921] text-[#A6B0B0] border border-[#37475A]'
                }`}>
                  {tab.badge}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
