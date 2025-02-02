import React from 'react';

import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <nav className="navbar navbar-expand-sm navbar-dark bg-primary mb-3 py-0">
      <div className="container">
        <a href="/" className="navbar-brand">
          Video Reuse Detector
        </a>
        <div>
          <ul className="navbar-nav mr-auto">
            <li className="nav-item">
              <Link to="/" className="nav-link">
                <i className="fas fa-home" /> Home
              </Link>
            </li>
            <li>
              <Link to="/admin" className="nav-link" target="_blank">
                <i className="fas fa-user-cog" /> Admin
              </Link>
            </li>
            <li>
              <Link to="/dashboard" className="nav-link" target="_blank">
                <i className="fas fa-tachometer-alt" /> RQ-dashboard
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}
