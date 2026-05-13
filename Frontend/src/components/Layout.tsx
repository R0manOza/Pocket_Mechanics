import { Outlet } from "react-router-dom"
import { Header } from "./Header"

export function Layout() {
  return (
    <div className="flex h-full flex-col">
      <Header />
      <main className="min-h-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
