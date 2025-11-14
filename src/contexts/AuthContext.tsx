import { createContext, useContext, ReactNode, useEffect } from 'react';
import { useCurrentUser, useLogin, useLogout, useRegister } from '@/hooks/useAuth';

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

export interface RegisterCredentials {
  email: string;
  password: string;
  username?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: ReturnType<typeof useLogin>;
  register: ReturnType<typeof useRegister>;
  logout: ReturnType<typeof useLogout>;
  refreshUser: () => Promise<void>;
}

// Создаем контекст
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Провайдер контекста - теперь использует TanStack Query hooks
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { data: userData, isLoading, error } = useCurrentUser();
  const loginMutation = useLogin();
  const logoutMutation = useLogout();
  const registerMutation = useRegister();

  // Transform API response to User type
  const user: User | null = userData ? {
    user_id: userData.user_id,
    email: userData.email,
    role: userData.role as 'admin' | 'user'
  } : null;

  const isAuthenticated = !!user;
  
  // Debug logging - only log on state changes
  useEffect(() => {
    console.log('[AuthProvider] State changed:', {
      isLoading,
      isAuthenticated,
      user: user?.email,
      hasError: !!error
    });
  }, [isLoading, isAuthenticated, user, error]);

  // Refresh user function for backward compatibility
  const refreshUser = async () => {
    // With TanStack Query, we can just invalidate the query
    // This is handled automatically by the mutations
    console.log('RefreshUser called - handled by TanStack Query');
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    loading: isLoading,
    login: loginMutation,
    register: registerMutation,
    logout: logoutMutation,
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
