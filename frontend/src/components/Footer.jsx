/**
 * Footer.jsx — Site footer.
 */
import { Link } from 'react-router-dom'

function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <div>
          <strong className="footer-brand">EcoPath AI</strong>
          <p>Sustainable travel across India</p>
        </div>
        <div className="footer-links">
          <Link to="/">Home</Link>
          <Link to="/planner">Planner</Link>
          <Link to="/history">History</Link>
        </div>
        <p className="footer-copy">&copy; {new Date().getFullYear()} EcoPath AI. Built for climate action.</p>
      </div>
    </footer>
  )
}

export default Footer
