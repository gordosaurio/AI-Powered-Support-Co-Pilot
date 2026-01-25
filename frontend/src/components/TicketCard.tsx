import { Clock, CheckCircle2 } from 'lucide-react'
import type { Ticket } from '../types/ticket'

interface TicketCardProps {
  ticket: Ticket
}

const getSentimentColor = (sentiment: string | null) => {
  if (!sentiment) return 'border-l-slate-400'
  const s = sentiment.toLowerCase()
  if (s.includes('positivo')) return 'border-l-emerald-500'
  if (s.includes('negativo')) return 'border-l-rose-500'
  return 'border-l-slate-400'
}

const getCategoryColor = (category: string | null) => {
  if (!category) return 'bg-slate-100 text-slate-700 ring-slate-600/20'
  const c = category.toLowerCase()
  if (c.includes('técnico')) return 'bg-blue-100 text-blue-700 ring-blue-600/20'
  if (c.includes('facturación')) return 'bg-purple-100 text-purple-700 ring-purple-600/20'
  if (c.includes('comercial')) return 'bg-amber-100 text-amber-700 ring-amber-600/20'
  return 'bg-slate-100 text-slate-700 ring-slate-600/20'
}

const getSentimentBadgeColor = (sentiment: string | null) => {
  if (!sentiment) return 'bg-slate-100 text-slate-700 ring-slate-600/20'
  const s = sentiment.toLowerCase()
  if (s.includes('positivo')) return 'bg-emerald-100 text-emerald-700 ring-emerald-600/20'
  if (s.includes('negativo')) return 'bg-rose-100 text-rose-700 ring-rose-600/20'
  return 'bg-slate-100 text-slate-700 ring-slate-600/20'
}

export function TicketCard({ ticket }: TicketCardProps) {
  const borderColor = getSentimentColor(ticket.sentiment)
  const categoryColor = getCategoryColor(ticket.category)
  const sentimentColor = getSentimentBadgeColor(ticket.sentiment)

  return (
    <div className={`group bg-white rounded-2xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden border-l-4 ${borderColor} hover:-translate-y-1`}>
      <div className="p-6 sm:p-8">
        
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-slate-500">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">
              {new Date(ticket.created_at).toLocaleDateString('es-ES', {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
          
          {ticket.processed && (
            <div className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full">
              <CheckCircle2 className="w-4 h-4" />
              <span className="text-sm font-semibold">Procesado</span>
            </div>
          )}
        </div>

        <h3 className="text-xl font-bold text-slate-900 mb-3 line-clamp-2 group-hover:text-teal-600 transition-colors">
          {ticket.description.split('\n')[0].substring(0, 80)}
          {ticket.description.length > 80 ? '...' : ''}
        </h3>

        <p className="text-slate-600 mb-6 line-clamp-3 text-sm leading-relaxed">
          {ticket.description}
        </p>

        <div className="flex flex-wrap gap-2">
          {ticket.category && (
            <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ring-1 ring-inset ${categoryColor} transition-all`}>
              {ticket.category}
            </span>
          )}
          {ticket.sentiment && (
            <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold ring-1 ring-inset ${sentimentColor} transition-all`}>
              {ticket.sentiment}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
