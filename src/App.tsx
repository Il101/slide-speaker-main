import { lazy, Suspense, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { analytics } from "@/lib/analytics";
import { useAuth } from "@/contexts/AuthContext";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { SkipLink } from "@/components/SkipLink";

// Lazy load pages for better performance
const Index = lazy(() => import("./pages/Index"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const NotFound = lazy(() => import("./pages/NotFound"));
const SubscriptionPage = lazy(() => import("./pages/SubscriptionPage").then(module => ({ default: module.SubscriptionPage })));
const Analytics = lazy(() => import("./pages/Analytics"));
const QuizGenerator = lazy(() => import("./components/QuizGenerator").then(module => ({ default: module.QuizGenerator })));
const QuizEditor = lazy(() => import("./components/QuizEditor"));
const PlaylistsPage = lazy(() => import("./pages/PlaylistsPage"));
const PlaylistPlayerPage = lazy(() => import("./pages/PlaylistPlayerPage"));

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-background">
    <div className="text-center">
      <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
      <p className="text-muted-foreground">Загрузка...</p>
    </div>
  </div>
);

const queryClient = new QueryClient();

// Analytics wrapper component
function AnalyticsWrapper({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  useEffect(() => {
    // Initialize analytics on mount
    analytics.init(user?.id);

    // Identify user when logged in
    if (user?.id) {
      analytics.identify(user.id);
    }
  }, [user]);

  useEffect(() => {
    // Track page view on location change
    analytics.trackPageView();
  }, [window.location.pathname]);

  return <>{children}</>;
}

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <SkipLink />
          <Toaster />
          <Sonner />
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <AnalyticsWrapper>
              <main id="main-content">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/" element={
                    <ProtectedRoute>
                      <Index />
                    </ProtectedRoute>
                  } />
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/subscription" element={
                    <ProtectedRoute>
                      <SubscriptionPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/analytics" element={
                    <ProtectedRoute requireRole="admin">
                      <Analytics />
                    </ProtectedRoute>
                  } />
                  <Route path="/lessons/:lessonId/quiz" element={
                    <ProtectedRoute>
                      <QuizGenerator standalone={true} />
                    </ProtectedRoute>
                  } />
                  <Route path="/quiz/:quizId/edit" element={
                    <ProtectedRoute>
                      <QuizEditor />
                    </ProtectedRoute>
                  } />
                  <Route path="/playlists" element={
                    <ProtectedRoute>
                      <PlaylistsPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/playlists/:id/play" element={
                    <ProtectedRoute>
                      <PlaylistPlayerPage />
                    </ProtectedRoute>
                  } />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>
              </main>
            </AnalyticsWrapper>
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
