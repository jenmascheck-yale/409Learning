import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Product } from './api'

// Shared state so a chat search can update the main Products page too.
type SearchResults = {
  query: string
  products: Product[]
}

type SearchContextType = {
  results: SearchResults | null
  setResults: (query: string, products: Product[]) => void
  clear: () => void
}

const SearchContext = createContext<SearchContextType | null>(null)

export function SearchResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<SearchResults | null>(null)

  const setResults = (query: string, products: Product[]) => {
    if (products.length > 0) setResultsState({ query, products })
  }
  const clear = () => setResultsState(null)

  return (
    <SearchContext.Provider value={{ results, setResults, clear }}>
      {children}
    </SearchContext.Provider>
  )
}

export function useSearchResults() {
  const ctx = useContext(SearchContext)
  if (!ctx) throw new Error('useSearchResults must be used within SearchResultsProvider')
  return ctx
}
