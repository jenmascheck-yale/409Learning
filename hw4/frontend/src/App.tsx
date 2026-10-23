import { Route, Routes } from 'react-router-dom'
import NavBar from './components/NavBar'
import ChatWidget from './components/ChatWidget'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductPage from './pages/ProductPage'
import About from './pages/About'
import Login from './pages/Login'
import CreateAccount from './pages/CreateAccount'

export default function App() {
  return (
    <>
      <NavBar />
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductPage />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<p className="status">Page not found.</p>} />
        </Routes>
      </main>
      <footer className="footer">
        <p>Campus Customs · New Haven, CT · Class project store, not affiliated with Yale University</p>
      </footer>
      <ChatWidget />
    </>
  )
}
