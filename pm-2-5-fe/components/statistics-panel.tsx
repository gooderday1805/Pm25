"use client"

import { Card } from "@/components/ui/card"
import type { PredictionData } from "./dashboard"
import { TrendingUp, Users, Target, CheckCircle } from "lucide-react"

interface StatisticsPanelProps {
  data: PredictionData
}

function getAQIColor(value: number): string {
  if (value <= 12) return "text-green-400"
  if (value <= 35) return "text-yellow-400"
  if (value <= 55) return "text-orange-400"
  if (value <= 150) return "text-red-400"
  return "text-purple-400"
}

function getAQIBg(value: number): string {
  if (value <= 12) return "bg-green-500/10"
  if (value <= 35) return "bg-yellow-500/10"
  if (value <= 55) return "bg-orange-500/10"
  if (value <= 150) return "bg-red-500/10"
  return "bg-purple-500/10"
}

export default function StatisticsPanel({ data }: StatisticsPanelProps) {
  const stats = [
    {
      title: "Trung Bình TP",
      value: data.statistics.city_average.toFixed(1),
      unit: "μg/m³",
      icon: Target,
      color: getAQIColor(data.statistics.city_average),
      bg: getAQIBg(data.statistics.city_average),
    },
    {
      title: "Cao Nhất",
      value: data.statistics.city_max.toFixed(1),
      unit: "μg/m³",
      icon: TrendingUp,
      color: getAQIColor(data.statistics.city_max),
      bg: getAQIBg(data.statistics.city_max),
    },
    {
      title: "Thấp Nhất",
      value: data.statistics.city_min.toFixed(1),
      unit: "μg/m³",
      icon: Users,
      color: getAQIColor(data.statistics.city_min),
      bg: getAQIBg(data.statistics.city_min),
    },
    {
      title: "Trên Chuẩn WHO",
      value: `${data.statistics.who_standard_15.above}/24`,
      unit: "quận",
      icon: CheckCircle,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, idx) => {
        const Icon = stat.icon
        return (
          <Card key={idx} className={`border-slate-700 ${stat.bg} p-4`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-400 mb-1">{stat.title}</p>
                <div className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}
                  <span className="text-xs ml-1 opacity-75">{stat.unit}</span>
                </div>
              </div>
              <Icon className={`h-6 w-6 ${stat.color} opacity-50`} />
            </div>
          </Card>
        )
      })}
    </div>
  )
}
