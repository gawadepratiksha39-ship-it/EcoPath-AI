/**
 * App.jsx — Root routing with public and protected pages.
 */
import { Routes, Route, useLocation } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Home from './pages/Home'
import History from './pages/History'
import Profile from './pages/Profile'

function AppLayout({ children, fullWidth = false }) {
  return (
    <div className="app">
      <Navbar />
      <main className={fullWidth ? 'main-content main-content-full' : 'main-content'}>
        {children}
      </main>
      <Footer />
    </div>
  )
}

function App() {
  const location = useLocation()
  const isWelcome = location.pathname === '/'

  return (
    <AppLayout fullWidth={isWelcome}>
      <Routes>
        <Route path="/" element={<Welcome />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/planner"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AppLayout>
  )
}

export default App
