import { useEffect, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { sendChat, fetchHistory, formatPrice, type Product } from '../api'
import { useAuth } from '../auth'
import { useSearchResults } from '../searchResults'

type Message = { role: 'user' | 'assistant'; text: string; products?: Product[] }

const GREETING: Message = { role: 'assistant', text: 'Hi! Ask me about Campus Customs merch.' }

// One-tap starter questions (front-end usability improvement).
const QUICK_QUESTIONS = [
  'What do you sell?',
  'What hoodies do you have?',
  'Show me quarter-zips',
  'What crewnecks are there?',
]

// Reads the current product page id from the URL (e.g. /products/basic-hoodie).
function currentProductId(pathname: string): string | undefined {
  const m = pathname.match(/^\/products\/(.+)$/)
  return m ? m[1] : undefined
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { user } = useAuth()
  const { setResults } = useSearchResults()
  const navigate = useNavigate()
  const location = useLocation()

  // Reload saved history when a shopper logs in; reset to the greeting on logout.
  useEffect(() => {
    let active = true
    if (user) {
      fetchHistory(user.id)
        .then((rows) => {
          if (!active) return
          const loaded: Message[] = rows.map((r) => ({
            role: r.role,
            text: r.content,
            products: r.products,
          }))
          setMessages(loaded.length ? [GREETING, ...loaded] : [GREETING])
        })
        .catch(() => {
          if (active) setMessages([GREETING])
        })
    } else {
      setMessages([GREETING])
    }
    return () => {
      active = false
    }
  }, [user])

  async function sendMessage(text: string) {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    setMessages((m) => [...m, { role: 'user', text: trimmed }])
    setInput('')
    setError('')
    setLoading(true)
    try {
      const { reply, products } = await sendChat(trimmed, {
        userId: user?.id,
        productId: currentProductId(location.pathname),
      })
      setMessages((m) => [...m, { role: 'assistant', text: reply, products }])
      if (products.length > 0) setResults(trimmed, products)
    } catch {
      setError('Sorry, the chat is not reachable right now. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    void sendMessage(input)
  }

  function openProduct(id: string) {
    navigate(`/products/${id}`)
    setOpen(false)
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <h2>Campus Customs Chat</h2>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-messages" aria-live="polite">
            {user && (
              <p className="chat-note">Signed in as {user.first_name} — your chat is saved.</p>
            )}
            {messages.map((m, i) => (
              <div key={i} className="chat-turn">
                <p className={`bubble ${m.role}`}>{m.text}</p>
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <button
                        type="button"
                        key={p.product_id}
                        className="chat-card"
                        onClick={() => openProduct(p.product_id)}
                      >
                        <img src={p.image_url} alt={p.name} loading="lazy" />
                        <span className="chat-card-name">{p.name}</span>
                        <span className="chat-card-price">{formatPrice(p.price)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && <p className="bubble assistant typing">Typing…</p>}
            {error && <p className="chat-error" role="alert">{error}</p>}
          </div>
          <div className="quick-questions">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                className="quick-chip"
                disabled={loading}
                onClick={() => void sendMessage(q)}
              >
                {q}
              </button>
            ))}
          </div>
          <form className="chat-form" onSubmit={handleSubmit}>
            <label htmlFor="chat-input" className="visually-hidden">
              Type your message
            </label>
            <input
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about hoodies, sizes, prices…"
              autoComplete="off"
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {open ? 'Close chat' : 'Chat with us'}
      </button>
    </div>
  )
}
