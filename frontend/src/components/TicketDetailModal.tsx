import { X, Clock, Tag, Heart } from 'lucide-react'
import type { Ticket } from '../types/ticket'

interface TicketDetailModalProps {
    ticket: Ticket | null
    isOpen: boolean
    onClose: () => void
}

export function TicketDetailModal({ ticket, isOpen, onClose }: TicketDetailModalProps) {
    if (!isOpen || !ticket) return null

    const getSentimentColor = (sentiment: string | null) => {
        if (!sentiment) return 'bg-gray-100 text-gray-600'
        const s = sentiment.toLowerCase()
        if (s.includes('positivo')) return 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700'
        if (s.includes('negativo')) return 'bg-gradient-to-r from-red-100 to-pink-100 text-red-700'
        return 'bg-gradient-to-r from-gray-100 to-slate-100 text-gray-700'
    }

    const getCategoryColor = (category: string | null) => {
        if (!category) return 'bg-gray-100 text-gray-600'
        const c = category.toLowerCase()
        if (c.includes('técnico')) return 'bg-blue-100 text-blue-700'
        if (c.includes('facturación')) return 'bg-purple-100 text-purple-700'
        if (c.includes('comercial')) return 'bg-orange-100 text-orange-700'
        return 'bg-gray-100 text-gray-700'
    }

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto" onClick={onClose}>
            <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
                <div className="fixed inset-0 transition-opacity bg-gray-900/75" />

                <div 
                    className="relative inline-block w-full max-w-3xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-2xl rounded-3xl"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="relative bg-gradient-to-r from-teal-600 to-emerald-600 px-8 py-6">
                        <button
                            onClick={onClose}
                            className="absolute top-4 right-4 p-2 text-white hover:bg-white/20 rounded-full transition-colors"
                        >
                            <X className="w-6 h-6" />
                        </button>
                        <h2 className="text-2xl font-bold text-white pr-12">Detalle del Ticket</h2>
                    </div>

                    <div className="px-8 py-6 space-y-6">
                        <div className="flex flex-wrap items-center gap-4 pb-6 border-b border-gray-200">
                            <div className="flex items-center gap-2 text-gray-600">
                                <Clock className="w-5 h-5" />
                                <span className="text-sm">
                                    {new Date(ticket.created_at).toLocaleString('es-ES', {
                                        dateStyle: 'medium',
                                        timeStyle: 'short'
                                    })}
                                </span>
                            </div>

                            {ticket.processed && (
                                <span className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-green-700 bg-green-100 rounded-full">
                                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                                    Procesado
                                </span>
                            )}
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-gray-900 mb-3">Descripción</h3>
                            <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                    {ticket.description}
                                </p>
                            </div>
                        </div>

                        {ticket.processed && (ticket.category || ticket.sentiment) && (
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-3">Clasificación IA</h3>
                                <div className="flex flex-wrap gap-3">
                                    {ticket.category && (
                                        <div className="flex items-center gap-2">
                                            <Tag className="w-5 h-5 text-gray-500" />
                                            <span className={`px-4 py-2 rounded-xl font-medium ${getCategoryColor(ticket.category)}`}>
                                                {ticket.category}
                                            </span>
                                        </div>
                                    )}
                                    
                                    {ticket.sentiment && (
                                        <div className="flex items-center gap-2">
                                            <Heart className="w-5 h-5 text-gray-500" />
                                            <span className={`px-4 py-2 rounded-xl font-medium ${getSentimentColor(ticket.sentiment)}`}>
                                                {ticket.sentiment}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="pt-4 border-t border-gray-200">
                            <p className="text-xs text-gray-500">
                                <span className="font-medium">ID:</span> {ticket.id}
                            </p>
                        </div>
                    </div>

                    <div className="px-8 py-4 bg-gray-50 border-t border-gray-200">
                        <button
                            onClick={onClose}
                            className="w-full px-6 py-3 bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-semibold rounded-xl transition-all duration-300 shadow-md hover:shadow-lg"
                        >
                            Cerrar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}
