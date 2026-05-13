import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import { Layout } from "./components/Layout"
import { AnalyzePage } from "./pages/AnalyzePage"
import { ChatPage } from "./pages/ChatPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
