/**
 * Navbar.jsx — Navigation with auth-aware links.
 */
import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to={user ? '/planner' : '/'} className="navbar-brand">
          EcoPath AI
        </Link>

        <ul className="navbar-links">
          {user ? (
            <>
              <li>
                <NavLink to="/planner" className={({ isActive }) => (isActive ? 'active' : '')}>
                  Route Planner
                </NavLink>
              </li>
              <li>
                <NavLink to="/history" className={({ isActive }) => (isActive ? 'active' : '')}>
                  History
                </NavLink>
              </li>
              <li>
                <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : '')}>
                  Profile
                </NavLink>
              </li>
              <li className="navbar-user">
                <span className="user-greeting">Hi, {user.name.split(' ')[0]}</span>
                <button type="button" className="btn btn-nav-logout" onClick={handleLogout}>
                  Logout
                </button>
              </li>
            </>
          ) : (
            <>
              <li>
                <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
                  Home
                </NavLink>
              </li>
              <li>
                <Link to="/login" className="nav-btn-login">Log In</Link>
              </li>
              <li>
                <Link to="/signup" className="btn btn-nav-signup">Sign Up</Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  )
}

export default Navbar
