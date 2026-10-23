import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <>
      <section className="hero">
        <svg className="crest" viewBox="0 0 64 72" aria-hidden="true">
          <path
            d="M32 2 L60 12 V34 C60 52 48 64 32 70 C16 64 4 52 4 34 V12 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path
            d="M32 8 L54 16 V34 C54 48 44 58 32 63 C20 58 10 48 10 34 V16 Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="1"
            opacity="0.5"
          />
          <text x="32" y="43" textAnchor="middle" className="crest-mark">
            CC
          </text>
        </svg>
        <p className="eyebrow">Est. New Haven, Connecticut</p>
        <h1>Wear your Bulldog spirit every day</h1>
        <p className="lead">
          Hoodies for late nights in the library, crewnecks for game day, and tees for every
          walk across Old Campus. Campus Customs is your stop for Yale gear.
        </p>
        <Link to="/products" className="button">
          Shop all products
        </Link>
      </section>

      <section className="features">
        <article>
          <h2>Game day ready</h2>
          <p>Show up to The Game in rivalry tees and layers made for cold November stands.</p>
        </article>
        <article>
          <h2>Your college, your colors</h2>
          <p>Gear for every residential college, so you can rep Berkeley, Morse, Saybrook and more.</p>
        </article>
        <article>
          <h2>Gifts for the whole family</h2>
          <p>Parents, siblings, and grandparents can join the Bulldog family with a sweatshirt of their own.</p>
        </article>
      </section>
    </>
  )
}
