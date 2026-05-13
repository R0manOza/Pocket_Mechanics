import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import DashboardLayout  from "./layouts/DashboardLayout"
import { AnalyzePage } from "./pages/AnalyzePage"
import { ChatPage } from "./pages/ChatPage"
import { LandingPage } from "./pages/LandingPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
