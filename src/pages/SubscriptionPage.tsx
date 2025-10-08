/**
 * Subscription Management Page
 */
import React, { useEffect } from 'react';
import { Crown, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SubscriptionManager } from '@/components/SubscriptionManager';
import { useNavigate } from 'react-router-dom';
import { trackEvent } from '@/lib/analytics';

export const SubscriptionPage: React.FC = () => {
  const navigate = useNavigate();

  // Track pricing page view
  useEffect(() => {
    trackEvent.pricingPageViewed();
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container max-w-6xl py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate(-1)}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <div className="flex items-center gap-3">
                <Crown className="h-8 w-8 text-primary" />
                <div>
                  <h1 className="text-3xl font-bold">Управление подпиской</h1>
                  <p className="text-muted-foreground">
                    Просмотр и управление вашим тарифным планом
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container max-w-6xl py-8">
        <SubscriptionManager />
      </div>

      {/* Footer */}
      <div className="border-t mt-12">
        <div className="container max-w-6xl py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>Нужна помощь? Свяжитесь с нами: support@slide-speaker.com</p>
            <p className="mt-2">
              Платежи обрабатываются безопасно через Stripe
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
