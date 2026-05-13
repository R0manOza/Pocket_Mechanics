import { NavLink } from "react-router-dom"

const NAV = [
  { to: "/chat", label: "Chat" },
  { to: "/analyze", label: "Analyze a photo" },
]

export function Header() {
  return (
    <nav className="flex items-center gap-4 border-b border-slate-200 bg-white px-4 py-3">
      <NavLink
        to="/"
        className="text-sm font-semibold text-slate-900 hover:text-slate-700"
      >
        Pocket Mechanics
      </NavLink>
      <ul className="flex gap-1">
        {NAV.map((n) => (
          <li key={n.to}>
            <NavLink
              to={n.to}
              className={({ isActive }) =>
                `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  isActive
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {n.label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  )
}
