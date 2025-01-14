import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const formatLocalDateTime = (utcDateTime) => {
  if (!utcDateTime) return '';
  // Split the ISO string and keep exact time
  const [datePart, timePart] = utcDateTime.split('T');
  const timeWithoutZ = timePart?.split('.')[0] || '00:00';
  return `${datePart} ${timeWithoutZ}`;
};

const AdministrativosDashboard = () => {
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [error, setError] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const navigate = useNavigate();

  const [showCreateVehicle, setShowCreateVehicle] = useState(false);
  const [vehicleFormData, setVehicleFormData] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    vehicle_type: '',
    plate_number: '',
    company_number: '',
    vin: '',
    company_id: currentUser?.company_id || ''
  });
  const [editingVehicle, setEditingVehicle] = useState(null);
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
    company_id: currentUser?.company_id || '',
    vehicle_id: null
  });
  const [editingRoute, setEditingRoute] = useState(null);

  const [showCreateUser, setShowCreateUser] = useState(false);
  const [userFormData, setUserFormData] = useState({
    name: '',
    email: '',
    role: '',
    company_id: currentUser?.company_id || ''
  });
  const [editingUser, setEditingUser] = useState(null);

  const [showUserDetails, setShowUserDetails] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const [showVehicleDetails, setShowVehicleDetails] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [showRouteDetails, setShowRouteDetails] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);

  // Fetch data for the administrative user's company
  const fetchData = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`
      };

      // First get current user to get company_id
      console.log('Fetching current user...');
      const currentUserRes = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/users/me`, 
        { headers }
      );
      setCurrentUser(currentUserRes.data);
      console.log('Current user data:', currentUserRes.data);

      // Then fetch all other data filtered by company
      console.log(`Fetching data for company: ${currentUserRes.data.company_id}`);
      
      try {
        const [usersRes, companiesRes, vehiclesRes, routesRes] = await Promise.all([
          axios.get(`${process.env.REACT_APP_BACKEND_URL}/users/company/${currentUserRes.data.company_id}`, { headers }),
          axios.get(`${process.env.REACT_APP_BACKEND_URL}/companies/${currentUserRes.data.company_id}`, { headers }),
          axios.get(`${process.env.REACT_APP_BACKEND_URL}/vehicles/company/${currentUserRes.data.company_id}`, { headers }),
          axios.get(`${process.env.REACT_APP_BACKEND_URL}/routes/company/${currentUserRes.data.company_id}`, { headers })
        ]);

        console.log('API Responses:', {
          users: usersRes.data,
          company: companiesRes.data,
          vehicles: vehiclesRes.data,
          routes: routesRes.data
        });

        // Filter out ADMIN and ADMINISTRATIVO users
        const filteredUsers = usersRes.data.filter(user => 
          !['ADMIN', 'ADMINISTRATIVO'].includes(user.role)
        );

        setUsers(filteredUsers);
        setCompanies([companiesRes.data]); // Set as array with single company
        setVehicles(vehiclesRes.data);
        setRoutes(routesRes.data);

      } catch (err) {
        console.error('Error fetching company data:', {
          status: err.response?.status,
          data: err.response?.data,
          error: err.message
        });
        setError(`Error al cargar datos: ${err.response?.data?.detail || err.message}`);
      }

    } catch (err) {
      console.error('Error in fetchData:', err);
      if (err.response?.status === 401) {
        navigate('/');
      }
      setError(`Error al cargar datos: ${err.response?.data?.detail || err.message}`);
    }
  }, [navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSignOut = async () => {
    try {
      const response = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/logout`, {});
      localStorage.clear();
      sessionStorage.clear();
      if (response.data.logoutUrl) {
        window.location.replace(response.data.logoutUrl);
      } else {
        window.location.replace('/');
      }
    } catch (error) {
      console.warn('Logout error:', error);
      localStorage.clear();
      sessionStorage.clear();
      window.location.replace('/');
    }
  };

  const handleCreateVehicle = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/vehicles/`, 
        { ...vehicleFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateVehicle(false);
      fetchData();
      setVehicleFormData({
        brand: '',
        model: '',
        year: new Date().getFullYear(),
        vehicle_type: '',
        plate_number: '',
        company_number: '',
        vin: '',
        company_id: currentUser.company_id
      });
    } catch (err) {
      setError('Error al crear el vehículo');
    }
  };

  const handleUpdateVehicle = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/vehicles/${editingVehicle.id}`,
        { ...vehicleFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateVehicle(false);
      setEditingVehicle(null);
      fetchData();
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
        fetchData();
      } catch (err) {
        setError('Error al eliminar el vehículo');
      }
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
      fetchData();
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

  const handleCreateRoute = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/routes/`, 
        { ...routeFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateRoute(false);
      fetchData();
      setRouteFormData({
        name: '',
        start_point: '',
        end_point: '',
        intermediate_stops: [],
        departure_time: '',
        estimated_duration: 0,
        repetition_frequency: null,
        repetition_period: null,
        company_id: currentUser.company_id,
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
        { ...routeFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateRoute(false);
      setEditingRoute(null);
      fetchData();
    } catch (err) {
      setError('Error al actualizar la ruta');
    }
  };

  const handleDeleteRoute = async (routeId) => {
    if (window.confirm('¿Está seguro de eliminar esta ruta? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `${process.env.REACT_APP_BACKEND_URL}/routes/${routeId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        fetchData();
      } catch (err) {
        setError('Error al eliminar la ruta');
      }
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
      fetchData();
    } catch (err) {
      setError('Error al actualizar el estado de la ruta');
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

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/users/`, 
        { ...userFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateUser(false);
      fetchData();
      setUserFormData({
        name: '',
        email: '',
        role: '',
        company_id: currentUser.company_id
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear el usuario');
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${process.env.REACT_APP_BACKEND_URL}/users/${editingUser.id}`,
        { ...userFormData, company_id: currentUser.company_id },
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setShowCreateUser(false);
      setEditingUser(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al actualizar el usuario');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('¿Está seguro de eliminar este usuario? Esta acción no se puede deshacer.')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(
          `${process.env.REACT_APP_BACKEND_URL}/users/${userId}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          }
        );
        fetchData();
      } catch (err) {
        setError(err.response?.data?.detail || 'Error al eliminar el usuario');
      }
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
        <h1>Dashboard Administrativo - {companies[0]?.name}</h1>
        <div className="header-buttons">
          <button onClick={handleSignOut} className="sign-out-button">
            Sign Out
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="dashboard-content">
        {/* Company Section */}
        <section className="companies-section">
          <h2>Información de la Empresa</h2>
          {companies[0] && (
            <div className="company-details">
              <p><strong>Nombre:</strong> {companies[0].name}</p>
              <p><strong>NIT:</strong> {companies[0].nit}</p>
              <p><strong>Email:</strong> {companies[0].email}</p>
              <p><strong>Teléfono:</strong> {companies[0].phone}</p>
              <p><strong>Estado:</strong> {companies[0].status}</p>
            </div>
          )}
        </section>

        {/* Users Section */}
        <section className="users-section">
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
                <option value="OPERADOR">Operador</option>
                <option value="CONDUCTOR">Conductor</option>
                <option value="PASAJERO">Pasajero</option>
                <option value="TECNICO">Técnico</option>
                <option value="JEFE_TALLER">Jefe de Taller</option>
              </select>
              <div className="form-buttons">
                <button type="submit">{editingUser ? 'Actualizar' : 'Crear'}</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setShowCreateUser(false);
                    setEditingUser(null);
                    setUserFormData({
                      name: '',
                      email: '',
                      role: '',
                      company_id: currentUser.company_id
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
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
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

          {/* User Details Modal */}
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
                      {companies[0]?.name || '-'}
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
        </section>

        {/* Vehicles Section */}
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
                      company_id: currentUser.company_id
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
                <th>Empresa</th>
                <th>Estado</th>
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
                      {companies[0]?.name || '-'}
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

        {/* Routes Section */}
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

              {/* Vehicle selection */}
              <select
                value={routeFormData.vehicle_id || ''}
                onChange={(e) => setRouteFormData({...routeFormData, vehicle_id: e.target.value || null})}
              >
                <option value="">Seleccionar vehículo (opcional)</option>
                {vehicles
                  .filter(v => v.status === 'ACTIVO')
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
                      company_id: currentUser?.company_id || '',
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
                  <td>{formatLocalDateTime(route.departure_time)}</td>
                  <td>{route.estimated_duration} min</td>
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

          {/* Route Details Modal */}
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
                      {formatLocalDateTime(selectedRoute.departure_time)}
                    </span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Duración:</span>
                    <span className="detail-value">{selectedRoute.estimated_duration} min</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Empresa:</span>
                    <span className="detail-value">
                      {companies[0]?.name || '-'}
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

export default AdministrativosDashboard;