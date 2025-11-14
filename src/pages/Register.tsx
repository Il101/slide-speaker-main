import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Brain, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { trackEvent } from '@/lib/analytics';

// Схема валидации с требованиями к паролю
const registerSchema = z.object({
  email: z.string().email('Введите корректный email'),
  username: z.string().min(3, 'Имя пользователя должно содержать минимум 3 символа').optional().or(z.literal('')),
  password: z.string()
    .min(8, 'Пароль должен содержать минимум 8 символов')
    .regex(/[A-Z]/, 'Пароль должен содержать минимум 1 заглавную букву')
    .regex(/[a-z]/, 'Пароль должен содержать минимум 1 строчную букву')
    .regex(/[0-9]/, 'Пароль должен содержать минимум 1 цифру')
    .regex(/[!@#$%^&*(),.?":{}|<>]/, 'Пароль должен содержать минимум 1 спецсимвол'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Пароли не совпадают",
  path: ["confirmPassword"],
});

type RegisterFormData = z.infer<typeof registerSchema>;

// Индикатор силы пароля
const PasswordStrengthIndicator: React.FC<{ password: string }> = ({ password }) => {
  const requirements = [
    { label: 'Минимум 8 символов', test: (p: string) => p.length >= 8 },
    { label: 'Заглавная буква (A-Z)', test: (p: string) => /[A-Z]/.test(p) },
    { label: 'Строчная буква (a-z)', test: (p: string) => /[a-z]/.test(p) },
    { label: 'Цифра (0-9)', test: (p: string) => /[0-9]/.test(p) },
    { label: 'Спецсимвол (!@#$...)', test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
  ];

  const passedCount = requirements.filter(req => req.test(password)).length;
  const strength = passedCount === 0 ? '' : passedCount <= 2 ? 'Слабый' : passedCount <= 4 ? 'Средний' : 'Сильный';
  const strengthColor = passedCount === 0 ? '' : passedCount <= 2 ? 'text-red-500' : passedCount <= 4 ? 'text-yellow-500' : 'text-green-500';

  return (
    <div className="space-y-2 mt-2">
      {password && (
        <div className={`text-sm font-medium ${strengthColor}`}>
          Сила пароля: {strength}
        </div>
      )}
      <div className="space-y-1">
        {requirements.map((req, index) => {
          const passed = req.test(password);
          return (
            <div key={index} className={`flex items-center text-xs ${passed ? 'text-green-600' : 'text-muted-foreground'}`}>
              {passed ? (
                <CheckCircle2 className="h-3 w-3 mr-2" />
              ) : (
                <X className="h-3 w-3 mr-2" />
              )}
              {req.label}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Register: React.FC = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { register: registerUser, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const email = watch('email');
  const password = watch('password');

  // Автозаполнение username из email
  useEffect(() => {
    if (email && email.includes('@')) {
      const usernameFromEmail = email.split('@')[0];
      setValue('username', usernameFromEmail);
    }
  }, [email, setValue]);

  const onSubmit = async (data: RegisterFormData) => {
    try {
      setError(null);
      
      // Register user
      await registerUser.mutateAsync({
        email: data.email,
        password: data.password,
        username: data.username || undefined,
      });
      
      // Auto-login after registration
      await login.mutateAsync({
        email: data.email,
        password: data.password
      });
      
      // Track successful registration
      trackEvent.signup('email');
      
      // Перенаправляем на страницу, с которой пришел пользователь, или на главную
      const from = (location.state as any)?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err: any) {
      // Track registration error
      trackEvent.error({
        errorType: 'RegistrationError',
        errorMessage: err.message || 'Unknown registration error',
        location: 'register_page'
      });
      
      const errorMessage = err.message || 'Произошла ошибка при регистрации';
      
      // Обработка специфичных ошибок от backend
      if (errorMessage.includes('Email already registered')) {
        setError('Этот email уже зарегистрирован. Попробуйте войти или используйте другой email.');
      } else if (errorMessage.includes('Password must')) {
        setError('Пароль не соответствует требованиям безопасности. Проверьте все требования ниже.');
      } else {
        setError(errorMessage);
      }
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
            Создайте аккаунт для доступа к интерактивным лекциям
          </p>
        </div>

        {/* Форма регистрации */}
        <Card className="p-6 card-gradient card-shadow">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email */}
            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                placeholder="example@email.com"
                {...register('email')}
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>

            {/* Username */}
            <div className="space-y-2">
              <Label htmlFor="username">
                Имя пользователя <span className="text-muted-foreground text-xs">(опционально)</span>
              </Label>
              <Input
                id="username"
                type="text"
                placeholder="username"
                {...register('username')}
                className={errors.username ? 'border-red-500' : ''}
              />
              {errors.username && (
                <p className="text-sm text-red-500">{errors.username.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Если не указать, будет использована часть email до @
              </p>
            </div>

            {/* Пароль */}
            <div className="space-y-2">
              <Label htmlFor="password">Пароль *</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Введите пароль"
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
              
              {/* Индикатор силы пароля */}
              {password && <PasswordStrengthIndicator password={password} />}
            </div>

            {/* Подтверждение пароля */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Подтвердите пароль *</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Введите пароль еще раз"
                  {...register('confirmPassword')}
                  className={errors.confirmPassword ? 'border-red-500' : ''}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              {errors.confirmPassword && (
                <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Ошибка */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Кнопка регистрации */}
            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting || registerUser.isPending || login.isPending}
            >
              {isSubmitting || registerUser.isPending || login.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Регистрация...
                </>
              ) : (
                'Зарегистрироваться'
              )}
            </Button>
          </form>

          {/* Ссылка на вход */}
          <div className="mt-6 text-center text-sm">
            <p className="text-muted-foreground">
              Уже есть аккаунт?{' '}
              <Link to="/login" className="text-primary hover:underline font-medium">
                Войти
              </Link>
            </p>
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

export default Register;
