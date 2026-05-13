import { Outlet } from "react-router-dom"
import { Header } from "../components/Header"

const DashboardLayout = () => {
  return (
    <div className="flex h-full flex-col w-full min-h-screen px-4 2xl:px-10">
      <Header />
      <main className="flex-1 overflow-y-auto pt-20 pb-8 2xl:pt-24 2xl:pb-16">
        <Outlet />
      </main>
    </div>
  )
}

export default DashboardLayout