import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireRole?: 'admin' | 'user';
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireAuth = true,
  requireRole 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Показываем загрузку во время проверки авторизации
  if (loading) {
    return (
      <div className="min-h-screen hero-gradient flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Проверка авторизации...</p>
        </div>
      </div>
    );
  }

  // Если требуется авторизация, но пользователь не авторизован
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Если требуется определенная роль
  if (requireRole && user?.role !== requireRole) {
    return (
      <div className="min-h-screen hero-gradient flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-foreground mb-4">
            Доступ запрещен
          </h1>
          <p className="text-muted-foreground mb-6">
            У вас нет прав для доступа к этой странице
          </p>
          <Navigate to="/" replace />
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
