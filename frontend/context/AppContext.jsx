/**
 * AutoGauge Global State Management
 * Using React Context & useReducer for state management
 */

import React, { createContext, useReducer, useCallback, useEffect } from 'react';
import { AuthAPI, TokenManager } from './api';

export const AppContext = createContext();

// ============================================================================
// INITIAL STATE
// ============================================================================

const initialState = {
  // Auth
  auth: {
    isAuthenticated: TokenManager.isAuthenticated(),
    user: TokenManager.getUser(),
    token: TokenManager.getToken(),
    loading: false,
    error: null,
  },

  // UI
  ui: {
    sidebarOpen: true,
    theme: 'dark',
    notifications: [],
  },

  // Estimations
  estimations: {
    list: [],
    current: null,
    loading: false,
    error: null,
    hasMore: true,
    page: 0,
  },

  // Saved Vehicles
  savedVehicles: {
    list: [],
    loading: false,
    error: null,
  },

  // Market Data
  market: {
    trends: null,
    statistics: null,
    loading: false,
    error: null,
  },

  // UI State
  modal: {
    isOpen: false,
    type: null,
    data: null,
  },
};

// ============================================================================
// ACTIONS
// ============================================================================

const ACTIONS = {
  // Auth Actions
  AUTH_START: 'AUTH_START',
  AUTH_SUCCESS: 'AUTH_SUCCESS',
  AUTH_ERROR: 'AUTH_ERROR',
  LOGOUT: 'LOGOUT',

  // Estimation Actions
  FETCH_ESTIMATIONS_START: 'FETCH_ESTIMATIONS_START',
  FETCH_ESTIMATIONS_SUCCESS: 'FETCH_ESTIMATIONS_SUCCESS',
  FETCH_ESTIMATIONS_ERROR: 'FETCH_ESTIMATIONS_ERROR',
  ADD_ESTIMATION: 'ADD_ESTIMATION',
  UPDATE_ESTIMATION: 'UPDATE_ESTIMATION',
  DELETE_ESTIMATION: 'DELETE_ESTIMATION',
  CLEAR_ESTIMATIONS: 'CLEAR_ESTIMATIONS',

  // Saved Vehicles Actions
  FETCH_SAVED_VEHICLES_START: 'FETCH_SAVED_VEHICLES_START',
  FETCH_SAVED_VEHICLES_SUCCESS: 'FETCH_SAVED_VEHICLES_SUCCESS',
  FETCH_SAVED_VEHICLES_ERROR: 'FETCH_SAVED_VEHICLES_ERROR',
  ADD_SAVED_VEHICLE: 'ADD_SAVED_VEHICLE',
  REMOVE_SAVED_VEHICLE: 'REMOVE_SAVED_VEHICLE',

  // Market Actions
  FETCH_MARKET_DATA_START: 'FETCH_MARKET_DATA_START',
  FETCH_MARKET_DATA_SUCCESS: 'FETCH_MARKET_DATA_SUCCESS',
  FETCH_MARKET_DATA_ERROR: 'FETCH_MARKET_DATA_ERROR',

  // UI Actions
  TOGGLE_SIDEBAR: 'TOGGLE_SIDEBAR',
  SET_THEME: 'SET_THEME',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  OPEN_MODAL: 'OPEN_MODAL',
  CLOSE_MODAL: 'CLOSE_MODAL',
};

// ============================================================================
// REDUCER
// ============================================================================

const reducer = (state, action) => {
  switch (action.type) {
    // Auth
    case ACTIONS.AUTH_START:
      return {
        ...state,
        auth: { ...state.auth, loading: true, error: null },
      };

    case ACTIONS.AUTH_SUCCESS:
      return {
        ...state,
        auth: {
          isAuthenticated: true,
          user: action.payload.user,
          token: action.payload.token,
          loading: false,
          error: null,
        },
      };

    case ACTIONS.AUTH_ERROR:
      return {
        ...state,
        auth: {
          ...state.auth,
          loading: false,
          error: action.payload,
        },
      };

    case ACTIONS.LOGOUT:
      return {
        ...state,
        auth: {
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: null,
        },
        estimations: initialState.estimations,
        savedVehicles: initialState.savedVehicles,
      };

    // Estimations
    case ACTIONS.FETCH_ESTIMATIONS_START:
      return {
        ...state,
        estimations: { ...state.estimations, loading: true, error: null },
      };

    case ACTIONS.FETCH_ESTIMATIONS_SUCCESS:
      return {
        ...state,
        estimations: {
          list: action.payload.items,
          loading: false,
          error: null,
          hasMore: action.payload.hasMore,
          page: action.payload.page,
        },
      };

    case ACTIONS.FETCH_ESTIMATIONS_ERROR:
      return {
        ...state,
        estimations: {
          ...state.estimations,
          loading: false,
          error: action.payload,
        },
      };

    case ACTIONS.ADD_ESTIMATION:
      return {
        ...state,
        estimations: {
          ...state.estimations,
          list: [action.payload, ...state.estimations.list],
        },
      };

    case ACTIONS.DELETE_ESTIMATION:
      return {
        ...state,
        estimations: {
          ...state.estimations,
          list: state.estimations.list.filter((e) => e.id !== action.payload),
        },
      };

    case ACTIONS.CLEAR_ESTIMATIONS:
      return {
        ...state,
        estimations: initialState.estimations,
      };

    // Saved Vehicles
    case ACTIONS.FETCH_SAVED_VEHICLES_START:
      return {
        ...state,
        savedVehicles: { ...state.savedVehicles, loading: true, error: null },
      };

    case ACTIONS.FETCH_SAVED_VEHICLES_SUCCESS:
      return {
        ...state,
        savedVehicles: {
          list: action.payload,
          loading: false,
          error: null,
        },
      };

    case ACTIONS.ADD_SAVED_VEHICLE:
      return {
        ...state,
        savedVehicles: {
          ...state.savedVehicles,
          list: [action.payload, ...state.savedVehicles.list],
        },
      };

    case ACTIONS.REMOVE_SAVED_VEHICLE:
      return {
        ...state,
        savedVehicles: {
          ...state.savedVehicles,
          list: state.savedVehicles.list.filter((v) => v.id !== action.payload),
        },
      };

    // Market
    case ACTIONS.FETCH_MARKET_DATA_START:
      return {
        ...state,
        market: { ...state.market, loading: true, error: null },
      };

    case ACTIONS.FETCH_MARKET_DATA_SUCCESS:
      return {
        ...state,
        market: {
          trends: action.payload.trends,
          statistics: action.payload.statistics,
          loading: false,
          error: null,
        },
      };

    // UI
    case ACTIONS.TOGGLE_SIDEBAR:
      return {
        ...state,
        ui: { ...state.ui, sidebarOpen: !state.ui.sidebarOpen },
      };

    case ACTIONS.SET_THEME:
      return {
        ...state,
        ui: { ...state.ui, theme: action.payload },
      };

    case ACTIONS.ADD_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: [
            ...state.ui.notifications,
            { id: Date.now(), ...action.payload },
          ],
        },
      };

    case ACTIONS.REMOVE_NOTIFICATION:
      return {
        ...state,
        ui: {
          ...state.ui,
          notifications: state.ui.notifications.filter(
            (n) => n.id !== action.payload
          ),
        },
      };

    case ACTIONS.OPEN_MODAL:
      return {
        ...state,
        modal: {
          isOpen: true,
          type: action.payload.type,
          data: action.payload.data,
        },
      };

    case ACTIONS.CLOSE_MODAL:
      return {
        ...state,
        modal: initialState.modal,
      };

    default:
      return state;
  }
};

