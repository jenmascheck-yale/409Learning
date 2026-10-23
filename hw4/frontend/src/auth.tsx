import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export type User = {
  id: number
  first_name: string | null
  last_name: string | null
  email: string
}

type AuthContextType = {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => void
}

export type SignupData = {
  first_name: string
  last_name: string
  email: string
  password: string
}

const AuthContext = createContext<AuthContextType | null>(null)

async function postAuth(url: string, body: object): Promise<User> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Something went wrong.')
  return data as User
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  // Remember the signed-in shopper across page reloads (not the password).
  useEffect(() => {
    const saved = localStorage.getItem('cc_user')
    if (saved) {
      try {
        setUser(JSON.parse(saved))
      } catch {
        localStorage.removeItem('cc_user')
      }
    }
  }, [])

  function remember(u: User) {
    setUser(u)
    localStorage.setItem('cc_user', JSON.stringify(u))
  }

  const login = async (email: string, password: string) => {
    remember(await postAuth('/api/login', { email, password }))
  }

  const signup = async (data: SignupData) => {
    remember(await postAuth('/api/signup', data))
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('cc_user')
  }

  return (
    <AuthContext.Provider value={{ user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
