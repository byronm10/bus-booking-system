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
  const [showProfileEdit, setShowProfileEdit] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    role: '',
    status: ''
  });
  const [currentUser, setCurrentUser] = useState(null);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [userFormData, setUserFormData] = useState({
    name: '',
    email: '',
    role: 'OPERATOR',
    company_id: ''
  });
  const [editingUser, setEditingUser] = useState(null);
  const [showEmailWarning, setShowEmailWarning] = useState(false);
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
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

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get('http://localhost:8000/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setCurrentUser(response.data);
    } catch (err) {
      setError('Failed to fetch user profile');
      if (err.response?.status === 401) {
        navigate('/');
      }
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchCompanies();
    fetchCurrentUser();
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

  const handleEditProfile = async (e) => {
    e.preventDefault();
    if (profileData.email !== currentUser.email) {
      if (!window.confirm('Al cambiar su correo electrónico, deberá iniciar sesión con el nuevo correo en su próximo acceso. ¿Desea continuar?')) {
        return;
      }
    }
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put('http://localhost:8000/users/profile', 
        {
          name: profileData.name,
          email: profileData.email,
          identification: profileData.identification,
          role: profileData.role,
          status: profileData.status
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      if (response.data.warning) {
        alert(response.data.warning);
        handleSignOut();  // Sign out user after email change
      } else {
        setShowProfileEdit(false);
        fetchUsers();
      }
    } catch (err) {
      setError('Error al actualizar el perfil');
    }
  };

  const startProfileEdit = () => {
    if (!currentUser) {
      setError('User profile not loaded');
      return;
    }
    
    setProfileData({
      name: currentUser.name || '',
      email: currentUser.email || '',
      role: currentUser.role || '',
      status: currentUser.status || ''
    });
    setShowProfileEdit(true);
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://localhost:8000/users/', userFormData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setShowCreateUser(false);
      fetchUsers();
      setUserFormData({ name: '', email: '', role: 'OPERATOR', company_id: '' });
    } catch (err) {
      console.error('Error creating user:', err.response?.data?.detail || err.message);
      setError(err.response?.data?.detail || 'Error al crear el usuario');
    }
  };

  const startEditingUser = (user) => {
    setEditingUser(user);
    setUserFormData({
      name: user.name,
      email: user.email,
      role: user.role,
      company_id: user.company_id
    });
    setShowCreateUser(true);
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('¿Está seguro de eliminar este usuario? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`http://localhost:8000/users/${userId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        fetchUsers();
      } catch (err) {
        console.error('Error deleting user:', err.response?.data?.detail || err.message);
        setError(err.response?.data?.detail || 'Error al eliminar el usuario');
      }
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(`http://localhost:8000/users/${editingUser.id}`, userFormData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setShowCreateUser(false);
      setEditingUser(null);
      fetchUsers();
      setUserFormData({ name: '', email: '', role: 'OPERATOR', company_id: '' });
    } catch (err) {
      console.error('Error updating user:', err.response?.data?.detail || err.message);
      setError(err.response?.data?.detail || 'Error al actualizar el usuario');
    }
  };

  const showUserDetailsModal = (user) => {
    setSelectedUser(user);
    setShowUserDetails(true);
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="header-buttons">
          <button 
            onClick={startProfileEdit} 
            className="edit-profile-button"
            disabled={!currentUser}
          >
            Editar Perfil
          </button>
          <button onClick={handleSignOut} className="sign-out-button">
            Sign Out
          </button>
        </div>
      </div>
      {error && <div className="error">{error}</div>}

      {/* Add Profile Edit Modal */}
      {showProfileEdit && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Editar Perfil</h2>
            <form onSubmit={handleEditProfile} className="profile-form">
              <div className="form-group">
                <label>Nombre:</label>
                <input
                  type="text"
                  value={profileData.name}
                  onChange={(e) => setProfileData({...profileData, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email:</label>
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Identificación:</label>
                <input
                  type="text"
                  value={profileData.identification || ''}
                  onChange={(e) => setProfileData({...profileData, identification: e.target.value})}
                  required
                />
              </div>
              <div className="form-buttons">
                <button type="submit">Guardar</button>
                <button 
                  type="button" 
                  onClick={() => setShowProfileEdit(false)}
                  className="cancel-button"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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
          <div className="section-header">
            <h2>Usuarios</h2>
            <button onClick={() => setShowCreateUser(true)} className="create-button">
              Crear Usuario
            </button>
          </div>

          {showCreateUser && (
            <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser} className="user-form">
              <input
                type="text"
                placeholder="Nombre"
                value={userFormData.name}
                onChange={(e) => setUserFormData({...userFormData, name: e.target.value})}
                required
              />
              <input
                type="email"
                placeholder="Correo electrónico"
                value={userFormData.email}
                onChange={(e) => setUserFormData({...userFormData, email: e.target.value})}
                required
              />
              <select
                value={userFormData.role}
                onChange={(e) => setUserFormData({...userFormData, role: e.target.value})}
                required
              >
                <option value="">Seleccionar rol</option>
                <option value="ADMIN">Administrador</option>
                <option value="OPERADOR">Operador</option>
                <option value="CONDUCTOR">Conductor</option>
                <option value="PASAJERO">Pasajero</option>
                <option value="TECNICO">Técnico</option>
                <option value="JEFE_TALLER">Jefe de Taller</option>
                <option value="ADMINISTRATIVO">Administrativo</option>
              </select>
              <select
                value={userFormData.company_id}
                onChange={(e) => setUserFormData({...userFormData, company_id: e.target.value})}
                required
              >
                <option value="">Seleccionar empresa</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>
              <div className="form-buttons">
                <button type="submit">{editingUser ? 'Actualizar' : 'Crear'}</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setShowCreateUser(false);
                    setEditingUser(null);
                    setUserFormData({ name: '', email: '', role: 'OPERATOR', company_id: '' });
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
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Empresa</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td>{user.name}</td>
                  <td>{user.email}</td>
                  <td>{user.role}</td>
                  <td>{user.status}</td>
                  <td>
                    {companies.find(c => c.id === user.company_id)?.name || '-'}
                  </td>
                  <td>
                    <button 
                      onClick={() => showUserDetailsModal(user)}
                      className="details-button"
                    >
                      Ver Detalles
                    </button>
                    <button 
                      onClick={() => startEditingUser(user)}
                      className="edit-button"
                    >
                      Editar
                    </button>
                    <button 
                      onClick={() => handleDeleteUser(user.id)}
                      className="delete-button"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {showUserDetails && selectedUser && (
            <div className="modal-overlay">
              <div className="modal-content">
                <h2>Detalles del Usuario</h2>
                <div className="user-details">
                  <div className="detail-row">
                    <span className="detail-label">Nombre:</span>
                    <span className="detail-value">{selectedUser.name}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Email:</span>
                    <span className="detail-value">{selectedUser.email}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Identificación:</span>
                    <span className="detail-value">{selectedUser.identification || 'No asignado'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Rol:</span>
                    <span className="detail-value">{selectedUser.role}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Estado:</span>
                    <span className="detail-value">{selectedUser.status}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Empresa:</span>
                    <span className="detail-value">
                      {companies.find(c => c.id === selectedUser.company_id)?.name || '-'}
                    </span>
                  </div>
                </div>
                <button 
                  className="close-button"
                  onClick={() => {
                    setShowUserDetails(false);
                    setSelectedUser(null);
                  }}
                >
                  Cerrar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;