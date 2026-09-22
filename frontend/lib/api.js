/**
 * API Service & Authentication Module
 * Handles all backend communication for AutoGauge
 */

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class AuthError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

// ============================================================================
// TOKEN MANAGEMENT
// ============================================================================

const TokenManager = {
  getToken: () => {
    try {
      return localStorage.getItem('authToken');
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  },

  setToken: (token) => {
    try {
      localStorage.setItem('authToken', token);
    } catch (error) {
      console.error('Error setting token:', error);
    }
  },

  removeToken: () => {
    try {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    } catch (error) {
      console.error('Error removing token:', error);
    }
  },

  getUser: () => {
    try {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    } catch (error) {
      console.error('Error getting user:', error);
      return null;
    }
  },

  setUser: (user) => {
    try {
      localStorage.setItem('user', JSON.stringify(user));
    } catch (error) {
      console.error('Error setting user:', error);
    }
  },

  isAuthenticated: () => {
    return !!TokenManager.getToken();
  },
};

// ============================================================================
// HTTP REQUEST HANDLER
// ============================================================================

const apiCall = async (endpoint, options = {}) => {
  const {
    method = 'GET',
    body = null,
    headers = {},
    includeAuth = true,
  } = options;

  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (includeAuth) {
    const token = TokenManager.getToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  const config = {
    method,
    headers: requestHeaders,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    if (!response.ok) {
      if (response.status === 401) {
        // Unauthorized - clear token and redirect to login
        TokenManager.removeToken();
        window.location.href = '/login';
      }

      const errorData = await response.json().catch(() => ({}));
      throw new AuthError(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      );
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error(`API Error [${method} ${endpoint}]:`, error);
    return {
      success: false,
      error: error.message || 'An error occurred',
      statusCode: error.statusCode,
    };
  }
};

// ============================================================================
// AUTHENTICATION API
// ============================================================================

export const AuthAPI = {
  signup: async (email, password, fullName, phone) => {
    const result = await apiCall('/auth/signup', {
      method: 'POST',
      body: { email, password, full_name: fullName, phone },
      includeAuth: false,
    });

    if (result.success) {
      TokenManager.setToken(result.data.token);
      TokenManager.setUser(result.data.user);
    }

    return result;
  },

  login: async (email, password) => {
    const result = await apiCall('/auth/login', {
      method: 'POST',
      body: { email, password },
      includeAuth: false,
    });

    if (result.success) {
      TokenManager.setToken(result.data.token);
      TokenManager.setUser(result.data.user);
    }

    return result;
  },

  logout: () => {
    TokenManager.removeToken();
    return { success: true };
  },

  refreshToken: async () => {
    return apiCall('/auth/refresh', { method: 'POST' });
  },

  getCurrentUser: async () => {
    return apiCall('/auth/me');
  },

  updateProfile: async (fullName, phone) => {
    const result = await apiCall('/auth/profile', {
      method: 'PUT',
      body: { full_name: fullName, phone },
    });

    if (result.success) {
      TokenManager.setUser(result.data.user);
    }

    return result;
  },

  changePassword: async (currentPassword, newPassword) => {
    return apiCall('/auth/change-password', {
      method: 'POST',
      body: { current_password: currentPassword, new_password: newPassword },
    });
  },
};

// ============================================================================
// ESTIMATION API
// ============================================================================

export const EstimationAPI = {
  startEstimation: async (formData) => {
    const uploadFormData = new FormData();

    // Add photos
    if (formData.photos) {
      formData.photos.forEach((photo, index) => {
        uploadFormData.append(`photo_${index}`, photo);
      });
    }

    // Add vehicle details
    Object.keys(formData).forEach((key) => {
      if (key !== 'photos') {
        uploadFormData.append(key, formData[key]);
      }
    });

    try {
      const token = TokenManager.getToken();
      const response = await fetch(`${API_BASE_URL}/estimations/analyze`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: uploadFormData,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return { success: true, data: await response.json() };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getEstimations: async (limit = 50, offset = 0) => {
    return apiCall(`/estimations?limit=${limit}&offset=${offset}`);
  },

  getEstimation: async (id) => {
    return apiCall(`/estimations/${id}`);
  },

  deleteEstimation: async (id) => {
    return apiCall(`/estimations/${id}`, { method: 'DELETE' });
  },

  getHistory: async (limit = 10) => {
    return apiCall(`/estimations/history?limit=${limit}`);
  },

  getStatistics: async () => {
    return apiCall('/estimations/statistics');
  },

  exportPDF: async (id) => {
    try {
      const token = TokenManager.getToken();
      const response = await fetch(`${API_BASE_URL}/estimations/${id}/export-pdf`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('PDF export failed');

      const blob = await response.blob();
      return { success: true, blob };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },
};

// ============================================================================
// SAVED VEHICLES API
// ============================================================================

export const SavedVehiclesAPI = {
  getSavedVehicles: async () => {
    return apiCall('/saved-vehicles');
  },

  saveVehicle: async (estimationId, vehicleName, notes = '') => {
    return apiCall('/saved-vehicles', {
      method: 'POST',
      body: { estimation_id: estimationId, vehicle_name: vehicleName, notes },
    });
  },

  deleteSavedVehicle: async (id) => {
    return apiCall(`/saved-vehicles/${id}`, { method: 'DELETE' });
  },

  updateSavedVehicle: async (id, notes) => {
    return apiCall(`/saved-vehicles/${id}`, {
      method: 'PUT',
      body: { notes },
    });
  },
};

// ============================================================================
// MARKET DATA API
// ============================================================================

export const MarketAPI = {
  getPriceTrends: async (brand, model) => {
    return apiCall(`/market/trends?brand=${brand}&model=${model}`);
  },

  getComparisonData: async (estimationIds) => {
    return apiCall('/market/compare', {
      method: 'POST',
      body: { estimation_ids: estimationIds },
    });
  },

  getMarketStatistics: async () => {
    return apiCall('/market/statistics');
  },

  getAveragePrices: async (filters) => {
    const params = new URLSearchParams(filters).toString();
    return apiCall(`/market/average-prices?${params}`);
  },
};

// ============================================================================
// UPLOAD API
// ============================================================================

export const UploadAPI = {
  uploadPhotos: async (files) => {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append(`file_${index}`, file);
    });

    try {
      const token = TokenManager.getToken();
      const response = await fetch(`${API_BASE_URL}/upload/photos`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      return { success: true, data: await response.json() };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  deletePhoto: async (photoId) => {
    return apiCall(`/upload/photos/${photoId}`, { method: 'DELETE' });
  },
};

// ============================================================================
// ANALYTICS API
// ============================================================================

export const AnalyticsAPI = {
  trackEvent: async (event, properties = {}) => {
    return apiCall('/analytics/events', {
      method: 'POST',
      body: { event, properties, timestamp: new Date().toISOString() },
    });
  },

  getDashboardMetrics: async () => {
    return apiCall('/analytics/dashboard');
  },

  getUserStats: async () => {
    return apiCall('/analytics/user-stats');
  },
};

// ============================================================================
// ERROR HANDLER
// ============================================================================

export const ErrorHandler = {
  formatError: (error) => {
    if (typeof error === 'string') return error;
    if (error?.message) return error.message;
    if (error?.error) return error.error;
    return 'An unexpected error occurred';
  },

  isNetworkError: (error) => {
    return !navigator.onLine || error?.statusCode === 0;
  },

  isAuthError: (error) => {
    return error?.statusCode === 401 || error?.statusCode === 403;
  },

  isValidationError: (error) => {
    return error?.statusCode === 400;
  },
};

// ============================================================================
// EXPORT ALL APIS
// ============================================================================

export default {
  TokenManager,
  apiCall,
  AuthAPI,
  EstimationAPI,
  SavedVehiclesAPI,
  MarketAPI,
  UploadAPI,
  AnalyticsAPI,
  ErrorHandler,
};