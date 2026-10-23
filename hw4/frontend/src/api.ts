// Calls to the FastAPI backend. Vite proxies /api and /images to port 8000.

export type Product = {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors?: string[]
  price: number
  image_url: string
}

// Product cards the chat search returns (API contract for Problem 7).
export type ChatResponse = { reply: string; products: Product[] }

// One saved message when reloading a logged-in shopper's history (Problem 8).
export type HistoryMessage = { role: 'user' | 'assistant'; content: string; products: Product[] }

export type SizeStock = { size: string; quantity: number }

export type ProductDetail = Product & { sizes: SizeStock[] }

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)

export const sendChat = (
  message: string,
  opts: { userId?: number; productId?: string } = {},
) =>
  getJson<ChatResponse>('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      user_id: opts.userId ?? null,
      product_id: opts.productId ?? null,
    }),
  })

export const fetchHistory = (userId: number) =>
  getJson<HistoryMessage[]>(`/api/chat/history?user_id=${userId}`)

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
