import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, seedDemoData } from '../lib/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('erp_token');
    const savedUser = localStorage.getItem('erp_user');
    
    if (token && savedUser) {
      try {
        const response = await authAPI.getMe();
        setUser(response.data);
      } catch {
        localStorage.removeItem('erp_token');
        localStorage.removeItem('erp_user');
      }
    }
    setLoading(false);
  };

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('erp_token', access_token);
    localStorage.setItem('erp_user', JSON.stringify(userData));
    
    // Fetch full user data including company_name
    try {
      const meResponse = await authAPI.getMe();
      setUser(meResponse.data);
      localStorage.setItem('erp_user', JSON.stringify(meResponse.data));
      return meResponse.data;
    } catch {
      setUser(userData);
      return userData;
    }
  };

  const register = async (data) => {
    const response = await authAPI.register(data);
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('erp_token', access_token);
    localStorage.setItem('erp_user', JSON.stringify(userData));
    setUser(userData);
    
    // Seed demo data for new users
    try {
      await seedDemoData();
    } catch {
      // Demo data might already exist
    }
    
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('erp_token');
    localStorage.removeItem('erp_user');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
