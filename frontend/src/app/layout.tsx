import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GE Healthcare StepWise | Precision Care Clinical Command Center',
  description: 'AI-Driven 4-Stage Clinical Decision Support Prioritization Platform for Early Alzheimer Diagnostic Pathways',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#EAEDED] text-[#0F1111] antialiased">
        {children}
      </body>
    </html>
  )
}
