/**
 * Debug script for browser console
 * Paste this in browser DevTools Console to debug VFX positioning
 * 
 * FIXED: Canvas координаты теперь трансформируются ТОЛЬКО с масштабом, без offset
 */

console.log('🔍 VFX Debug Info:');
console.log('==================');

// Get slide container
const slideContainer = document.querySelector('[aria-label*="Слайд"]');
if (slideContainer) {
    const rect = slideContainer.getBoundingClientRect();
    console.log('📦 Slide container:', {
        width: rect.width,
        height: rect.height,
        top: rect.top,
        left: rect.left
    });
}

// Get slide image
const slideImage = slideContainer?.querySelector('img');
if (slideImage) {
    const rect = slideImage.getBoundingClientRect();
    const computed = window.getComputedStyle(slideImage);
    console.log('🖼️  Slide image:', {
        naturalWidth: slideImage.naturalWidth,
        naturalHeight: slideImage.naturalHeight,
        displayWidth: rect.width,
        displayHeight: rect.height,
        transform: computed.transform,
        objectFit: computed.objectFit
    });
    
    // Вычислить масштаб
    if (slideImage.naturalWidth > 0) {
        const imageScale = rect.width / slideImage.naturalWidth;
        console.log('📐 Image scale:', imageScale.toFixed(4));
    }
}

// Get canvas
const canvas = slideContainer?.querySelector('canvas');
if (canvas) {
    const rect = canvas.getBoundingClientRect();
    const computed = window.getComputedStyle(canvas);
    console.log('🎨 Canvas:', {
        width: canvas.width,
        height: canvas.height,
        displayWidth: rect.width,
        displayHeight: rect.height,
        style: {
            width: canvas.style.width,
            height: canvas.style.height,
            position: computed.position,
            top: computed.top,
            left: computed.left
        }
    });
    
    // Verify canvas matches container
    const containerRect = slideContainer.getBoundingClientRect();
    const matchesContainer = Math.abs(rect.width - containerRect.width) < 1 && 
                            Math.abs(rect.height - containerRect.height) < 1;
    console.log('✅ Canvas matches container:', matchesContainer ? 'YES' : 'NO ❌');
}

// Try to get first effect bbox
console.log('\n🎯 Example effect bbox from database: [112, 90, 277, 60]');
console.log('   This means: x=112px, y=90px, width=277px, height=60px');
console.log('   In original slide coordinates (e.g., 1920x1080)');

if (slideImage && canvas && slideImage.naturalWidth > 0) {
    const [origX, origY, origW, origH] = [112, 90, 277, 60];
    const scale = canvas.getBoundingClientRect().width / slideImage.naturalWidth;
    const transformedX = origX * scale;
    const transformedY = origY * scale;
    const transformedW = origW * scale;
    const transformedH = origH * scale;
    
    console.log('\n� Expected transformation (using only scale):');
    console.log('   Scale factor:', scale.toFixed(4));
    console.log('   Transformed bbox:', [
        transformedX.toFixed(1),
        transformedY.toFixed(1),
        transformedW.toFixed(1),
        transformedH.toFixed(1)
    ]);
    console.log('   Position on canvas:', `x=${transformedX.toFixed(0)}px, y=${transformedY.toFixed(0)}px`);
}

console.log('\n💡 Fixes applied:');
console.log('   ✅ Canvas координаты теперь используют ТОЛЬКО масштаб');
console.log('   ✅ Offset изображения больше НЕ применяется к canvas');
console.log('   ✅ Canvas занимает весь контейнер без смещения');

