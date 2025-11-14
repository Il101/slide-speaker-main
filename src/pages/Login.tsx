import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Brain, Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { trackEvent } from '@/lib/analytics';

// Схема валидации
const loginSchema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(6, 'Пароль должен содержать минимум 6 символов'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const Login: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setError(null);
      console.log('[Login] Attempting login with:', data.email);
      
      await login.mutateAsync({
        email: data.email,
        password: data.password
      });
      
      console.log('[Login] Login successful, user data should be refetched');
      
      // Track successful login
      trackEvent.login('email');
      
      // Перенаправляем на страницу, с которой пришел пользователь, или на главную
      const from = (location.state as any)?.from?.pathname || '/';
      console.log('[Login] Navigating to:', from);
      navigate(from, { replace: true });
    } catch (err) {
      console.error('[Login] Login failed:', err);
      
      // Track login error
      trackEvent.error({
        errorType: 'LoginError',
        errorMessage: err instanceof Error ? err.message : 'Unknown login error',
        location: 'login_page'
      });
      
      setError(
        err instanceof Error 
          ? err.message 
          : 'Произошла ошибка при входе в систему'
      );
    }
  };

  return (
    <div className="min-h-screen hero-gradient flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Логотип и заголовок */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Brain className="h-12 w-12 text-primary mr-3" />
            <h1 className="text-3xl font-bold text-foreground">
              ИИ-Лектор
            </h1>
          </div>
          <p className="text-muted-foreground">
            Войдите в систему для создания интерактивных лекций
          </p>
        </div>

        {/* Форма входа */}
        <Card className="p-6 card-gradient card-shadow">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@example.com"
                {...register('email')}
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Пароль */}
            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="admin123"
                  {...register('password')}
                  className={errors.password ? 'border-red-500' : ''}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>

            {/* Ошибка */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Кнопка входа */}
            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting || login.isPending}
            >
              {isSubmitting || login.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Вход...
                </>
              ) : (
                'Войти'
              )}
            </Button>

            {/* Кнопки быстрого входа */}
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setValue('email', 'admin@example.com');
                  setValue('password', 'admin123');
                }}
                className="text-xs"
              >
                Админ
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setValue('email', 'user@example.com');
                  setValue('password', 'user123');
                }}
                className="text-xs"
              >
                Пользователь
              </Button>
            </div>
          </form>

          {/* Ссылка на регистрацию */}
          <div className="mt-6 text-center text-sm">
            <p className="text-muted-foreground">
              Нет аккаунта?{' '}
              <Link to="/register" className="text-primary hover:underline font-medium">
                Зарегистрироваться
              </Link>
            </p>
          </div>

          {/* Дополнительная информация */}
          <div className="mt-4 text-center text-sm text-muted-foreground">
            <p>Демо-аккаунты для тестирования:</p>
            <div className="mt-2 space-y-1">
              <p><strong>Администратор:</strong> admin@example.com / admin123</p>
              <p><strong>Пользователь:</strong> user@example.com / user123</p>
            </div>
          </div>
        </Card>

        {/* Ссылка на главную */}
        <div className="text-center mt-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/')}
            className="text-muted-foreground hover:text-foreground"
          >
            ← Вернуться на главную
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Login;
