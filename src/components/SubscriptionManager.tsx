/**
 * Subscription Manager Component
 * 
 * Displays current subscription plan and allows upgrades
 */
import React, { useState, useEffect } from 'react';
import { Crown, Check, X, Loader2, Zap, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api';

interface SubscriptionPlan {
  name: string;
  presentations_per_month: number;
  max_slides: number;
  max_file_size_mb: number;
  ai_quality: string;
  export_formats: string[];
  priority: string;
  custom_voices: boolean;
  api_access: boolean;
  features: string[];
  price_monthly?: number;
}

interface SubscriptionInfo {
  user_id: string;
  tier: 'free' | 'pro' | 'enterprise';
  plan: SubscriptionPlan;
  usage: {
    presentations_this_month: number;
    current_concurrent: number;
  };
  expires_at?: string | null;
}

const tierColors = {
  free: 'bg-gray-100 text-gray-800 border-gray-300',
  pro: 'bg-blue-100 text-blue-800 border-blue-300',
  enterprise: 'bg-purple-100 text-purple-800 border-purple-300',
};

const getTierIcon = (tier: string) => {
  switch (tier) {
    case 'free':
      return <Zap className="h-5 w-5" />;
    case 'pro':
      return <TrendingUp className="h-5 w-5" />;
    case 'enterprise':
      return <Crown className="h-5 w-5" />;
    default:
      return <Zap className="h-5 w-5" />;
  }
};

export const SubscriptionManager: React.FC = () => {
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [allPlans, setAllPlans] = useState<Record<string, SubscriptionPlan> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { toast } = useToast();

  useEffect(() => {
    loadSubscription();
    loadAllPlans();
  }, []);

  const loadSubscription = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('/api/subscription/info', {
        headers: {
          ...apiClient.getAuthHeaders(),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load subscription');
      }

      const data = await response.json();
      setSubscription(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load subscription');
    } finally {
      setIsLoading(false);
    }
  };

  const loadAllPlans = async () => {
    try {
      const response = await fetch('/api/subscription/plans');
      if (response.ok) {
        const data = await response.json();
        setAllPlans(data);
      }
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  };

  const handleUpgrade = async (targetTier: string) => {
    try {
      setIsLoading(true);

      // First, try to create a Stripe checkout session
      const checkoutResponse = await fetch('/api/subscription/create-checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...apiClient.getAuthHeaders(),
        },
        body: JSON.stringify({ tier: targetTier }),
      });

      if (!checkoutResponse.ok) {
        throw new Error('Failed to create checkout session');
      }

      const checkoutData = await checkoutResponse.json();

      // If Stripe is configured, redirect to checkout
      if (checkoutData.session_url) {
        window.location.href = checkoutData.session_url;
        return;
      }

      // If Stripe is not configured, show message
      if (checkoutData.message) {
        toast({
          title: 'Платежная система не настроена',
          description: checkoutData.message,
          variant: 'default',
        });

        // For testing/demo purposes, allow direct upgrade
        // In production, remove this block
        const confirmUpgrade = window.confirm(
          `Демо-режим: Вы хотите обновить подписку до ${targetTier}?\n\n` +
          'В продакшене это будет доступно только после оплаты через Stripe.'
        );

        if (confirmUpgrade) {
          const upgradeResponse = await fetch('/api/subscription/upgrade', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...apiClient.getAuthHeaders(),
            },
            body: JSON.stringify({ tier: targetTier }),
          });

          if (!upgradeResponse.ok) {
            throw new Error('Failed to upgrade subscription');
          }

          const upgradeData = await upgradeResponse.json();

          toast({
            title: 'Подписка обновлена!',
            description: upgradeData.message,
          });

          // Reload subscription info
          await loadSubscription();
        }
      }
    } catch (err) {
      console.error('Upgrade error:', err);
      toast({
        title: 'Ошибка',
        description: err instanceof Error ? err.message : 'Не удалось обновить подписку',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !subscription) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error || 'Не удалось загрузить информацию о подписке'}</AlertDescription>
      </Alert>
    );
  }

  const { tier, plan, usage } = subscription;
  const usagePercent = plan.presentations_per_month === -1
    ? 0
    : (usage.presentations_this_month / plan.presentations_per_month) * 100;

  return (
    <div className="space-y-6">
      {/* Current Plan */}
      <Card className={`border-2 ${tierColors[tier]}`}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getTierIcon(tier)}
              <div>
                <CardTitle>{plan.name}</CardTitle>
                <CardDescription>Ваш текущий тариф</CardDescription>
              </div>
            </div>
            <Badge className={tierColors[tier]}>
              {tier.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Usage Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Использовано презентаций</span>
              <span className="font-medium">
                {plan.presentations_per_month === -1
                  ? `${usage.presentations_this_month} (unlimited)`
                  : `${usage.presentations_this_month} / ${plan.presentations_per_month}`}
              </span>
            </div>
            {plan.presentations_per_month !== -1 && (
              <Progress value={usagePercent} className="h-2" />
            )}
          </div>

          {/* Plan Limits */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <p className="text-sm text-muted-foreground">Макс. слайдов</p>
              <p className="text-lg font-semibold">{plan.max_slides}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Макс. размер</p>
              <p className="text-lg font-semibold">{plan.max_file_size_mb}MB</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Качество AI</p>
              <p className="text-lg font-semibold capitalize">{plan.ai_quality}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Приоритет</p>
              <p className="text-lg font-semibold capitalize">{plan.priority}</p>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-2 pt-4 border-t">
            <p className="text-sm font-medium">Возможности:</p>
            <ul className="space-y-1">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-center gap-2 text-sm">
                  <Check className="h-4 w-4 text-green-500" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Options */}
      {tier !== 'enterprise' && allPlans && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold">Обновить тариф</h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            {/* PRO Plan */}
            {tier === 'free' && allPlans.pro && (
              <Card className="border-2 border-blue-300">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                    <CardTitle>Professional</CardTitle>
                  </div>
                  <CardDescription>
                    ${allPlans.pro.price_monthly}/месяц
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {allPlans.pro.features.slice(0, 4).map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-blue-500" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button
                    onClick={() => handleUpgrade('PRO')}
                    className="w-full"
                    variant="default"
                  >
                    Обновить до PRO
                  </Button>
                </CardFooter>
              </Card>
            )}

            {/* ENTERPRISE Plan */}
            {allPlans.enterprise && (
              <Card className="border-2 border-purple-300">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Crown className="h-5 w-5 text-purple-600" />
                    <CardTitle>Enterprise</CardTitle>
                  </div>
                  <CardDescription>
                    ${allPlans.enterprise.price_monthly}/месяц
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {allPlans.enterprise.features.slice(0, 4).map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-purple-500" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button
                    onClick={() => handleUpgrade('ENTERPRISE')}
                    className="w-full"
                    variant="default"
                  >
                    Обновить до ENTERPRISE
                  </Button>
                </CardFooter>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Usage Warning */}
      {usagePercent > 80 && plan.presentations_per_month !== -1 && (
        <Alert>
          <AlertDescription>
            Вы использовали {Math.round(usagePercent)}% лимита презентаций. 
            Рассмотрите возможность обновления тарифа для продолжения работы.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};
