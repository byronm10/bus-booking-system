import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('http://localhost:8000/users/', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        setUsers(response.data);
      } catch (err) {
        setError('Failed to fetch users');
        if (err.response?.status === 401) {
          // Redirect to login if unauthorized
          navigate('/');
        }
      }
    };

    fetchUsers();
  }, [navigate]);

  const handleSignOut = async () => {
    try {
      // Call backend logout endpoint first
      const response = await axios.post('http://localhost:8000/logout', {});

      // Clear all storage
      localStorage.clear();
      sessionStorage.clear();
      document.cookie.split(";").forEach((c) => {
        document.cookie = c
          .replace(/^ +/, "")
          .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });

      // Redirect to Cognito logout URL if provided
      if (response.data.logoutUrl) {
        window.location.replace(response.data.logoutUrl);
      } else {
        window.location.replace('/');
      }
    } catch (error) {
      console.warn('Logout error:', error);
      // Fallback to local logout
      localStorage.clear();
      sessionStorage.clear();
      window.location.replace('/');
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <button onClick={handleSignOut} className="sign-out-button">
          Sign Out
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="users-list">
        <h2>Users</h2>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id}>
                <td>{user.name}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminDashboard;