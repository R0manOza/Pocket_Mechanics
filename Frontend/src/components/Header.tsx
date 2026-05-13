import { useState } from "react"
import { NavLink } from "react-router-dom"
import { Logo } from "./Logo"

const NAV = [
  { to: "/chat", label: "Chat" },
  { to: "/analyze", label: "Analyze a photo" },
]

export function Header() {
  const [open, setOpen] = useState(false)

  return (
    <nav className="sticky w-full z-50 transition-all duration-300 border-b border-b-transparent bg-transparent max-sm:pt-4 max-sm:pb-2 sm:pt-6 xl:sm:pt-8">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto flex justify-between items-center">
        <NavLink
          to="/"
          aria-label="Pocket Mechanics — home"
          className="shrink-0 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-brand-accent"
        >
          <Logo />
        </NavLink>

        <ul className="hidden md:flex items-center space-x-8">
          {NAV.map((n) => (
            <li key={n.to}>
              <NavLink
                to={n.to}
                className={({ isActive }) =>
                  `text-base 2xl:text-lg font-medium transition-colors ${
                    isActive
                      ? "text-brand-accent"
                      : "text-brand-text-muted hover:text-brand-text"
                  }`
                }
              >
                {n.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <button
          type="button"
          className="md:hidden text-brand-text outline-none focus-visible:ring-2 focus-visible:ring-brand-accent rounded hover:cursor-pointer"
          aria-label={open ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="27"
            height="27"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            {open ? (
              <>
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </>
            ) : (
              <>
                <path d="M4 5h16" />
                <path d="M4 12h16" />
                <path d="M4 19h16" />
              </>
            )}
          </svg>
        </button>
      </div>

      {open && (
        <ul className="md:hidden mx-4 mt-4 flex flex-col gap-1 rounded-xl bg-brand-card p-3 border border-brand-border">
          {NAV.map((n) => (
            <li key={n.to}>
              <NavLink
                to={n.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? "text-brand-accent bg-brand-card-soft"
                      : "text-brand-text-muted hover:text-brand-text hover:bg-brand-card-soft"
                  }`
                }
              >
                {n.label}
              </NavLink>
            </li>
          ))}
        </ul>
      )}
    </nav>
  )
}
