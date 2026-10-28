import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Smriti | Brain Health & Connected Care',
  description: 'Explore Smriti, a brain health platform for Alzheimer’s care pathways, brain tumor detection, and connected telemedicine consultations.',
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
