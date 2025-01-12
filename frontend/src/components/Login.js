import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';  // Add this import
import '../styles/Login.css';

const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [isResettingPassword, setIsResettingPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetStep, setResetStep] = useState(1); // 1: email, 2: code+password
  const [error, setError] = useState('');

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

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/forgot-password`, null, {
        params: {
          email: resetEmail
        }
      });
      setResetStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.[0]?.msg || 'Error al procesar la solicitud');
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    try {
        await axios.post(`${process.env.REACT_APP_BACKEND_URL}/reset-password`, {
            email: resetEmail,
            code: resetCode,
            new_password: newPassword
        });
        setIsResettingPassword(false);
        setResetStep(1);
        alert('Contraseña actualizada exitosamente');
    } catch (err) {
        setError(err.response?.data?.detail || 'Error al cambiar la contraseña');
    }
};

  if (isLoading) {
    return <div className="login-container">Loading...</div>;
  }

  return (
    <div className="login-container">
      <h1>Bus Fleet Management</h1>
      
      {!isResettingPassword ? (
        <>
          <button onClick={handleCognitoLogin} className="cognito-button">
            Sign In
          </button>
          <button 
            onClick={() => setIsResettingPassword(true)} 
            className="forgot-password-button"
          >
            Olvidé mi contraseña
          </button>
        </>
      ) : (
        resetStep === 1 ? (
          <form onSubmit={handleForgotPassword} className="reset-form">
            <h2>Recuperar Contraseña</h2>
            <input
              type="email"
              placeholder="Correo electrónico"
              value={resetEmail}
              onChange={(e) => setResetEmail(e.target.value)}
              required
            />
            <button type="submit">Enviar Código</button>
            <button 
              type="button" 
              onClick={() => {
                setIsResettingPassword(false);
                setError('');  // Clear any errors when canceling
              }}
              className="cancel-button"
            >
              Cancelar
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className="reset-form">
            <h2>Cambiar Contraseña</h2>
            <input
              type="text"
              placeholder="Código de verificación"
              value={resetCode}
              onChange={(e) => setResetCode(e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Nueva contraseña"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <button type="submit">Cambiar Contraseña</button>
            <button 
              type="button" 
              onClick={() => {
                setIsResettingPassword(false);
                setError('');  // Clear any errors when canceling
              }}
              className="cancel-button"
            >
              Cancelar
            </button>
          </form>
        )
      )}

      {/* Ensure error is a string before rendering */}
      {error && <div className="error">{typeof error === 'object' ? JSON.stringify(error) : error}</div>}
    </div>
  );
};

export default Login;