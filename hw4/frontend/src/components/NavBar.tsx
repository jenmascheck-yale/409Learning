import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

const baseLinks = [
  { to: '/', label: 'Home' },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand">
          Campus Customs
        </Link>
        <nav aria-label="Main">
          <ul className="nav-links">
            {baseLinks.map((l) => (
              <li key={l.to}>
                <NavLink to={l.to} end={l.to === '/'}>
                  {l.label}
                </NavLink>
              </li>
            ))}
            {user ? (
              <>
                <li>
                  <span className="nav-greeting">Hi, {user.first_name || 'shopper'}</span>
                </li>
                <li>
                  <button type="button" className="nav-logout" onClick={handleLogout}>
                    Log out
                  </button>
                </li>
              </>
            ) : (
              <>
                <li>
                  <NavLink to="/login">Log in</NavLink>
                </li>
                <li>
                  <NavLink to="/create-account">Create account</NavLink>
                </li>
              </>
            )}
          </ul>
        </nav>
      </div>
    </header>
  )
}
