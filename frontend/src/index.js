import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './styles/Login.css';
import './styles/AdminDashboard.css';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import AdministrativosDashboard from './components/AdministrativosDashboard';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const navigate = useNavigate();
  const [isVerified, setIsVerified] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifyToken = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          throw new Error('No token found');
        }

        // Verify token by making a request to /users/
        const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/users/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        // Only set verified if we get valid data back
        if (response.data && Array.isArray(response.data)) {
          setIsVerified(true);
        } else {
          throw new Error('Invalid response from server');
        }

      } catch (error) {
        console.error('Token verification failed:', error);
        // Clear everything on verification failure
        localStorage.clear();
        sessionStorage.clear();
        document.cookie.split(";").forEach((c) => {
          document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
        navigate('/', { replace: true });
      } finally {
        setIsLoading(false);
      }
    };

    verifyToken();

    // Periodic token verification
    const interval = setInterval(verifyToken, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [navigate]);

  // Show loading state
  if (isLoading) {
    return <div>Verifying authentication...</div>;
  }

  // Only render children if verified
  return isVerified ? children : null;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/dashboard-administrativo" 
          element={
            <ProtectedRoute>
              <AdministrativosDashboard />
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  </React.StrictMode>
);