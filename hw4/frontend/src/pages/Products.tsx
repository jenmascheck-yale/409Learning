import { useEffect, useMemo, useState } from 'react'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import { useSearchResults } from '../searchResults'

// Group a messy garment_type into a friendly category (mirrors the backend).
function categoryOf(garmentType: string): string {
  const t = garmentType.toLowerCase()
  if (t.includes('hood')) return 'Hoodies'
  if (t.includes('crew')) return 'Crewnecks'
  if (t.includes('zip')) return 'Quarter-Zips'
  if (t.includes('jacket')) return 'Jackets'
  if (t.includes('t-shirt') || t.includes('tee') || t.endsWith('shirt')) return 'T-Shirts'
  return 'Other'
}

const CATEGORIES = ['All', 'Hoodies', 'Crewnecks', 'T-Shirts', 'Quarter-Zips', 'Jackets']

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [category, setCategory] = useState('All')
  const [query, setQuery] = useState('')
  const { results, clear } = useSearchResults()

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch(() => setError('Could not load products. Is the backend running on port 8000?'))
      .finally(() => setLoading(false))
  }, [])

  // Filter + search over the full catalogue (front-end usability improvement).
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return products.filter((p) => {
      const inCategory = category === 'All' || categoryOf(p.garment_type) === category
      const matches =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.garment_type.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q)
      return inCategory && matches
    })
  }, [products, category, query])

  // A chat search takes over the grid until the shopper clears it.
  if (results) {
    return (
      <section>
        <h1>Products</h1>
        <div className="search-banner">
          <span>
            Showing {results.products.length} result
            {results.products.length === 1 ? '' : 's'} for your chat search: “{results.query}”
          </span>
          <button type="button" className="link-button" onClick={clear}>
            Show all products
          </button>
        </div>
        <div className="grid">
          {results.products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <section>
      <h1>Products</h1>

      <div className="filters">
        <div className="category-buttons" role="group" aria-label="Filter by category">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              className={`chip ${category === c ? 'active' : ''}`}
              onClick={() => setCategory(c)}
            >
              {c}
            </button>
          ))}
        </div>
        <input
          type="search"
          className="product-search"
          placeholder="Search products…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search products"
        />
      </div>

      {loading && <p className="status">Loading products…</p>}
      {error && <p className="status error" role="alert">{error}</p>}
      {!loading && !error && (
        <p className="result-count">
          {filtered.length} product{filtered.length === 1 ? '' : 's'}
        </p>
      )}
      {!loading && filtered.length === 0 && !error && (
        <p className="status">No products match your search. Try another category or term.</p>
      )}
      <div className="grid">
        {filtered.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  )
}
