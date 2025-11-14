# 🔄 Улучшения Системы Подписок

**Дата создания:** 12 ноября 2025  
**Приоритет:** КРИТИЧЕСКИЙ  
**Статус:** Планируется

---

## 📋 Оглавление

- [Критичные улучшения (СРОЧНО)](#критичные-улучшения-срочно)
- [Важные улучшения (Неделя)](#важные-улучшения-неделя)
- [Желательные улучшения (Месяц)](#желательные-улучшения-месяц)
- [Юридические требования](#юридические-требования)
- [Детальная реализация](#детальная-реализация)

---

## 🔴 Критичные улучшения (СРОЧНО)

### 1. ❌ Отмена Подписки (Cancel Subscription)

**Проблема:** Пользователь НЕ может отменить подписку через приложение. Это нарушает законы многих стран и требования Stripe.

**Решение:**

#### Backend: `backend/app/api/subscriptions.py`

```python
@router.post("/cancel")
async def cancel_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Cancel user's subscription
    Cancels at period end to not cut off immediately
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has paid subscription
        if user.subscription_tier == 'free':
            raise HTTPException(status_code=400, detail="No active subscription to cancel")
        
        # If Stripe is configured, cancel subscription in Stripe
        if STRIPE_ENABLED:
            # Get user's Stripe subscription
            # Note: You need to store stripe_subscription_id in User model
            if hasattr(user, 'stripe_subscription_id') and user.stripe_subscription_id:
                # Cancel at period end (don't cut off immediately)
                stripe.Subscription.modify(
                    user.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                
                logger.info(f"User {user_id} cancelled subscription (will end at period end)")
                
                return {
                    "success": True,
                    "message": "Subscription will be cancelled at the end of billing period",
                    "cancelled_at_period_end": True,
                    "current_period_end": None  # Get from Stripe subscription object
                }
        
        # If no Stripe or no subscription_id, just downgrade to free immediately
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                subscription_tier='free',
                subscription_expires_at=datetime.utcnow()
            )
        )
        await db.commit()
        
        logger.info(f"User {user_id} downgraded to free tier")
        
        return {
            "success": True,
            "message": "Downgraded to free tier",
            "new_tier": "free"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reactivate")
async def reactivate_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Reactivate cancelled subscription (before period ends)
    """
    try:
        user_id = current_user["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if STRIPE_ENABLED and hasattr(user, 'stripe_subscription_id') and user.stripe_subscription_id:
            # Remove cancel_at_period_end flag
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            logger.info(f"User {user_id} reactivated subscription")
            
            return {
                "success": True,
                "message": "Subscription reactivated successfully"
            }
        
        raise HTTPException(status_code=400, detail="No cancelled subscription found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Frontend: `src/components/SubscriptionManager.tsx`

```tsx
const [isCancelling, setIsCancelling] = useState(false);
const [showCancelDialog, setShowCancelDialog] = useState(false);

const handleCancelSubscription = async () => {
  if (!window.confirm(
    'Вы уверены, что хотите отменить подписку?\n\n' +
    'Вы сохраните доступ до конца текущего платежного периода.'
  )) {
    return;
  }
  
  try {
    setIsCancelling(true);
    
    const response = await fetch('/api/subscription/cancel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...apiClient.getAuthHeaders(),
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to cancel subscription');
    }
    
    const data = await response.json();
    
    toast({
      title: 'Подписка отменена',
      description: data.message,
    });
    
    // Reload subscription info
    await loadSubscription();
    
  } catch (error) {
    console.error('Cancel error:', error);
    toast({
      title: 'Ошибка',
      description: 'Не удалось отменить подписку',
      variant: 'destructive',
    });
  } finally {
    setIsCancelling(false);
  }
};

// В JSX добавить кнопку:
{tier !== 'free' && (
  <div className="mt-4 pt-4 border-t">
    <Button 
      variant="outline" 
      onClick={handleCancelSubscription}
      disabled={isCancelling}
      className="w-full text-red-600 border-red-300 hover:bg-red-50"
    >
      {isCancelling ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Отмена...
        </>
      ) : (
        <>
          <X className="mr-2 h-4 w-4" />
          Отменить подписку
        </>
      )}
    </Button>
    <p className="text-xs text-muted-foreground mt-2 text-center">
      Доступ сохранится до конца платежного периода
    </p>
  </div>
)}
```

#### Необходимые изменения в модели User:

```python
# backend/app/core/database.py

class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    # ... existing fields ...
    
    # Добавить новые поля для интеграции со Stripe:
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    subscription_cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

#### Миграция:

```python
# backend/alembic/versions/008_add_stripe_fields.py

def upgrade() -> None:
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('subscription_cancelled_at', sa.DateTime(), nullable=True))
    
    # Create indexes for faster lookups
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'])
    op.create_index('ix_users_stripe_subscription_id', 'users', ['stripe_subscription_id'])

def downgrade() -> None:
    op.drop_index('ix_users_stripe_subscription_id', 'users')
    op.drop_index('ix_users_stripe_customer_id', 'users')
    op.drop_column('users', 'subscription_cancelled_at')
    op.drop_column('users', 'subscription_expires_at')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_customer_id')
```

**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Время:** 2-3 часа  
**Зависимости:** Миграция БД

---

### 2. ❌ Stripe Customer Portal

**Проблема:** Пользователь не может:
- Управлять платежными методами
- Скачивать инвойсы
- Видеть историю платежей
- Обновлять данные карты

**Решение:** Stripe Customer Portal - готовое решение от Stripe!

#### Backend: `backend/app/api/subscriptions.py`

```python
@router.post("/create-portal-session")
async def create_portal_session(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Create Stripe Customer Portal session
    
    Allows users to:
    - Update payment methods
    - View invoices
    - Cancel subscription
    - Update billing information
    """
    if not STRIPE_ENABLED:
        raise HTTPException(
            status_code=503, 
            detail="Stripe not configured. Please contact support."
        )
    
    try:
        user_id = current_user["user_id"]
        
        # Get user's stripe_customer_id from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has Stripe customer ID
        if not hasattr(user, 'stripe_customer_id') or not user.stripe_customer_id:
            raise HTTPException(
                status_code=400, 
                detail="No active subscription found. Please subscribe first."
            )
        
        # Create Stripe Customer Portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/subscription",
        )
        
        logger.info(f"Created portal session for user {user_id}")
        
        return {
            "url": portal_session.url
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Payment system error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Frontend: `src/components/SubscriptionManager.tsx`

```tsx
const handleManageBilling = async () => {
  try {
    setIsLoading(true);
    
    const response = await fetch('/api/subscription/create-portal-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...apiClient.getAuthHeaders(),
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to create portal session');
    }
    
    const data = await response.json();
    
    // Redirect to Stripe Customer Portal
    window.location.href = data.url;
    
  } catch (error) {
    console.error('Portal error:', error);
    toast({
      title: 'Ошибка',
      description: 'Не удалось открыть портал управления',
      variant: 'destructive',
    });
  } finally {
    setIsLoading(false);
  }
};

// В JSX добавить кнопку:
{tier !== 'free' && (
  <Card className="mt-4">
    <CardHeader>
      <CardTitle className="text-lg">Управление подпиской</CardTitle>
      <CardDescription>
        Управляйте платежными методами, скачивайте инвойсы
      </CardDescription>
    </CardHeader>
    <CardContent>
      <Button 
        onClick={handleManageBilling}
        disabled={isLoading}
        className="w-full"
      >
        <CreditCard className="mr-2 h-4 w-4" />
        Управление платежами
      </Button>
    </CardContent>
  </Card>
)}
```

**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Время:** 1 час  
**Зависимости:** stripe_customer_id в User модели

---

### 3. ❌ Privacy Policy & Terms of Service

**Проблема:** Отсутствуют обязательные юридические документы.

**Решение:**

#### Создать страницы:

```tsx
// src/pages/PrivacyPolicy.tsx

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const PrivacyPolicy: React.FC = () => {
  return (
    <div className="container max-w-4xl py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">Политика Конфиденциальности</CardTitle>
          <p className="text-muted-foreground">Последнее обновление: 12 ноября 2025</p>
        </CardHeader>
        <CardContent className="prose max-w-none">
          <h2>1. Сбор Информации</h2>
          <p>
            Мы собираем следующую информацию:
          </p>
          <ul>
            <li><strong>Информация аккаунта:</strong> Email, имя пользователя, пароль (хешированный)</li>
            <li><strong>Платежная информация:</strong> Обрабатывается через Stripe (мы не храним данные карт)</li>
            <li><strong>Контент:</strong> Загруженные презентации и созданные видео</li>
            <li><strong>Использование:</strong> Логи API запросов, аналитика использования</li>
          </ul>

          <h2>2. Использование Данных</h2>
          <p>Мы используем ваши данные для:</p>
          <ul>
            <li>Предоставления и улучшения наших услуг</li>
            <li>Обработки платежей и управления подписками</li>
            <li>Отправки важных уведомлений о сервисе</li>
            <li>Соблюдения юридических обязательств</li>
          </ul>

          <h2>3. Защита Данных</h2>
          <p>Мы применяем следующие меры безопасности:</p>
          <ul>
            <li>Bcrypt хеширование паролей</li>
            <li>HTTPS шифрование всех передач данных</li>
            <li>Защищенное хранилище файлов (MinIO)</li>
            <li>Регулярное резервное копирование</li>
          </ul>

          <h2>4. Ваши Права (GDPR)</h2>
          <p>Вы имеете право на:</p>
          <ul>
            <li><strong>Доступ:</strong> Получить копию ваших данных</li>
            <li><strong>Исправление:</strong> Обновить неточные данные</li>
            <li><strong>Удаление:</strong> Запросить удаление вашего аккаунта</li>
            <li><strong>Экспорт:</strong> Получить все ваши данные в машиночитаемом формате</li>
          </ul>

          <h2>5. Cookies</h2>
          <p>
            Мы используем cookies для:
          </p>
          <ul>
            <li>Аутентификации (HttpOnly cookies для JWT токенов)</li>
            <li>Аналитики (анонимизированные данные)</li>
          </ul>

          <h2>6. Третьи Стороны</h2>
          <p>Мы работаем с:</p>
          <ul>
            <li><strong>Stripe:</strong> Обработка платежей</li>
            <li><strong>Google Cloud:</strong> Обработка документов и TTS</li>
            <li><strong>Хостинг:</strong> Railway/Netlify для инфраструктуры</li>
          </ul>

          <h2>7. Хранение Данных</h2>
          <p>
            Мы храним ваши данные до тех пор, пока ваш аккаунт активен.
            После удаления аккаунта данные удаляются в течение 30 дней.
          </p>

          <h2>8. Контакты</h2>
          <p>
            По вопросам конфиденциальности: <a href="mailto:privacy@slidespeaker.com">privacy@slidespeaker.com</a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
```

```tsx
// src/pages/TermsOfService.tsx

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export const TermsOfService: React.FC = () => {
  return (
    <div className="container max-w-4xl py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">Условия Использования</CardTitle>
          <p className="text-muted-foreground">Последнее обновление: 12 ноября 2025</p>
        </CardHeader>
        <CardContent className="prose max-w-none">
          <h2>1. Принятие Условий</h2>
          <p>
            Используя Slide Speaker, вы соглашаетесь с этими условиями.
            Если вы не согласны, пожалуйста, не используйте наш сервис.
          </p>

          <h2>2. Описание Сервиса</h2>
          <p>
            Slide Speaker предоставляет:
          </p>
          <ul>
            <li>Конвертацию презентаций в видео с AI озвучкой</li>
            <li>Генерацию speaker notes</li>
            <li>Экспорт в различных форматах</li>
          </ul>

          <h2>3. Учетная Запись</h2>
          <p>Вы обязаны:</p>
          <ul>
            <li>Предоставить точную информацию при регистрации</li>
            <li>Сохранять конфиденциальность пароля</li>
            <li>Уведомлять нас о несанкционированном доступе</li>
          </ul>

          <h2>4. Подписка и Платежи</h2>
          <ul>
            <li>Подписки оплачиваются ежемесячно или ежегодно</li>
            <li>Автоматическое продление если не отменено</li>
            <li>Возврат средств в течение 14 дней с момента покупки</li>
            <li>Цены могут изменяться с уведомлением за 30 дней</li>
          </ul>

          <h2>5. Использование Контента</h2>
          <p>Вы не можете:</p>
          <ul>
            <li>Загружать контент, нарушающий авторские права</li>
            <li>Использовать сервис для нелегальных целей</li>
            <li>Передавать вредоносное ПО</li>
            <li>Перепродавать доступ к сервису</li>
          </ul>

          <h2>6. Интеллектуальная Собственность</h2>
          <ul>
            <li>Вы сохраняете права на загруженный контент</li>
            <li>Мы сохраняем права на созданное AI содержимое</li>
            <li>Вы получаете лицензию на использование сгенерированных видео</li>
          </ul>

          <h2>7. Ограничения Использования</h2>
          <p>
            Лимиты определяются вашим тарифным планом:
          </p>
          <ul>
            <li>Free: 3 презентации/месяц, до 10 слайдов</li>
            <li>Pro: 50 презентаций/месяц, до 100 слайдов</li>
            <li>Enterprise: Неограниченно</li>
          </ul>

          <h2>8. Отказ от Гарантий</h2>
          <p>
            Сервис предоставляется "как есть". Мы не гарантируем:
          </p>
          <ul>
            <li>Бесперебойную работу 100% времени</li>
            <li>Идеальное качество AI генерации</li>
            <li>Совместимость со всеми форматами файлов</li>
          </ul>

          <h2>9. Ограничение Ответственности</h2>
          <p>
            Мы не несем ответственности за:
          </p>
          <ul>
            <li>Потерю данных из-за технических проблем</li>
            <li>Косвенные убытки от использования сервиса</li>
            <li>Контент, созданный другими пользователями</li>
          </ul>

          <h2>10. Прекращение Использования</h2>
          <p>
            Мы можем приостановить или удалить ваш аккаунт:
          </p>
          <ul>
            <li>При нарушении этих условий</li>
            <li>При неоплате подписки</li>
            <li>По вашему запросу</li>
          </ul>

          <h2>11. Изменения Условий</h2>
          <p>
            Мы можем изменять эти условия. Существенные изменения
            вступают в силу через 30 дней после уведомления.
          </p>

          <h2>12. Контакты</h2>
          <p>
            По вопросам условий: <a href="mailto:legal@slidespeaker.com">legal@slidespeaker.com</a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
```

#### Добавить роуты:

```tsx
// src/App.tsx

import { PrivacyPolicy } from '@/pages/PrivacyPolicy';
import { TermsOfService } from '@/pages/TermsOfService';

// В роутинге:
<Route path="/privacy" element={<PrivacyPolicy />} />
<Route path="/terms" element={<TermsOfService />} />
```

#### Добавить ссылки в Footer:

```tsx
// src/components/Footer.tsx

export const Footer: React.FC = () => {
  return (
    <footer className="border-t mt-auto">
      <div className="container py-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © 2025 Slide Speaker. All rights reserved.
          </p>
          <div className="flex gap-4">
            <a href="/privacy" className="text-sm text-muted-foreground hover:text-foreground">
              Privacy Policy
            </a>
            <a href="/terms" className="text-sm text-muted-foreground hover:text-foreground">
              Terms of Service
            </a>
            <a href="mailto:support@slidespeaker.com" className="text-sm text-muted-foreground hover:text-foreground">
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
```

**Приоритет:** 🔴 КРИТИЧЕСКИЙ  
**Время:** 2-3 часа  
**Зависимости:** Нет

---

## 🟡 Важные улучшения (Неделя)

### 4. Email Уведомления

**Что реализовать:**

```python
# backend/app/services/email_service.py

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

class EmailService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@slidespeaker.com')
    
    async def send_payment_success(self, user_email: str, amount: float, plan: str):
        """Send payment confirmation"""
        message = Mail(
            from_email=self.from_email,
            to_emails=user_email,
            subject='Payment Successful - Slide Speaker',
            html_content=f'''
                <h1>Payment Confirmed!</h1>
                <p>Thank you for subscribing to {plan} plan.</p>
                <p>Amount: ${amount}</p>
                <p>You now have access to all {plan} features.</p>
            '''
        )
        await self.sg.send(message)
    
    async def send_subscription_ending(self, user_email: str, days_left: int):
        """Send subscription ending reminder"""
        message = Mail(
            from_email=self.from_email,
            to_emails=user_email,
            subject=f'Your subscription ends in {days_left} days',
            html_content=f'''
                <h1>Subscription Ending Soon</h1>
                <p>Your subscription will end in {days_left} days.</p>
                <p>Renew now to keep your access.</p>
            '''
        )
        await self.sg.send(message)
    
    async def send_payment_failed(self, user_email: str):
        """Send payment failed notification"""
        pass
    
    async def send_subscription_cancelled(self, user_email: str, end_date: str):
        """Send cancellation confirmation"""
        pass
```

**Интеграция в webhook:**

```python
# В webhook при успешном платеже:
if event_type == "checkout.session.completed":
    # ... existing code ...
    
    # Send confirmation email
    email_service = EmailService()
    await email_service.send_payment_success(
        user_email=current_user.get("email"),
        amount=plan.get("price_monthly"),
        plan=tier
    )
```

**Приоритет:** 🟡 ВАЖНО  
**Время:** 4-6 часов  
**Зависимости:** SendGrid/Mailgun аккаунт

---

### 5. История Платежей и Инвойсы

```python
@router.get("/invoices")
async def get_user_invoices(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20
) -> List[Dict]:
    """Get user's payment invoices from Stripe"""
    if not STRIPE_ENABLED:
        return []
    
    try:
        user_id = current_user["user_id"]
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user or not hasattr(user, 'stripe_customer_id') or not user.stripe_customer_id:
            return []
        
        # Get invoices from Stripe
        invoices = stripe.Invoice.list(
            customer=user.stripe_customer_id,
            limit=limit
        )
        
        return [{
            "id": inv.id,
            "date": inv.created,
            "amount": inv.amount_paid / 100,  # Convert from cents
            "currency": inv.currency.upper(),
            "status": inv.status,
            "invoice_pdf": inv.invoice_pdf,
            "hosted_invoice_url": inv.hosted_invoice_url,
            "description": inv.lines.data[0].description if inv.lines.data else None
        } for inv in invoices.data]
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error fetching invoices: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        return []
```

**Frontend компонент:**

```tsx
// src/components/InvoiceHistory.tsx

export const InvoiceHistory: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      const response = await fetch('/api/subscription/invoices', {
        headers: apiClient.getAuthHeaders(),
      });
      const data = await response.json();
      setInvoices(data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>История платежей</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Loader2 className="animate-spin" />
        ) : invoices.length === 0 ? (
          <p className="text-muted-foreground">Нет платежей</p>
        ) : (
          <div className="space-y-2">
            {invoices.map((invoice) => (
              <div key={invoice.id} className="flex justify-between items-center p-3 border rounded">
                <div>
                  <p className="font-medium">
                    {new Date(invoice.date * 1000).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {invoice.description}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">
                    ${invoice.amount.toFixed(2)} {invoice.currency}
                  </p>
                  <a 
                    href={invoice.invoice_pdf} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Скачать PDF
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

**Приоритет:** 🟡 ВАЖНО  
**Время:** 2-3 часа  
**Зависимости:** stripe_customer_id

---

### 6. Экспорт Данных (GDPR)

```python
@router.get("/export-data")
async def export_user_data(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export all user data (GDPR Article 20 - Right to Data Portability)
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user info
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        
        # Get lessons
        lessons_result = await db.execute(
            select(Lesson).where(Lesson.user_id == user_id)
        )
        lessons = lessons_result.scalars().all()
        
        # Get exports
        exports_result = await db.execute(
            select(Export).where(Export.user_id == user_id)
        )
        exports = exports_result.scalars().all()
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "subscription_tier": user.subscription_tier,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            },
            "lessons": [{
                "id": l.id,
                "title": l.title,
                "description": l.description,
                "status": l.status,
                "slides_count": l.slides_count,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "completed_at": l.completed_at.isoformat() if l.completed_at else None
            } for l in lessons],
            "exports": [{
                "id": e.id,
                "lesson_id": e.lesson_id,
                "status": e.status,
                "quality": e.quality,
                "created_at": e.created_at.isoformat() if e.created_at else None
            } for e in exports],
            "statistics": {
                "total_lessons": len(lessons),
                "total_exports": len(exports),
                "completed_lessons": len([l for l in lessons if l.status == 'completed'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error exporting user data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Приоритет:** 🟡 ВАЖНО  
**Время:** 2 часа  
**Зависимости:** Нет

---

### 7. Удаление Аккаунта

```python
@router.delete("/account")
async def delete_account(
    password: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Permanently delete user account and all associated data (GDPR Right to Erasure)
    
    Warning: This action is irreversible!
    """
    try:
        user_id = current_user["user_id"]
        
        # Get user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password for security
        from ..core.auth import AuthManager
        if not AuthManager.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=403, detail="Invalid password")
        
        # 1. Cancel Stripe subscription if exists
        if STRIPE_ENABLED and hasattr(user, 'stripe_subscription_id') and user.stripe_subscription_id:
            try:
                stripe.Subscription.delete(user.stripe_subscription_id)
                logger.info(f"Cancelled Stripe subscription for user {user_id}")
            except stripe.error.StripeError as e:
                logger.warning(f"Failed to cancel Stripe subscription: {e}")
        
        # 2. Delete user's lessons and associated files
        lessons_result = await db.execute(
            select(Lesson).where(Lesson.user_id == user_id)
        )
        lessons = lessons_result.scalars().all()
        
        # TODO: Delete actual files from storage (MinIO/S3)
        for lesson in lessons:
            await db.delete(lesson)
        
        # 3. Delete user's exports
        await db.execute(
            delete(Export).where(Export.user_id == user_id)
        )
        
        # 4. Delete user
        await db.delete(user)
        
        # 5. Commit all deletions
        await db.commit()
        
        logger.info(f"User {user_id} account permanently deleted")
        
        return {
            "message": "Account deleted successfully",
            "deleted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

**Frontend:**

```tsx
const DeleteAccountDialog: React.FC = () => {
  const [password, setPassword] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!window.confirm(
      'ВНИМАНИЕ: Это действие необратимо!\n\n' +
      'Будут удалены:\n' +
      '- Ваш аккаунт\n' +
      '- Все презентации\n' +
      '- Все экспорты\n' +
      '- Подписка будет отменена\n\n' +
      'Вы уверены?'
    )) {
      return;
    }

    try {
      setIsDeleting(true);

      const response = await fetch('/api/subscription/account', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          ...apiClient.getAuthHeaders(),
        },
        body: JSON.stringify({ password }),
      });

      if (!response.ok) {
        throw new Error('Failed to delete account');
      }

      toast({
        title: 'Аккаунт удален',
        description: 'Ваш аккаунт и все данные удалены',
      });

      // Logout and redirect
      await apiClient.logout();
      window.location.href = '/';

    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось удалить аккаунт',
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Card className="border-red-200">
      <CardHeader>
        <CardTitle className="text-red-600">Опасная зона</CardTitle>
        <CardDescription>
          Удаление аккаунта необратимо
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Input
            type="password"
            placeholder="Введите пароль для подтверждения"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={!password || isDeleting}
            className="w-full"
          >
            {isDeleting ? 'Удаление...' : 'Удалить аккаунт навсегда'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
```

**Приоритет:** 🟡 ВАЖНО  
**Время:** 3-4 часа  
**Зависимости:** Нет

---

## 🟢 Желательные улучшения (Месяц)

### 8. Триал Период

```python
# При создании checkout session:
checkout_session = stripe.checkout.Session.create(
    customer_email=current_user.get("email"),
    mode="subscription",
    subscription_data={
        "trial_period_days": 14  # 14 дней бесплатного триала
    },
    line_items=[{
        "price": price_id,
        "quantity": 1,
    }],
    # ... rest
)
```

**Приоритет:** 🟢 ЖЕЛАТЕЛЬНО  
**Время:** 1-2 часа

---

### 9. Понижение Плана (Downgrade)

```python
@router.post("/downgrade")
async def downgrade_subscription(
    downgrade_request: DowngradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Downgrade to lower tier (immediate or at period end)"""
    # Implement downgrade logic
    pass
```

**Приоритет:** 🟢 ЖЕЛАТЕЛЬНО  
**Время:** 2-3 часа

---

### 10. Промокоды

```python
@router.post("/apply-coupon")
async def apply_coupon(
    coupon_code: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Apply discount coupon"""
    # Use Stripe Coupons API
    pass
```

**Приоритет:** 🟢 ЖЕЛАТЕЛЬНО  
**Время:** 3-4 часа

---

## 📝 Юридические Требования

### Обязательные документы:

- [x] ~~Политика конфиденциальности (Privacy Policy)~~
- [x] ~~Условия использования (Terms of Service)~~
- [ ] Политика возврата (Refund Policy)
- [ ] Cookie Policy

### GDPR Compliance:

- [x] ~~Право на доступ к данным (Data Export)~~
- [x] ~~Право на удаление (Delete Account)~~
- [ ] Право на исправление
- [ ] Прозрачность обработки данных
- [ ] Cookie consent banner

### CCPA Compliance (California):

- [ ] "Do Not Sell My Personal Information" ссылка
- [ ] Раскрытие категорий собираемых данных

---

## 🎯 План Реализации

### Неделя 1 (КРИТИЧНО):
1. ✅ Отмена подписки - 3 часа
2. ✅ Stripe Customer Portal - 1 час
3. ✅ Privacy Policy & Terms - 3 часа
4. ✅ Миграция БД (stripe_customer_id) - 1 час

**Итого:** ~8 часов

### Неделя 2 (ВАЖНО):
5. ✅ Email уведомления - 6 часов
6. ✅ История платежей - 3 часа
7. ✅ Экспорт данных - 2 часа
8. ✅ Удаление аккаунта - 4 часа

**Итого:** ~15 часов

### Неделя 3-4 (ЖЕЛАТЕЛЬНО):
9. Триал период - 2 часа
10. Downgrade функционал - 3 часа
11. Промокоды - 4 часа
12. Refund Policy - 2 часа

**Итого:** ~11 часов

---

## ⚠️ Важные Замечания

1. **Stripe Customer Portal** решает 80% проблем управления подпиской!
2. Без **отмены подписки** продукт незаконен во многих странах
3. **Privacy Policy** обязательна для GDPR и Stripe
4. **Email уведомления** критичны для пользовательского опыта
5. **Экспорт/удаление данных** - требование GDPR

---

## 📞 Контакты

По вопросам реализации: developer@slidespeaker.com

---

**Статус:** 📝 Планируется  
**Последнее обновление:** 12 ноября 2025
