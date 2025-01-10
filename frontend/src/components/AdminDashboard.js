import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [error, setError] = useState('');
  const [showCreateCompany, setShowCreateCompany] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    nit: '',
    email: '',
    phone: '',
    address: ''
  });
  const [editingCompany, setEditingCompany] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();

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

  const fetchCompanies = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/companies/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setCompanies(response.data);
    } catch (err) {
      setError('Error al cargar empresas');
    }
  };

  const fetchCompanyDetails = async (companyId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://localhost:8000/companies/${companyId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setSelectedCompany(response.data);
      setShowDetails(true);
    } catch (err) {
      setError('Error al cargar detalles de la empresa');
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchCompanies();
  }, [navigate]);

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://localhost:8000/companies/', formData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setShowCreateCompany(false);
      fetchCompanies();
      setFormData({ name: '', nit: '', email: '', phone: '', address: '' });
    } catch (err) {
      setError('Error al crear la empresa');
    }
  };

  const handleEditCompany = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(`http://localhost:8000/companies/${editingCompany.id}`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setEditingCompany(null);
      setShowCreateCompany(false);
      fetchCompanies();
      setFormData({ name: '', nit: '', email: '', phone: '', address: '' });
    } catch (err) {
      setError('Error al actualizar la empresa');
    }
  };

  const handleDeleteCompany = async (companyId) => {
    if (window.confirm('¿Está seguro de eliminar esta empresa? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`http://localhost:8000/companies/${companyId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        fetchCompanies();
      } catch (err) {
        setError('Error al eliminar la empresa');
      }
    }
  };

  const startEditing = (company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      nit: company.nit,
      email: company.email,
      phone: company.phone,
      address: company.address
    });
    setShowCreateCompany(true);
  };

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
      <div className="dashboard-content">
        <section className="companies-section">
          <div className="section-header">
            <h2>Empresas de Transporte</h2>
            <button onClick={() => setShowCreateCompany(true)} className="create-button">
              Crear Empresa
            </button>
          </div>
          
          {showCreateCompany && (
            <form onSubmit={editingCompany ? handleEditCompany : handleCreateCompany} className="company-form">
              <input
                type="text"
                placeholder="Nombre de la empresa"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="NIT"
                value={formData.nit}
                onChange={(e) => setFormData({...formData, nit: e.target.value})}
                required
              />
              <input
                type="email"
                placeholder="Correo electrónico"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
              <input
                type="tel"
                placeholder="Teléfono"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Dirección"
                value={formData.address}
                onChange={(e) => setFormData({...formData, address: e.target.value})}
                required
              />
              <div className="form-buttons">
                <button type="submit">{editingCompany ? 'Actualizar' : 'Guardar'}</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setShowCreateCompany(false);
                    setEditingCompany(null);
                    setFormData({ name: '', nit: '', email: '', phone: '', address: '' });
                  }}
                >
                  Cancelar
                </button>
              </div>
            </form>
          )}
          
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>NIT</th>
                <th>Correo</th>
                <th>Teléfono</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {companies.map(company => (
                <tr key={company.id}>
                  <td>{company.name}</td>
                  <td>{company.nit}</td>
                  <td>{company.email}</td>
                  <td>{company.phone}</td>
                  <td>{company.status}</td>
                  <td>
                    <button 
                      onClick={() => fetchCompanyDetails(company.id)}
                      className="details-button"
                    >
                      Ver Detalles
                    </button>
                    <button 
                      onClick={() => startEditing(company)}
                      className="edit-button"
                    >
                      Editar
                    </button>
                    <button 
                      onClick={() => handleDeleteCompany(company.id)}
                      className="delete-button"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Modal de detalles */}
          {showDetails && selectedCompany && (
            <div className="modal-overlay">
              <div className="modal-content">
                <h2>Detalles de la Empresa</h2>
                <div className="company-details">
                  <div className="detail-row">
                    <span className="detail-label">Nombre:</span>
                    <span className="detail-value">{selectedCompany.name}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">NIT:</span>
                    <span className="detail-value">{selectedCompany.nit}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Email:</span>
                    <span className="detail-value">{selectedCompany.email}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Teléfono:</span>
                    <span className="detail-value">{selectedCompany.phone}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Dirección:</span>
                    <span className="detail-value">{selectedCompany.address}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Estado:</span>
                    <span className="detail-value">{selectedCompany.status}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Creado:</span>
                    <span className="detail-value">
                      {new Date(selectedCompany.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <button 
                  className="close-button"
                  onClick={() => {
                    setShowDetails(false);
                    setSelectedCompany(null);
                  }}
                >
                  Cerrar
                </button>
              </div>
            </div>
          )}
        </section>

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
    </div>
  );
};

export default AdminDashboard;