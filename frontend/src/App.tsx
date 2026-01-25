import { useState } from 'react'
import { Plus } from 'lucide-react'
import { TicketList } from './components/TicketList'
import { CreateTicketModal } from './components/CreateTicketModal'
import { useTickets } from './hooks/useTickets'

function App() {
  const { tickets, loading, error, refetch } = useTickets()
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleSuccess = () => {
    refetch()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-slate-50/30 to-white/50 pointer-events-none" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        
        <header className="text-center mb-16 sm:mb-20">
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 mb-6 tracking-tight">
            Sistema de <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-600 via-emerald-500 to-lime-500">Tickets</span>
          </h1>
          <p className="text-xl sm:text-2xl text-slate-600 font-light max-w-3xl mx-auto leading-relaxed">
            Gestión inteligente de soporte con IA
          </p>
        </header>

        <div className="flex justify-center mb-16">
          <button 
            onClick={() => setIsModalOpen(true)}
            className="group bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white font-semibold py-4 px-10 rounded-2xl transition-all duration-300 flex items-center gap-3 shadow-xl hover:shadow-2xl hover:scale-105 transform"
          >
            <Plus className="w-6 h-6 group-hover:rotate-90 transition-transform duration-300" strokeWidth={2.5} />
            <span className="text-lg">Crear Ticket</span>
          </button>
        </div>

        <TicketList tickets={tickets} loading={loading} error={error} />
      </div>

      <CreateTicketModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleSuccess}
      />
    </div>
  )
}

export default App
