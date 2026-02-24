import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SessionHistory from './pages/SessionHistory'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Main dashboard — doctor's primary view */}
        <Route path="/" element={<Dashboard />} />
        {/* Session history — list of all past consultations */}
        <Route path="/history" element={<SessionHistory />} />
      </Routes>
    </BrowserRouter>
  )
}