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
import { RouteErrorBoundary } from "@/components/RouteErrorBoundary";
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
// 🔥 TEMPORARY: Import PlayerPage directly (not lazy) for debugging
import PlayerPage from "./pages/PlayerPage";
const VFXTest = lazy(() => import("./pages/VFXTest")); // 🎨 VFX Test page

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-background">
    <div className="text-center">
      <Loader2 className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
      <p className="text-muted-foreground">Загрузка...</p>
    </div>
  </div>
);

// Configure QueryClient with retry logic and exponential backoff
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
      retryDelay: 1000,
    },
  },
});

// Analytics wrapper component
function AnalyticsWrapper({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  useEffect(() => {
    // Initialize analytics on mount
    analytics.init(user?.user_id);

    // Identify user when logged in
    if (user?.user_id) {
      analytics.identify(user.user_id);
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
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <Index />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/login" element={
                    <RouteErrorBoundary>
                      <Login />
                    </RouteErrorBoundary>
                  } />
                  <Route path="/register" element={
                    <RouteErrorBoundary>
                      <Register />
                    </RouteErrorBoundary>
                  } />
                  <Route path="/subscription" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <SubscriptionPage />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/analytics" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute requireRole="admin">
                        <Analytics />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/lessons/:lessonId/quiz" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <QuizGenerator standalone={true} />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/quiz/:quizId/edit" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <QuizEditor />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/playlists" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <PlaylistsPage />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/playlists/:id/play" element={
                    <RouteErrorBoundary>
                      <ProtectedRoute>
                        <PlaylistPlayerPage />
                      </ProtectedRoute>
                    </RouteErrorBoundary>
                  } />
                  <Route path="/player/:lessonId" element={
                    <RouteErrorBoundary>
                      <PlayerPage />
                    </RouteErrorBoundary>
                  } />
                  <Route path="/vfx-test" element={
                    <RouteErrorBoundary>
                      <VFXTest />
                    </RouteErrorBoundary>
                  } />
                  {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                  <Route path="*" element={
                    <RouteErrorBoundary>
                      <NotFound />
                    </RouteErrorBoundary>
                  } />
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
