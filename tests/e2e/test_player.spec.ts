import { test, expect } from '@playwright/test';

test.describe('Player E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the player page
    await page.goto('http://localhost:3000');
  });

  test('should load player interface', async ({ page }) => {
    // Check if the player interface loads
    await expect(page.locator('[data-testid="player-container"]')).toBeVisible();
    
    // Check if slide display is present
    await expect(page.locator('[data-testid="slide-display"]')).toBeVisible();
    
    // Check if controls are present
    await expect(page.locator('[data-testid="play-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="pause-button"]')).toBeVisible();
  });

  test('should play and pause audio', async ({ page }) => {
    // Click play button
    await page.click('[data-testid="play-button"]');
    
    // Check if pause button is visible
    await expect(page.locator('[data-testid="pause-button"]')).toBeVisible();
    
    // Click pause button
    await page.click('[data-testid="pause-button"]');
    
    // Check if play button is visible again
    await expect(page.locator('[data-testid="play-button"]')).toBeVisible();
  });

  test('should navigate between slides', async ({ page }) => {
    // Check initial slide
    await expect(page.locator('[data-testid="slide-counter"]')).toContainText('1 /');
    
    // Click next slide button
    await page.click('[data-testid="next-slide-button"]');
    
    // Check if slide changed
    await expect(page.locator('[data-testid="slide-counter"]')).toContainText('2 /');
    
    // Click previous slide button
    await page.click('[data-testid="prev-slide-button"]');
    
    // Check if slide changed back
    await expect(page.locator('[data-testid="slide-counter"]')).toContainText('1 /');
  });

  test('should show visual effects during playback', async ({ page }) => {
    // Start playback
    await page.click('[data-testid="play-button"]');
    
    // Wait for visual effects to appear
    await expect(page.locator('[data-testid="highlight-effect"]')).toBeVisible({ timeout: 5000 });
    
    // Check if effects are properly positioned
    const highlight = page.locator('[data-testid="highlight-effect"]').first();
    await expect(highlight).toBeVisible();
  });

  test('should enter edit mode', async ({ page }) => {
    // Click edit button
    await page.click('[data-testid="edit-button"]');
    
    // Check if edit mode is active
    await expect(page.locator('[data-testid="cue-editor"]')).toBeVisible();
    
    // Check if elements are highlighted for editing
    await expect(page.locator('[data-testid="element-overlay"]')).toBeVisible();
  });

  test('should adjust volume', async ({ page }) => {
    // Find volume slider
    const volumeSlider = page.locator('[data-testid="volume-slider"]');
    
    // Adjust volume
    await volumeSlider.fill('50');
    
    // Check if volume changed
    await expect(volumeSlider).toHaveValue('50');
  });

  test('should change playback speed', async ({ page }) => {
    // Click speed selector
    await page.click('[data-testid="speed-selector"]');
    
    // Select 1.5x speed
    await page.click('[data-testid="speed-1.5x"]');
    
    // Check if speed changed
    await expect(page.locator('[data-testid="speed-selector"]')).toContainText('1.5x');
  });

  test('should show subtitles', async ({ page }) => {
    // Click subtitles toggle
    await page.click('[data-testid="subtitles-button"]');
    
    // Check if subtitles are visible
    await expect(page.locator('[data-testid="subtitles-display"]')).toBeVisible();
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Simulate network error by intercepting requests
    await page.route('**/api/**', route => route.abort());
    
    // Try to load a lesson
    await page.goto('http://localhost:3000/lesson/test-lesson');
    
    // Check if error boundary is shown
    await expect(page.locator('[data-testid="error-boundary"]')).toBeVisible();
    
    // Check if retry button is available
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if player is still functional
    await expect(page.locator('[data-testid="player-container"]')).toBeVisible();
    
    // Check if controls are accessible
    await expect(page.locator('[data-testid="play-button"]')).toBeVisible();
  });
});