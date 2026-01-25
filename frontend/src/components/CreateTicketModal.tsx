import { useState } from 'react'
import { X, AlertCircle, CheckCircle2 } from 'lucide-react'

interface CreateTicketModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

const MIN_CHARACTERS = 30

export function CreateTicketModal({ isOpen, onClose, onSuccess }: CreateTicketModalProps) {
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showLengthWarning, setShowLengthWarning] = useState(false)

  if (!isOpen) return null

  const isValidLength = description.length >= MIN_CHARACTERS
  const remainingChars = MIN_CHARACTERS - description.length

  const handleSubmit = async () => {
    if (!isValidLength) {
      setShowLengthWarning(true)
      setTimeout(() => setShowLengthWarning(false), 3000)
      return
    }

    setIsSubmitting(true)
    
    try {
      const response = await fetch('https://ai-powered-support-co-pilot-production-c917.up.railway.app/create_ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description }),
      })

      if (!response.ok) {
        throw new Error('Error al crear el ticket')
      }

      // Limpiar y cerrar
      setDescription('')
      onSuccess()
      onClose()
    } catch (error) {
      console.error('Error:', error)
      alert('Hubo un error al crear el ticket. Por favor, inténtalo nuevamente.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setDescription('')
      setShowLengthWarning(false)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="relative bg-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        
        <div className="sticky top-0 bg-white border-b border-slate-200 px-8 py-6 rounded-t-3xl flex items-center justify-between">
          <h2 className="text-3xl font-bold text-slate-900">Crear Nuevo Ticket</h2>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-slate-600 transition-colors disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="px-8 py-6">
          <p className="text-slate-600 text-lg mb-6 leading-relaxed">
            Describe tu consulta o problema de manera detallada para que nuestro equipo pueda brindarte la mejor asistencia posible.
          </p>

          <div className="mb-4">
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ejemplo: Tengo problemas para acceder a mi cuenta desde ayer. He intentado recuperar mi contraseña pero no recibo el correo de restablecimiento..."
              className="w-full h-48 px-4 py-3 text-slate-900 bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-none transition-all"
              disabled={isSubmitting}
            />
            
            <div className="flex items-center justify-between mt-2">
              <span className={`text-sm font-medium ${isValidLength ? 'text-emerald-600' : 'text-slate-500'}`}>
                {description.length} caracteres
              </span>
              
              {!isValidLength && description.length > 0 && (
                <span className="text-sm text-amber-600 font-medium">
                  Faltan {remainingChars} caracteres
                </span>
              )}
              
              {isValidLength && (
                <div className="flex items-center gap-1.5 text-emerald-600">
                  <CheckCircle2 className="w-4 h-4" />
                  <span className="text-sm font-semibold">Listo para enviar</span>
                </div>
              )}
            </div>
          </div>

          {showLengthWarning && (
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-3 animate-shake">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-amber-800 font-semibold">Descripción muy corta</p>
                <p className="text-amber-700 text-sm">
                  Por favor, proporciona al menos {MIN_CHARACTERS} caracteres para crear el ticket. Te faltan {remainingChars} caracteres más.
                </p>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1 px-6 py-3 text-slate-700 bg-slate-100 hover:bg-slate-200 font-semibold rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className={`flex-1 px-6 py-3 font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 ${
                isValidLength
                  ? 'bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-700 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl hover:scale-105'
                  : 'bg-slate-300 text-slate-500 cursor-not-allowed'
              }`}
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creando...
                </>
              ) : (
                'Crear Ticket'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
