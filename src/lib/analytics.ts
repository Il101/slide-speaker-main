/**
 * Analytics client SDK for tracking user events
 */

import { nanoid } from 'nanoid';

interface EventProperties {
  [key: string]: any;
}

interface SessionData {
  sessionId: string;
  userId?: string;
  startTime: Date;
}

class Analytics {
  private sessionId: string;
  private userId?: string;
  private isInitialized = false;
  private apiBaseUrl: string;

  constructor() {
    this.sessionId = '';
    // Use environment variable or default to /api
    this.apiBaseUrl = import.meta.env.VITE_API_URL || '/api';
  }

  /**
   * Initialize analytics session
   */
  init(userId?: string) {
    if (typeof window === 'undefined') return;

    // Get or create session ID
    this.sessionId = sessionStorage.getItem('analytics_session_id') || nanoid();
    sessionStorage.setItem('analytics_session_id', this.sessionId);
    
    this.userId = userId;
    this.isInitialized = true;

    // Track session start
    this.trackSession();
    
    // Track page views
    this.trackPageView();
    
    // Track page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.track('Page Hidden');
      } else {
        this.track('Page Visible');
      }
    });

    // Track beforeunload to capture session end
    window.addEventListener('beforeunload', () => {
      this.track('Session End');
    });
  }

  /**
   * Identify user (call when user logs in)
   */
  identify(userId: string) {
    this.userId = userId;
    localStorage.setItem('analytics_user_id', userId);
    
    // Update current session with user ID
    this.trackSession();
  }

  /**
   * Clear user identity (call on logout)
   */
  clearIdentity() {
    this.userId = undefined;
    localStorage.removeItem('analytics_user_id');
  }

  /**
   * Track an event
   */
  async track(eventName: string, properties: EventProperties = {}) {
    if (!this.isInitialized) return;

    const eventData = {
      event_name: eventName,
      user_id: this.userId,
      session_id: this.sessionId,
      properties,
      timestamp: new Date().toISOString(),
      
      // Capture device/browser info
      user_agent: navigator.userAgent,
      page: window.location.pathname,
      referrer: document.referrer,
      screen_resolution: `${window.screen.width}x${window.screen.height}`,
    };

    try {
      // Send to API (use navigator.sendBeacon for reliable delivery)
      const blob = new Blob([JSON.stringify(eventData)], { type: 'application/json' });
      
      // Try sendBeacon first (better for page unload events)
      if (navigator.sendBeacon) {
        navigator.sendBeacon(`${this.apiBaseUrl}/analytics/track`, blob);
      } else {
        // Fallback to fetch
        await fetch(`${this.apiBaseUrl}/analytics/track`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(eventData),
          keepalive: true, // Keep request alive even if page is closed
        });
      }
    } catch (error) {
      // Silently fail - don't break app functionality
      console.debug('Analytics error:', error);
    }
  }

  /**
   * Track page view
   */
  trackPageView() {
    this.track('Page View', {
      path: window.location.pathname,
      title: document.title,
      url: window.location.href,
      search: window.location.search,
      hash: window.location.hash,
    });
  }

  /**
   * Track session data
   */
  private async trackSession() {
    const urlParams = new URLSearchParams(window.location.search);
    
    const sessionData = {
      session_id: this.sessionId,
      user_id: this.userId,
      landing_page: window.location.pathname,
      referrer: document.referrer,
      utm_source: urlParams.get('utm_source'),
      utm_medium: urlParams.get('utm_medium'),
      utm_campaign: urlParams.get('utm_campaign'),
    };

    try {
      await fetch(`${this.apiBaseUrl}/analytics/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData),
      });
    } catch (error) {
      console.debug('Session tracking error:', error);
    }
  }
}

// Export singleton instance
export const analytics = new Analytics();

/**
 * Helper functions to track common events
 */
export const trackEvent = {
  // User events
  signup: (method: string) => 
    analytics.track('User Signed Up', { method }),
  
  login: (method: string) => 
    analytics.track('User Logged In', { method }),
  
  logout: () => 
    analytics.track('User Logged Out'),
  
  emailVerified: () => 
    analytics.track('Email Verified'),

  // Lecture events
  presentationUploaded: (data: { fileSize: number; fileName: string; fileType: string }) =>
    analytics.track('Presentation Uploaded', data),
  
  lectureGenerationStarted: (data: { presentationId: string; slideCount?: number }) =>
    analytics.track('Lecture Generation Started', data),
  
  lectureGenerationCompleted: (data: { lectureId: string; duration?: number; processingTime: number }) =>
    analytics.track('Lecture Generation Completed', data),
  
  lectureGenerationFailed: (data: { error: string; step?: string }) =>
    analytics.track('Lecture Generation Failed', data),
  
  lectureDownloaded: (data: { lectureId: string; format?: string; lectureNumber: number }) =>
    analytics.track('Lecture Downloaded', data),
  
  lectureDeleted: (data: { lectureId: string }) =>
    analytics.track('Lecture Deleted', data),

  // Content editing
  slideEdited: (data: { lectureId: string; slideNumber: number; editType: string }) =>
    analytics.track('Slide Edited', data),
  
  audioRegenerated: (data: { lectureId: string; slideNumber: number }) =>
    analytics.track('Audio Regenerated', data),

  // Monetization events
  pricingPageViewed: () =>
    analytics.track('Pricing Page Viewed'),
  
  upgradeClicked: (data: { plan: string; location: string }) =>
    analytics.track('Upgrade Button Clicked', data),
  
  checkoutStarted: (data: { plan: string; price?: number }) =>
    analytics.track('Checkout Started', data),
  
  paymentSucceeded: (data: { plan: string; amount: number }) =>
    analytics.track('Payment Succeeded', data),
  
  subscriptionCancelled: (data: { plan: string; reason?: string }) =>
    analytics.track('Subscription Cancelled', data),

  // Feature interactions
  featureUsed: (data: { feature: string; details?: any }) =>
    analytics.track('Feature Used', data),
  
  helpClicked: (data: { location: string; topic?: string }) =>
    analytics.track('Help Clicked', data),
  
  feedbackSubmitted: (data: { type: string; rating?: number }) =>
    analytics.track('Feedback Submitted', data),

  // Errors
  error: (data: { errorType: string; errorMessage: string; location: string; fatal?: boolean }) =>
    analytics.track('Error Occurred', data),
  
  apiError: (data: { endpoint: string; statusCode: number; errorMessage: string }) =>
    analytics.track('API Error', data),
};

/**
 * React Hook for analytics
 */
export function useAnalytics() {
  return {
    track: analytics.track.bind(analytics),
    identify: analytics.identify.bind(analytics),
    clearIdentity: analytics.clearIdentity.bind(analytics),
    trackPageView: analytics.trackPageView.bind(analytics),
    trackEvent,
  };
}

export default analytics;
