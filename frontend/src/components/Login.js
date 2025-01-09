import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const clearStorage = () => {
      localStorage.clear();
      sessionStorage.clear();
      // Clear any cookies
      document.cookie.split(";").forEach((c) => {
        document.cookie = c
          .replace(/^ +/, "")
          .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
    };

    // Clear storage on component mount
    clearStorage();

    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    
    if (token) {
      localStorage.setItem('token', token);
      navigate('/dashboard', { replace: true });
    }
  }, [location, navigate]);

  const handleCognitoLogin = () => {
    setIsLoading(true);
    // Clear any existing tokens before login
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = 'http://localhost:8000/login';
  };

  if (isLoading) {
    return <div className="login-container">Loading...</div>;
  }

  return (
    <div className="login-container">
      <h1>Bus Fleet Management</h1>
      <button onClick={handleCognitoLogin} className="cognito-button">
        Sign In
      </button>
    </div>
  );
};

export default Login;