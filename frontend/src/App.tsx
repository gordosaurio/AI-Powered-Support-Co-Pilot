import { Plus } from 'lucide-react'
import { TicketList } from './components/TicketList'
import { useTickets } from './hooks/useTickets'

function App() {
  const { tickets, loading, error } = useTickets()

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-blue-50">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        <header className="text-center mb-12">
          <h1 className="text-center text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-3">
            Sistema de Tickets
          </h1>
          <p className="text-lg text-gray-600">
            Gestión inteligente de soporte con IA
          </p>
        </header>

        <div className="flex justify-center mb-12">
          <button className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium py-4 px-8 rounded-xl transition-all duration-200 flex items-center gap-3 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:-translate-y-0.5">
            <Plus className="w-5 h-5" strokeWidth={2.5} />
            <span>Crear Ticket</span>
          </button>
        </div>

        <TicketList tickets={tickets} loading={loading} error={error} />
      </div>
    </div>
  )
}

export default App
