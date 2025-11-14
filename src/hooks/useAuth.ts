import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { LoginRequest, RegisterRequest } from '@/lib/api';

export const authKeys = {
  currentUser: ['auth', 'currentUser'] as const,
  session: ['auth', 'session'] as const,
};

/**
 * Hook to get current authenticated user
 * Automatically refetches on window focus and reconnect
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: authKeys.currentUser,
    queryFn: async () => {
      console.log('[useCurrentUser] Fetching current user...');
      try {
        const user = await apiClient.getCurrentUser();
        console.log('[useCurrentUser] Got user:', user.email);
        return user;
      } catch (error) {
        console.log('[useCurrentUser] Error:', error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on 401 errors
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook for user login
 * Automatically invalidates and refetches user data on success
 */
export function useLogin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      console.log('[useLogin] Attempting login...');
      const result = await apiClient.login(credentials);
      console.log('[useLogin] Login API call successful');
      return result;
    },
    onSuccess: async () => {
      console.log('[useLogin] onSuccess - invalidating queries...');
      // Invalidate and refetch user data - wait for it to complete
      await queryClient.invalidateQueries({ queryKey: authKeys.currentUser });
      console.log('[useLogin] onSuccess - refetching user data...');
      // Explicitly refetch to ensure we have fresh data
      await queryClient.refetchQueries({ queryKey: authKeys.currentUser });
      console.log('[useLogin] onSuccess - refetch complete');
    },
    onError: (error) => {
      console.error('[useLogin] Login error:', error);
    },
  });
}

/**
 * Hook for user logout
 * Clears all cached data on success
 */
export function useLogout() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      // Clear all queries
      queryClient.clear();
      // Remove user data from localStorage
      localStorage.removeItem('slide-speaker-user');
    },
    onError: (error) => {
      console.error('Logout error:', error);
      // Clear data even on error
      queryClient.clear();
      localStorage.removeItem('slide-speaker-user');
    },
  });
}

/**
 * Hook for user registration
 * Automatically invalidates and refetches user data on success
 */
export function useRegister() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (credentials: RegisterRequest) => apiClient.register(credentials),
    onSuccess: async () => {
      // Invalidate and refetch user data - wait for it to complete
      await queryClient.invalidateQueries({ queryKey: authKeys.currentUser });
      // Explicitly refetch to ensure we have fresh data
      await queryClient.refetchQueries({ queryKey: authKeys.currentUser });
    },
    onError: (error) => {
      console.error('Registration error:', error);
    },
  });
}
