import type { Ticket } from '../types/ticket'
import { Clock, CheckCircle2 } from 'lucide-react'

interface TicketCardProps {
  ticket: Ticket
}

export function TicketCard({ ticket }: TicketCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('es-CO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getSentimentBorderColor = (sentiment: string | null) => {
    if (!sentiment) return 'border-l-gray-400'
    const colors = {
      'Positivo': 'border-l-green-500',
      'Neutral': 'border-l-gray-400',
      'Negativo': 'border-l-red-500'
    }
    return colors[sentiment as keyof typeof colors] || 'border-l-gray-400'
  }

  const getSentimentTitleColor = (sentiment: string | null) => {
    if (!sentiment) return 'text-gray-900'
    const colors = {
      'Positivo': 'text-green-700',
      'Neutral': 'text-gray-700',
      'Negativo': 'text-red-700'
    }
    return colors[sentiment as keyof typeof colors] || 'text-gray-900'
  }

  const getCategoryStyle = (category: string | null) => {
    if (!category) return 'bg-gray-100 text-gray-700'
    const styles = {
      'Técnico': 'bg-blue-100 text-blue-700',
      'Facturación': 'bg-amber-100 text-amber-700',
      'Comercial': 'bg-purple-100 text-purple-700',
      'Otro': 'bg-gray-100 text-gray-700'
    }
    return styles[category as keyof typeof styles] || styles['Otro']
  }

  const getSentimentBadgeStyle = (sentiment: string | null) => {
    if (!sentiment) return 'bg-gray-100 text-gray-700'
    const styles = {
      'Positivo': 'bg-green-100 text-green-700',
      'Neutral': 'bg-gray-100 text-gray-700',
      'Negativo': 'bg-red-100 text-red-700'
    }
    return styles[sentiment as keyof typeof styles] || styles['Neutral']
  }

  return (
    <div 
      className={`
        w-full sm:w-[calc(50%-12px)] lg:w-[calc(33.333%-16px)] xl:w-[calc(25%-18px)]
        min-w-[280px] max-w-[400px]
        bg-white rounded-xl p-5 
        shadow-md hover:shadow-2xl 
        transition-all duration-300 
        border-l-4 ${getSentimentBorderColor(ticket.sentiment)}
        hover:-translate-y-1
      `}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Clock className="w-3.5 h-3.5" />
          <span>{formatDate(ticket.created_at)}</span>
        </div>
        {ticket.processed && (
          <div className="flex items-center gap-1 text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
            <CheckCircle2 className="w-3 h-3" />
            <span>Procesado</span>
          </div>
        )}
      </div>

      <h3 className={`text-base font-semibold mb-3 line-clamp-2 ${getSentimentTitleColor(ticket.sentiment)}`}>
        {ticket.description.substring(0, 80)}{ticket.description.length > 80 ? '...' : ''}
      </h3>

      <p className="text-sm text-gray-600 mb-4 line-clamp-3 leading-relaxed">
        {ticket.description}
      </p>

      <div className="flex flex-wrap gap-2">
        {ticket.category && (
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${getCategoryStyle(ticket.category)}`}>
            {ticket.category}
          </span>
        )}
        {ticket.sentiment && (
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${getSentimentBadgeStyle(ticket.sentiment)}`}>
            {ticket.sentiment}
          </span>
        )}
      </div>
    </div>
  )
}
