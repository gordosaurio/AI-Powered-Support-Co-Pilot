export type TicketCategory = 'Técnico' | 'Facturación' | 'Comercial' | 'Otro'
export type TicketSentiment = 'Positivo' | 'Neutral' | 'Negativo'

export interface Ticket {
  id: string
  created_at: string
  description: string
  category: TicketCategory | null
  sentiment: TicketSentiment | null
  processed: boolean
}
