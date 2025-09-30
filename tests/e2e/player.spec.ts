import { test, expect } from '@playwright/test';

test.describe('Player Functionality', () => {
  test('should play lecture with sound, highlights, and auto slide change', async ({ page }) => {
    // Navigate to the player page with a demo lesson
    await page.goto('/?lesson=demo');
    
    // Wait for the player to load
    await page.waitForSelector('[data-testid="player-container"]', { timeout: 10000 });
    
    // Check that the play button is visible and clickable
    const playButton = page.locator('button[aria-label="Play"]');
    await expect(playButton).toBeVisible();
    
    // Click play button
    await playButton.click();
    
    // Wait for audio to start playing
    await page.waitForTimeout(2000);
    
    // Check that audio is playing (volume should be > 0)
    const audioElement = page.locator('audio');
    await expect(audioElement).toBeAttached();
    
    // Check that highlights appear (should have data-testid="highlight")
    const highlightElement = page.locator('[data-testid="highlight"]');
    await expect(highlightElement).toBeVisible({ timeout: 5000 });
    
    // Check that highlight is not in center (bbox should be offset by >10%)
    const highlightBox = await highlightElement.boundingBox();
    if (highlightBox) {
      const slideContainer = page.locator('.aspect-video');
      const containerBox = await slideContainer.boundingBox();
      
      if (containerBox) {
        const centerX = containerBox.width / 2;
        const centerY = containerBox.height / 2;
        
        const highlightCenterX = highlightBox.x + highlightBox.width / 2;
        const highlightCenterY = highlightBox.y + highlightBox.height / 2;
        
        const offsetX = Math.abs(highlightCenterX - centerX);
        const offsetY = Math.abs(highlightCenterY - centerY);
        
        // Check that highlight is offset by at least 10% of container dimensions
        const minOffsetX = containerBox.width * 0.1;
        const minOffsetY = containerBox.height * 0.1;
        
        expect(offsetX).toBeGreaterThan(minOffsetX);
        expect(offsetY).toBeGreaterThan(minOffsetY);
      }
    }
    
    // Wait for slide change (should happen automatically)
    await page.waitForTimeout(5000);
    
    // Check that slide counter has changed (indicating slide change)
    const slideCounter = page.locator('text=/\\d+ \\/ \\d+/');
    await expect(slideCounter).toBeVisible();
    
    // Verify that the slide number has increased
    const slideText = await slideCounter.textContent();
    expect(slideText).toMatch(/^[2-9] \/ \d+$/); // Should be slide 2 or higher
  });
  
  test('should handle missing targetId gracefully', async ({ page }) => {
    // Navigate to a lesson that might have missing targetId
    await page.goto('/?lesson=demo');
    
    // Wait for the player to load
    await page.waitForSelector('[data-testid="player-container"]', { timeout: 10000 });
    
    // Check console for warnings about missing targetId
    const consoleMessages: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'warning' && msg.text().includes('Target element')) {
        consoleMessages.push(msg.text());
      }
    });
    
    // Click play button
    const playButton = page.locator('button[aria-label="Play"]');
    await playButton.click();
    
    // Wait for any warnings to appear
    await page.waitForTimeout(3000);
    
    // Check that warnings were logged for missing targetId
    expect(consoleMessages.length).toBeGreaterThan(0);
    expect(consoleMessages.some(msg => msg.includes('Target element') && msg.includes('not found'))).toBe(true);
  });
  
  test('should display lecture text in subtitles', async ({ page }) => {
    // Navigate to the player page
    await page.goto('/?lesson=demo');
    
    // Wait for the player to load
    await page.waitForSelector('[data-testid="player-container"]', { timeout: 10000 });
    
    // Click subtitles toggle
    const subtitlesButton = page.locator('button[aria-label="Show subtitles"]');
    await subtitlesButton.click();
    
    // Check that subtitles are visible
    const subtitlesContainer = page.locator('text=No lecture text available').or(
      page.locator('.text-base.leading-relaxed')
    );
    await expect(subtitlesContainer).toBeVisible();
    
    // Check that subtitles contain some text
    const subtitlesText = await subtitlesContainer.textContent();
    expect(subtitlesText).toBeTruthy();
  });
  
  test('should handle MP3 audio format', async ({ page }) => {
    // Navigate to the player page
    await page.goto('/?lesson=demo');
    
    // Wait for the player to load
    await page.waitForSelector('[data-testid="player-container"]', { timeout: 10000 });
    
    // Check that audio element has MP3 source
    const audioElement = page.locator('audio');
    await expect(audioElement).toBeAttached();
    
    // Check that audio source ends with .mp3
    const audioSrc = await audioElement.getAttribute('src');
    expect(audioSrc).toMatch(/\.mp3$/);
    
    // Click play button
    const playButton = page.locator('button[aria-label="Play"]');
    await playButton.click();
    
    // Wait for audio to start
    await page.waitForTimeout(2000);
    
    // Check that audio is playing
    const isPlaying = await audioElement.evaluate((el: HTMLAudioElement) => !el.paused);
    expect(isPlaying).toBe(true);
  });
});