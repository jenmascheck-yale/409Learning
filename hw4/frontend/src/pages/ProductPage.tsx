import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail } from '../api'

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setProduct(null)
    setError('')
    fetchProduct(productId)
      .then(setProduct)
      .catch(() => setError('Sorry, we could not find that product.'))
  }, [productId])

  if (error) return <p className="status error" role="alert">{error}</p>
  if (!product) return <p className="status">Loading product…</p>

  return (
    <section>
      <Link to="/products" className="back">
        ← Back to products
      </Link>
      <div className="detail">
        <img src={product.image_url} alt={product.name} className="detail-image" />
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price large">{formatPrice(product.price)}</p>
          <p>{product.description}</p>
          {product.colors && product.colors.length > 0 && (
            <p>
              <strong>Colors:</strong> {product.colors.join(', ')}
            </p>
          )}
          <h2>Sizes and stock</h2>
          <ul className="sizes">
            {product.sizes.map((s) => (
              <li key={s.size} className={s.quantity === 0 ? 'sold-out' : ''}>
                <span className="size">{s.size}</span>
                <span>{s.quantity === 0 ? 'Sold out' : `${s.quantity} in stock`}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
