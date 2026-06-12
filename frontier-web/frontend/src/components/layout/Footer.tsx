import Link from 'next/link'
import Logo from '../shared/Logo'

const categories = ['Art', 'Philosophy', 'Politics', 'Culture', 'History', 'Essay']

const links = {
  journal: [
    { label: 'About', href: '/about' },
    { label: 'Archive', href: '/archive' },
    { label: 'Contributors', href: '/contributors' },
    { label: 'Contact', href: '/contact' },
  ],
  legal: [
    { label: 'Privacy Policy', href: '/privacy' },
    { label: 'Terms of Use', href: '/terms' },
  ],
}

export default function Footer() {
  return (
    <footer className="border-t border-border/50 mt-24">
      {/* Main footer grid */}
      <div className="container py-16 grid grid-cols-1 md:grid-cols-[2fr_1fr_1fr] gap-12">

        {/* Brand */}
        <div className="flex flex-col gap-4 max-w-xs">
          <Logo />
          <p className="text-sm text-muted-foreground font-light leading-relaxed">
            A journal of ideas at the edge of art, philosophy, and culture.
            Published independently since 2021.
          </p>

        </div>

        {/* Categories */}
        <div className="flex flex-col gap-4">
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            Topics
          </span>
          <ul className="flex flex-col gap-2">
            {categories.map((cat) => (
              <li key={cat}>
                <Link
                  href={`/category/${cat.toLowerCase()}`}
                  className="text-sm text-foreground/70 hover:text-foreground transition-colors duration-200 font-light"
                >
                  {cat}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Journal links */}
        <div className="flex flex-col gap-4">
          <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            Journal
          </span>
          <ul className="flex flex-col gap-2">
            {links.journal.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="text-sm text-foreground/70 hover:text-foreground transition-colors duration-200 font-light"
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="container pb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-t border-border/40 pt-6">
        <p className="text-xs text-muted-foreground font-light">
          © {new Date().getFullYear()} Frontier. All rights reserved.
        </p>
        <div className="flex items-center gap-6">
          {links.legal.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  )
}