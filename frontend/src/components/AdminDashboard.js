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
  const [vehicles, setVehicles] = useState([]);
  const [showCreateVehicle, setShowCreateVehicle] = useState(false);
  const [vehicleFormData, setVehicleFormData] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    vehicle_type: '',
    plate_number: '',
    company_number: '',
    vin: '',
    company_id: ''
  });
  const [editingVehicle, setEditingVehicle] = useState(null);
  const [routes, setRoutes] = useState([]);
  const [showCreateRoute, setShowCreateRoute] = useState(false);
  const [routeFormData, setRouteFormData] = useState({
    name: '',
    start_point: '',
    end_point: '',
    intermediate_stops: [],
    departure_time: '',
    estimated_duration: 0,
    repetition_frequency: null,
    repetition_period: null,
    company_id: '',
    vehicle_id: null
  });
  const [editingRoute, setEditingRoute] = useState(null);
  const [showVehicleDetails, setShowVehicleDetails] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showRouteDetails, setShowRouteDetails] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);
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

  const fetchVehicles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/vehicles/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setVehicles(response.data);
    } catch (err) {
      setError('Error al cargar vehículos');
    }
  };

  const fetchRoutes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/routes/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setRoutes(response.data);
    } catch (err) {
      setError('Error al cargar rutas');
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchCompanies();
    fetchCurrentUser();
    fetchVehicles();
    fetchRoutes();  // Add this
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

  const handleCreateVehicle = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/vehicles/`, vehicleFormData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setShowCreateVehicle(false);
      fetchVehicles();
      setVehicleFormData({
        brand: '',
        model: '',
        year: new Date().getFullYear(),
        vehicle_type: '',
        plate_number: '',
        company_number: '',
        vin: '',
        company_id: ''
      });
    } catch (err) {
      setError('Error al crear el vehículo');
    }
  };

  const handleUpdateVehicleStatus = async (vehicleId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/vehicles/${vehicleId}/status`,
        { status: newStatus },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      fetchVehicles();
    } catch (err) {
      setError('Error al actualizar el estado del vehículo');
    }
  };

  const startEditingVehicle = (vehicle) => {
    setEditingVehicle(vehicle);
    setVehicleFormData({
      brand: vehicle.brand,
      model: vehicle.model,
      year: vehicle.year,
      vehicle_type: vehicle.vehicle_type,
      plate_number: vehicle.plate_number,
      company_number: vehicle.company_number,
      vin: vehicle.vin || '',
      company_id: vehicle.company_id
    });
    setShowCreateVehicle(true);
  };

  const handleUpdateVehicle = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/vehicles/${editingVehicle.id}`,
        vehicleFormData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateVehicle(false);
      setEditingVehicle(null);
      fetchVehicles();
      setVehicleFormData({
        brand: '',
        model: '',
        year: new Date().getFullYear(),
        vehicle_type: '',
        plate_number: '',
        company_number: '',
        vin: '',
        company_id: ''
      });
    } catch (err) {
      setError('Error al actualizar el vehículo');
    }
  };

  const handleDeleteVehicle = async (vehicleId) => {
    if (window.confirm('¿Está seguro de eliminar este vehículo? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `${process.env.REACT_APP_BACKEND_URL}/vehicles/${vehicleId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        fetchVehicles();
      } catch (err) {
        setError('Error al eliminar el vehículo');
      }
    }
  };

  const handleCreateRoute = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/routes/`, routeFormData, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      setShowCreateRoute(false);
      fetchRoutes();
      setRouteFormData({
        name: '',
        start_point: '',
        end_point: '',
        intermediate_stops: [],
        departure_time: '',
        estimated_duration: 0,
        repetition_frequency: null,
        repetition_period: null,
        company_id: '',
        vehicle_id: null
      });
    } catch (err) {
      setError('Error al crear la ruta');
    }
  };

  const handleUpdateRoute = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/routes/${editingRoute.id}`,
        routeFormData,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateRoute(false);
      setEditingRoute(null);
      fetchRoutes();
      setRouteFormData({
        name: '',
        start_point: '',
        end_point: '',
        intermediate_stops: [],
        departure_time: '',
        estimated_duration: 0,
        repetition_frequency: null,
        repetition_period: null,
        company_id: '',
        vehicle_id: null
      });
    } catch (err) {
      setError('Error al actualizar la ruta');
    }
  };

  const handleRouteStatusChange = async (routeId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/routes/${routeId}/status`,
        { status: newStatus },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      fetchRoutes();
    } catch (err) {
      setError('Error al actualizar el estado de la ruta');
    }
  };

  const handleDeleteRoute = async (routeId) => {
    if (window.confirm('¿Está seguro de eliminar esta ruta? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${process.env.REACT_APP_BACKEND_URL}/routes/${routeId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        fetchRoutes();
      } catch (err) {
        setError('Error al eliminar la ruta');
      }
    }
  };

  const startEditingRoute = (route) => {
    setEditingRoute(route);
    setRouteFormData({
      name: route.name,
      start_point: route.start_point,
      end_point: route.end_point,
      intermediate_stops: route.intermediate_stops || [],
      departure_time: new Date(route.departure_time).toISOString().slice(0, 16),
      estimated_duration: route.estimated_duration,
      repetition_frequency: route.repetition_frequency,
      repetition_period: route.repetition_period,
      company_id: route.company_id,
      vehicle_id: route.vehicle_id
    });
    setShowCreateRoute(true);
  };

  const showUserDetailsModal = (user) => {
    setSelectedUser(user);
    setShowUserDetails(true);
  };

  const showVehicleDetailsModal = (vehicle) => {
    setSelectedVehicle(vehicle);
    setShowVehicleDetails(true);
  };

  const showRouteDetailsModal = (route) => {
    setSelectedRoute(route);
    setShowRouteDetails(true);
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

      {/* Error message */}
      {error && <div className="error">{error}</div>}

      {/* Profile Edit Modal */}
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

        <section className="vehicles-section">
          <div className="section-header">
            <h2>Vehículos</h2>
            <button onClick={() => setShowCreateVehicle(true)} className="create-button">
              Crear Vehículo
            </button>
          </div>

          {showCreateVehicle && (
            <form onSubmit={editingVehicle ? handleUpdateVehicle : handleCreateVehicle} className="vehicle-form">
              <input
                type="text"
                placeholder="Marca"
                value={vehicleFormData.brand}
                onChange={(e) => setVehicleFormData({...vehicleFormData, brand: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Modelo"
                value={vehicleFormData.model}
                onChange={(e) => setVehicleFormData({...vehicleFormData, model: e.target.value})}
                required
              />
              <input
                type="number"
                placeholder="Año"
                value={vehicleFormData.year}
                onChange={(e) => setVehicleFormData({...vehicleFormData, year: parseInt(e.target.value)})}
                required
              />
              <select
                value={vehicleFormData.vehicle_type}
                onChange={(e) => setVehicleFormData({...vehicleFormData, vehicle_type: e.target.value})}
                required
              >
                <option value="">Seleccionar tipo de vehículo</option>
                <option value="BUS">Autobús</option>
                <option value="CAMION">Camión</option>
                <option value="FURGONETA">Furgoneta</option>
                <option value="COCHE">Coche</option>
                <option value="MOTO">Moto</option>
              </select>
              <input
                type="text"
                placeholder="Número de placa"
                value={vehicleFormData.plate_number}
                onChange={(e) => setVehicleFormData({...vehicleFormData, plate_number: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Número del vehículo en la empresa"
                value={vehicleFormData.company_number}
                onChange={(e) => setVehicleFormData({...vehicleFormData, company_number: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="VIN (opcional)"
                value={vehicleFormData.vin}
                onChange={(e) => setVehicleFormData({...vehicleFormData, vin: e.target.value})}
              />
              <select
                value={vehicleFormData.company_id}
                onChange={(e) => setVehicleFormData({...vehicleFormData, company_id: e.target.value})}
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
                <button type="submit">{editingVehicle ? 'Actualizar' : 'Crear'}</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setShowCreateVehicle(false);
                    setEditingVehicle(null);
                    setVehicleFormData({
                      brand: '',
                      model: '',
                      year: new Date().getFullYear(),
                      vehicle_type: '',
                      plate_number: '',
                      company_number: '',
                      vin: '',
                      company_id: ''
                    });
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
                <th>Marca</th>
                <th>Modelo</th>
                <th>Año</th>
                <th>Tipo</th>
                <th>Placa</th>
                <th>Número</th>
                <th>VIN</th>
                <th>Empresa</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.map(vehicle => (
                <tr key={vehicle.id}>
                  <td>{vehicle.brand}</td>
                  <td>{vehicle.model}</td>
                  <td>{vehicle.year}</td>
                  <td>{vehicle.vehicle_type}</td>
                  <td>{vehicle.plate_number}</td>
                  <td>{vehicle.company_number}</td>
                  <td>{vehicle.vin || '-'}</td>
                  <td>{companies.find(c => c.id === vehicle.company_id)?.name || '-'}</td>
                  <td>
                    <select
                      value={vehicle.status}
                      onChange={(e) => handleUpdateVehicleStatus(vehicle.id, e.target.value)}
                      className={`status-select status-${vehicle.status.toLowerCase()}`}
                    >
                      <option value="ACTIVO">Activo</option>
                      <option value="EN_RUTA">En Ruta</option>
                      <option value="MANTENIMIENTO">Mantenimiento</option>
                      <option value="INACTIVO">Inactivo</option>
                      <option value="BAJA">Baja</option>
                      <option value="AVERIADO">Averiado</option>
                    </select>
                  </td>
                  <td>
                    <button 
                      onClick={() => showVehicleDetailsModal(vehicle)}
                      className="details-button"
                    >
                      Ver Detalles
                    </button>
                    <button 
                      onClick={() => startEditingVehicle(vehicle)}
                      className="edit-button"
                    >
                      Editar
                    </button>
                    <button 
                      onClick={() => handleDeleteVehicle(vehicle.id)}
                      className="delete-button"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {showVehicleDetails && selectedVehicle && (
            <div className="modal-overlay">
              <div className="modal-content">
                <h2>Detalles del Vehículo</h2>
                <div className="vehicle-details">
                  <div className="detail-row">
                    <span className="detail-label">Marca:</span>
                    <span className="detail-value">{selectedVehicle.brand}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Modelo:</span>
                    <span className="detail-value">{selectedVehicle.model}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Año:</span>
                    <span className="detail-value">{selectedVehicle.year}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Tipo:</span>
                    <span className="detail-value">{selectedVehicle.vehicle_type}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Placa:</span>
                    <span className="detail-value">{selectedVehicle.plate_number}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Número:</span>
                    <span className="detail-value">{selectedVehicle.company_number}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">VIN:</span>
                    <span className="detail-value">{selectedVehicle.vin || 'No asignado'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Empresa:</span>
                    <span className="detail-value">
                      {companies.find(c => c.id === selectedVehicle.company_id)?.name || '-'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Estado:</span>
                    <span className="detail-value">{selectedVehicle.status}</span>
                  </div>
                </div>
                <button 
                  className="close-button"
                  onClick={() => {
                    setShowVehicleDetails(false);
                    setSelectedVehicle(null);
                  }}
                >
                  Cerrar
                </button>
              </div>
            </div>
          )}
        </section>

        <section className="routes-section">
          <div className="section-header">
            <h2>Rutas</h2>
            <button onClick={() => setShowCreateRoute(true)} className="create-button">
              Crear Ruta
            </button>
          </div>

          {showCreateRoute && (
            <form onSubmit={editingRoute ? handleUpdateRoute : handleCreateRoute} className="route-form">
              <input
                type="text"
                placeholder="Nombre de la ruta"
                value={routeFormData.name}
                onChange={(e) => setRouteFormData({...routeFormData, name: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Punto de inicio"
                value={routeFormData.start_point}
                onChange={(e) => setRouteFormData({...routeFormData, start_point: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Punto final"
                value={routeFormData.end_point}
                onChange={(e) => setRouteFormData({...routeFormData, end_point: e.target.value})}
                required
              />
              
              {/* Date and Time inputs */}
              <div className="datetime-inputs">
                <input
                  type="date"
                  value={routeFormData.departure_time.split('T')[0]}
                  onChange={(e) => {
                    const time = routeFormData.departure_time.split('T')[1] || '00:00';
                    setRouteFormData({
                      ...routeFormData,
                      departure_time: `${e.target.value}T${time}`
                    });
                  }}
                  required
                />
                <input
                  type="time"
                  value={routeFormData.departure_time.split('T')[1] || ''}
                  onChange={(e) => {
                    const date = routeFormData.departure_time.split('T')[0];
                    setRouteFormData({
                      ...routeFormData,
                      departure_time: `${date}T${e.target.value}`
                    });
                  }}
                  required
                />
              </div>

              {/* Duration inputs */}
              <div className="duration-inputs">
                <div className="duration-field">
                  <label>Días:</label>
                  <input
                    type="number"
                    min="0"
                    value={Math.floor(routeFormData.estimated_duration / 1440)}
                    onChange={(e) => {
                      const days = parseInt(e.target.value) || 0;
                      const remainingMinutes = routeFormData.estimated_duration % 1440;
                      setRouteFormData({
                        ...routeFormData,
                        estimated_duration: (days * 1440) + remainingMinutes
                      });
                    }}
                  />
                </div>
                <div className="duration-field">
                  <label>Horas:</label>
                  <input
                    type="number"
                    min="0"
                    max="23"
                    value={Math.floor((routeFormData.estimated_duration % 1440) / 60)}
                    onChange={(e) => {
                      const hours = parseInt(e.target.value) || 0;
                      const days = Math.floor(routeFormData.estimated_duration / 1440);
                      const minutes = routeFormData.estimated_duration % 60;
                      setRouteFormData({
                        ...routeFormData,
                        estimated_duration: (days * 1440) + (hours * 60) + minutes
                      });
                    }}
                  />
                </div>
                <div className="duration-field">
                  <label>Minutos:</label>
                  <input
                    type="number"
                    min="0"
                    max="59"
                    value={routeFormData.estimated_duration % 60}
                    onChange={(e) => {
                      const minutes = parseInt(e.target.value) || 0;
                      const days = Math.floor(routeFormData.estimated_duration / 1440);
                      const hours = Math.floor((routeFormData.estimated_duration % 1440) / 60);
                      setRouteFormData({
                        ...routeFormData,
                        estimated_duration: (days * 1440) + (hours * 60) + minutes
                      });
                    }}
                  />
                </div>
              </div>

              {/* Company selection */}
              <select
                value={routeFormData.company_id}
                onChange={(e) => {
                  setRouteFormData({
                    ...routeFormData,
                    company_id: e.target.value,
                    vehicle_id: null  // Reset vehicle when company changes
                  });
                }}
                required
              >
                <option value="">Seleccionar empresa</option>
                {companies.map(company => (
                  <option key={company.id} value={company.id}>
                    {company.name}
                  </option>
                ))}
              </select>

              {/* Vehicle selection */}
              <select
                value={routeFormData.vehicle_id || ''}
                onChange={(e) => setRouteFormData({...routeFormData, vehicle_id: e.target.value || null})}
              >
                <option value="">Seleccionar vehículo (opcional)</option>
                {vehicles
                  .filter(v => v.company_id === routeFormData.company_id && v.status === 'ACTIVO')
                  .map(vehicle => (
                    <option key={vehicle.id} value={vehicle.id}>
                      {vehicle.brand} {vehicle.model} - {vehicle.plate_number}
                    </option>
                  ))}
              </select>
              <div className="form-buttons">
                <button type="submit">{editingRoute ? 'Actualizar' : 'Crear'}</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setShowCreateRoute(false);
                    setEditingRoute(null);
                    setRouteFormData({
                      name: '',
                      start_point: '',
                      end_point: '',
                      intermediate_stops: [],
                      departure_time: '',
                      estimated_duration: 0,
                      repetition_frequency: null,
                      repetition_period: null,
                      company_id: '',
                      vehicle_id: null
                    });
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
                <th>Origen</th>
                <th>Destino</th>
                <th>Salida</th>
                <th>Duración</th>
                <th>Empresa</th>
                <th>Vehículo</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {routes.map(route => (
                <tr key={route.id}>
                  <td>{route.name}</td>
                  <td>{route.start_point}</td>
                  <td>{route.end_point}</td>
                  <td>{new Date(route.departure_time).toLocaleString()}</td>
                  <td>{route.estimated_duration} min</td>
                  <td>{companies.find(c => c.id === route.company_id)?.name || '-'}</td>
                  <td>{vehicles.find(v => v.id === route.vehicle_id)?.plate_number || '-'}</td>
                  <td>
                    <select
                      value={route.status}
                      onChange={(e) => handleRouteStatusChange(route.id, e.target.value)}
                      className={`status-select status-${route.status.toLowerCase()}`}
                    >
                      <option value="ACTIVA">Activa</option>
                      <option value="EN_EJECUCION">En Ejecución</option>
                      <option value="COMPLETADA">Completada</option>
                      <option value="SUSPENDIDA">Suspendida</option>
                    </select>
                  </td>
                  <td>
                    <button 
                      onClick={() => showRouteDetailsModal(route)}
                      className="details-button"
                    >
                      Ver Detalles
                    </button>
                    <button 
                      onClick={() => startEditingRoute(route)}
                      className="edit-button"
                    >
                      Editar
                    </button>
                    <button 
                      onClick={() => handleDeleteRoute(route.id)}
                      className="delete-button"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {showRouteDetails && selectedRoute && (
            <div className="modal-overlay">
              <div className="modal-content">
                <h2>Detalles de la Ruta</h2>
                <div className="route-details">
                  <div className="detail-row">
                    <span className="detail-label">Nombre:</span>
                    <span className="detail-value">{selectedRoute.name}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Origen:</span>
                    <span className="detail-value">{selectedRoute.start_point}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Destino:</span>
                    <span className="detail-value">{selectedRoute.end_point}</span>
                  </div>
                  {selectedRoute.intermediate_stops?.length > 0 && (
                    <div className="detail-row">
                      <span className="detail-label">Paradas:</span>
                      <div className="detail-value">
                        {selectedRoute.intermediate_stops.map((stop, index) => (
                          <div key={index} className="stop-detail">
                            {index + 1}. {stop.location} ({stop.estimated_stop_time} min)
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  <div className="detail-row">
                    <span className="detail-label">Salida:</span>
                    <span className="detail-value">
                      {new Date(selectedRoute.departure_time).toLocaleString()}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Duración:</span>
                    <span className="detail-value">{selectedRoute.estimated_duration} min</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Empresa:</span>
                    <span className="detail-value">
                      {companies.find(c => c.id === selectedRoute.company_id)?.name || '-'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Vehículo:</span>
                    <span className="detail-value">
                      {vehicles.find(v => v.id === selectedRoute.vehicle_id)?.plate_number || 'No asignado'}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Estado:</span>
                    <span className="detail-value">{selectedRoute.status}</span>
                  </div>
                </div>
                <button 
                  className="close-button"
                  onClick={() => {
                    setShowRouteDetails(false);
                    setSelectedRoute(null);
                  }}
                >
                  Cerrar
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default AdminDashboard;