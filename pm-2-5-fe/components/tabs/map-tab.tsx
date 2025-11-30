"use client"
import { Card } from "@/components/ui/card"
import { AlertCircle, Loader2 } from "lucide-react"
import dynamic from "next/dynamic"
import type { PredictionData } from "../dashboard"

const MapComponent = dynamic(() => import("../map-component"), {
  ssr: false,
  loading: () => (
    <div className="h-96 flex items-center justify-center rounded-lg bg-slate-800/50 border border-slate-700">
      <Loader2 className="h-6 w-6 text-blue-400 animate-spin" />
    </div>
  ),
})

interface MapTabProps {
  data: PredictionData | null
}

export default function MapTab({ data }: MapTabProps) {
  if (!data) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-12 text-center">
        <AlertCircle className="mx-auto h-12 w-12 text-slate-400 mb-3" />
        <p className="text-slate-400">Vui lòng dự đoán ở Tab 1 trước để xem bản đồ</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Card className="border-slate-700 bg-slate-800/50 p-4">
        <MapComponent data={data} />
      </Card>
    </div>
  )
}
