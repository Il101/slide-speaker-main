import React, { Component, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Вызвать пользовательский обработчик если есть
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Card className="flex flex-col items-center justify-center min-h-[400px] p-8 m-4">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-semibold mb-2">Что-то пошло не так</h2>
          <p className="text-muted-foreground text-center mb-4 max-w-md">
            Произошла ошибка при отображении этого компонента. 
            Попробуйте перезагрузить страницу.
          </p>
          {this.state.error && (
            <details className="mb-4 text-sm text-muted-foreground">
              <summary className="cursor-pointer mb-2">Детали ошибки</summary>
              <pre className="bg-muted p-4 rounded-md overflow-auto max-w-xl">
                {this.state.error.toString()}
              </pre>
            </details>
          )}
          <Button onClick={() => window.location.reload()}>
            Перезагрузить страницу
          </Button>
        </Card>
      );
    }

    return this.props.children;
  }
}