// ============================================================================
// PROVIDER COMPONENT
// ============================================================================

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Initialize auth on mount
  useEffect(() => {
    const initAuth = async () => {
      if (state.auth.isAuthenticated && !state.auth.user) {
        const result = await AuthAPI.getCurrentUser();
        if (result.success) {
          dispatch({
            type: ACTIONS.AUTH_SUCCESS,
            payload: {
              user: result.data.user,
              token: TokenManager.getToken(),
            },
          });
        } else {
          dispatch({ type: ACTIONS.LOGOUT });
        }
      }
    };

    initAuth();
  }, []);

  // Action creators
  const authLogin = useCallback(async (email, password) => {
    dispatch({ type: ACTIONS.AUTH_START });
    const result = await AuthAPI.login(email, password);

    if (result.success) {
      dispatch({
        type: ACTIONS.AUTH_SUCCESS,
        payload: {
          user: result.data.user,
          token: result.data.token,
        },
      });
    } else {
      dispatch({
        type: ACTIONS.AUTH_ERROR,
        payload: result.error,
      });
    }

    return result;
  }, []);

  const authSignup = useCallback(async (email, password, fullName, phone) => {
    dispatch({ type: ACTIONS.AUTH_START });
    const result = await AuthAPI.signup(email, password, fullName, phone);

    if (result.success) {
      dispatch({
        type: ACTIONS.AUTH_SUCCESS,
        payload: {
          user: result.data.user,
          token: result.data.token,
        },
      });
    } else {
      dispatch({
        type: ACTIONS.AUTH_ERROR,
        payload: result.error,
      });
    }

    return result;
  }, []);

  const authLogout = useCallback(() => {
    AuthAPI.logout();
    dispatch({ type: ACTIONS.LOGOUT });
  }, []);

  const addNotification = useCallback((type, message, duration = 4000) => {
    const id = Date.now();
    dispatch({
      type: ACTIONS.ADD_NOTIFICATION,
      payload: { id, type, message },
    });

    if (duration) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }

    return id;
  }, []);

  const removeNotification = useCallback((id) => {
    dispatch({
      type: ACTIONS.REMOVE_NOTIFICATION,
      payload: id,
    });
  }, []);

  const openModal = useCallback((modalType, data) => {
    dispatch({
      type: ACTIONS.OPEN_MODAL,
      payload: { type: modalType, data },
    });
  }, []);

  const closeModal = useCallback(() => {
    dispatch({ type: ACTIONS.CLOSE_MODAL });
  }, []);

  const addEstimation = useCallback((estimation) => {
    dispatch({
      type: ACTIONS.ADD_ESTIMATION,
      payload: estimation,
    });
  }, []);

  const deleteEstimation = useCallback((estimationId) => {
    dispatch({
      type: ACTIONS.DELETE_ESTIMATION,
      payload: estimationId,
    });
  }, []);

  const addSavedVehicle = useCallback((vehicle) => {
    dispatch({
      type: ACTIONS.ADD_SAVED_VEHICLE,
      payload: vehicle,
    });
  }, []);

  const removeSavedVehicle = useCallback((vehicleId) => {
    dispatch({
      type: ACTIONS.REMOVE_SAVED_VEHICLE,
      payload: vehicleId,
    });
  }, []);

  const value = {
    state,
    dispatch,
    authLogin,
    authSignup,
    authLogout,
    addNotification,
    removeNotification,
    openModal,
    closeModal,
    addEstimation,
    deleteEstimation,
    addSavedVehicle,
    removeSavedVehicle,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// ============================================================================
// CUSTOM HOOK
// ============================================================================

export const useApp = () => {
  const context = React.useContext(AppContext);

  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }

  return context;
};

export default { AppContext, AppProvider, useApp };
