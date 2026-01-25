import { useState } from 'react'
import { X, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react'

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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gradient-to-br from-slate-900/60 via-slate-800/50 to-slate-900/60 backdrop-blur-md animate-fadeIn">
        <div className="relative bg-gradient-to-br from-white via-slate-50 to-white rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden border border-slate-200/50">
            
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-emerald-500 to-lime-500" />
            
            <div className="relative bg-gradient-to-br from-slate-50 to-white border-b border-slate-200/80 px-8 py-8">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-br from-teal-100 to-emerald-100 rounded-xl">
                    <Sparkles className="w-6 h-6 text-teal-600" />
                </div>
                <div>
                    <h2 className="text-3xl font-bold text-slate-900">Crear Nuevo Ticket</h2>
                    <p className="text-sm text-slate-500 mt-1">Comparte tu consulta con nuestro equipo</p>
                </div>
                </div>
                <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all duration-200 disabled:opacity-50"
                >
                <X className="w-6 h-6" />
                </button>
            </div>
            </div>

            <div className="px-8 py-6 max-h-[calc(90vh-180px)] overflow-y-auto">
            <div className="mb-6 p-5 bg-gradient-to-br from-teal-50 to-emerald-50 rounded-2xl border border-teal-100/50">
                <p className="text-slate-700 text-base leading-relaxed">
                <span className="font-semibold text-teal-700">💡 Consejo:</span> Describe tu consulta o problema de manera detallada para que nuestro equipo pueda brindarte la mejor asistencia posible.
                </p>
            </div>

            <div className="mb-4">
                <div className="relative">
                <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Ejemplo: Tengo problemas para acceder a mi cuenta desde ayer. He intentado recuperar mi contraseña pero no recibo el correo de restablecimiento..."
                    className="w-full h-56 px-5 py-4 text-slate-900 bg-white border-2 border-slate-200 rounded-2xl focus:outline-none focus:ring-4 focus:ring-teal-500/20 focus:border-teal-500 resize-none transition-all duration-300 shadow-sm hover:shadow-md placeholder:text-slate-400"
                    disabled={isSubmitting}
                />
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-teal-500/5 to-emerald-500/5 pointer-events-none opacity-0 group-focus-within:opacity-100 transition-opacity" />
                </div>
                
                <div className="flex items-center justify-between mt-3 px-2">
                <div className="flex items-center gap-2">
                    <div className={`h-2 w-32 bg-slate-200 rounded-full overflow-hidden ${description.length > 0 ? 'block' : 'hidden'}`}>
                    <div 
                        className={`h-full transition-all duration-300 ${isValidLength ? 'bg-gradient-to-r from-emerald-500 to-teal-500' : 'bg-gradient-to-r from-amber-400 to-orange-400'}`}
                        style={{ width: `${Math.min((description.length / MIN_CHARACTERS) * 100, 100)}%` }}
                    />
                    </div>
                    <span className={`text-sm font-semibold ${isValidLength ? 'text-emerald-600' : 'text-slate-500'}`}>
                    {description.length} / {MIN_CHARACTERS}
                    </span>
                </div>
                
                {!isValidLength && description.length > 0 && (
                    <span className="text-sm text-amber-600 font-medium bg-amber-50 px-3 py-1 rounded-full">
                    Faltan {remainingChars}
                    </span>
                )}
                
                {isValidLength && (
                    <div className="flex items-center gap-2 text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="text-sm font-semibold">Listo para enviar</span>
                    </div>
                )}
                </div>
            </div>

            {showLengthWarning && (
                <div className="mb-4 p-5 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-2xl flex items-start gap-4 animate-shake shadow-lg">
                <div className="p-2 bg-amber-100 rounded-xl">
                    <AlertCircle className="w-5 h-5 text-amber-700" />
                </div>
                <div>
                    <p className="text-amber-900 font-bold text-base">Descripción muy corta</p>
                    <p className="text-amber-800 text-sm mt-1 leading-relaxed">
                    Por favor, proporciona al menos <span className="font-semibold">{MIN_CHARACTERS} caracteres</span> para crear el ticket. Te faltan <span className="font-semibold">{remainingChars} caracteres</span> más.
                    </p>
                </div>
                </div>
            )}
            </div>

            <div className="px-8 py-6 bg-gradient-to-br from-slate-50 to-white border-t border-slate-200/80">
            <div className="flex gap-4">
                <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="flex-1 px-6 py-4 text-slate-700 bg-white hover:bg-slate-50 font-semibold rounded-2xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-slate-200 hover:border-slate-300 shadow-sm hover:shadow-md"
                >
                Cancelar
                </button>
                <button
                onClick={handleSubmit}
                disabled={isSubmitting || !isValidLength}
                className={`flex-1 px-6 py-4 font-bold rounded-2xl transition-all duration-300 flex items-center justify-center gap-3 shadow-lg ${
                    isValidLength && !isSubmitting
                    ? 'bg-gradient-to-r from-teal-600 via-emerald-600 to-teal-600 bg-size-200 bg-pos-0 hover:bg-pos-100 text-white hover:shadow-2xl hover:scale-[1.02] active:scale-[0.98]'
                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                }`}
                >
                {isSubmitting ? (
                    <>
                    <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Creando ticket...</span>
                    </>
                ) : (
                    <>
                    <Sparkles className="w-5 h-5" />
                    <span>Crear Ticket</span>
                    </>
                )}
                </button>
            </div>
            </div>
        </div>
        </div>
    )
}
