import React, { useState } from 'react';
import { Menu, X, Crown, LogOut, User, Shield, Brain, ListVideo } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { useAuth, useRole } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Separator } from '@/components/ui/separator';

export const MobileNav: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const { isAdmin } = useRole();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate('/');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    setOpen(false);
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button 
          variant="ghost" 
          size="icon" 
          className="md:hidden"
          aria-label="Открыть меню"
        >
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[300px] sm:w-[350px]">
        <SheetHeader className="text-left">
          <SheetTitle className="flex items-center space-x-2">
            <Brain className="h-6 w-6 text-primary" />
            <span>ИИ-Лектор</span>
          </SheetTitle>
        </SheetHeader>
        
        <nav className="flex flex-col space-y-4 mt-8">
          {user && (
            <>
              {/* Информация о пользователе */}
              <div className="space-y-2 p-4 rounded-lg bg-muted">
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{user.email}</span>
                </div>
                {isAdmin && (
                  <div className="flex items-center space-x-2">
                    <Shield className="h-4 w-4 text-yellow-500" />
                    <span className="text-xs text-yellow-600 font-medium">
                      Администратор
                    </span>
                  </div>
                )}
              </div>

              <Separator />

              {/* Навигационные кнопки */}
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleNavigation('/')}
              >
                <Brain className="mr-2 h-4 w-4" />
                Главная
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleNavigation('/playlists')}
              >
                <ListVideo className="mr-2 h-4 w-4" />
                Плейлисты
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleNavigation('/subscription')}
              >
                <Crown className="mr-2 h-4 w-4 text-yellow-500" />
                Подписка
              </Button>

              <Separator />

              {/* Кнопка выхода */}
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Выйти
              </Button>
            </>
          )}

          {!user && (
            <>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => handleNavigation('/')}
              >
                <Brain className="mr-2 h-4 w-4" />
                Главная
              </Button>

              <Button
                variant="default"
                className="w-full justify-start"
                onClick={() => handleNavigation('/login')}
              >
                Войти
              </Button>
            </>
          )}
        </nav>
      </SheetContent>
    </Sheet>
  );
};
