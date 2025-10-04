import React from 'react';
import { Brain, LogOut, User, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth, useRole } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface NavigationProps {
  showLogo?: boolean;
  showUserInfo?: boolean;
  className?: string;
}

const Navigation: React.FC<NavigationProps> = ({ 
  showLogo = true, 
  showUserInfo = true,
  className = '' 
}) => {
  const { user, logout } = useAuth();
  const { isAdmin } = useRole();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className={`flex items-center justify-between p-4 ${className}`}>
      {/* Логотип */}
      {showLogo && (
        <div className="flex items-center space-x-2">
          <Brain className="h-8 w-8 text-primary" />
          <h1 className="text-xl font-bold text-foreground">
            ИИ-Лектор
          </h1>
        </div>
      )}

      {/* Информация о пользователе и кнопка выхода */}
      {showUserInfo && user && (
        <div className="flex items-center space-x-4">
          {/* Информация о пользователе */}
          <Card className="px-4 py-2 card-gradient">
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  {user.email}
                </span>
              </div>
              {isAdmin && (
                <div className="flex items-center space-x-1">
                  <Shield className="h-4 w-4 text-yellow-500" />
                  <span className="text-xs text-yellow-600 font-medium">
                    Админ
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Кнопка выхода */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="flex items-center space-x-2"
          >
            <LogOut className="h-4 w-4" />
            <span>Выйти</span>
          </Button>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
