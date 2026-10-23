import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function CreateAccount() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function update(field: keyof typeof form) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm((f) => ({ ...f, [field]: e.target.value }))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }
    setLoading(true)
    try {
      const { confirm_password, ...data } = form
      void confirm_password
      await signup(data)
      navigate('/products')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Create account</h1>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          First name
          <input autoComplete="given-name" required value={form.first_name} onChange={update('first_name')} />
        </label>
        <label>
          Last name
          <input autoComplete="family-name" required value={form.last_name} onChange={update('last_name')} />
        </label>
        <label>
          Email
          <input type="email" autoComplete="email" required value={form.email} onChange={update('email')} />
        </label>
        <label>
          Password
          <input type="password" autoComplete="new-password" required value={form.password} onChange={update('password')} />
        </label>
        <label>
          Confirm password
          <input type="password" autoComplete="new-password" required value={form.confirm_password} onChange={update('confirm_password')} />
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="button" disabled={loading}>
          {loading ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
