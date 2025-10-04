import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api';

// Типы для авторизации
export interface User {
  user_id: string;
  email: string;
  role: 'admin' | 'user';
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Создаем контекст
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Константы для localStorage
const TOKEN_KEY = 'slide-speaker-auth-token';
const USER_KEY = 'slide-speaker-user';

// Провайдер контекста
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Проверяем, авторизован ли пользователь
  const isAuthenticated = !!user;

  // Инициализация при загрузке
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const savedUser = localStorage.getItem(USER_KEY);

      if (token && savedUser) {
        // Проверяем валидность токена
        try {
          const userData = JSON.parse(savedUser);
          setUser(userData);
          
          // Проверяем, что токен еще действителен
          await apiClient.getCurrentUser();
        } catch (error) {
          // Токен недействителен, очищаем данные
          clearAuthData();
        }
      }
    } catch (error) {
      console.error('Ошибка инициализации авторизации:', error);
      clearAuthData();
    } finally {
      setLoading(false);
    }
  };

  // Очистка данных авторизации
  const clearAuthData = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  };

  // Функция входа
  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      
      const response = await apiClient.login(credentials);
      
      // Сохраняем токен
      localStorage.setItem(TOKEN_KEY, response.access_token);
      
      // Получаем информацию о пользователе
      const userData = await apiClient.getCurrentUser();
      
      // Преобразуем роль в правильный тип
      const user: User = {
        user_id: userData.user_id,
        email: userData.email,
        role: userData.role as 'admin' | 'user'
      };
      
      // Сохраняем данные пользователя
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setUser(user);
      
    } catch (error) {
      console.error('Ошибка входа:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Функция выхода
  const logout = () => {
    clearAuthData();
    // Можно добавить вызов API для инвалидации токена на сервере
  };

  // Обновление данных пользователя
  const refreshUser = async () => {
    try {
      const userData = await apiClient.getCurrentUser();
      
      // Преобразуем роль в правильный тип
      const user: User = {
        user_id: userData.user_id,
        email: userData.email,
        role: userData.role as 'admin' | 'user'
      };
      
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setUser(user);
    } catch (error) {
      console.error('Ошибка обновления данных пользователя:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Хук для использования контекста
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth должен использоваться внутри AuthProvider');
  }
  return context;
};

// Хук для проверки роли пользователя
export const useRole = () => {
  const { user } = useAuth();
  
  return {
    isAdmin: user?.role === 'admin',
    isUser: user?.role === 'user',
    role: user?.role,
  };
};
