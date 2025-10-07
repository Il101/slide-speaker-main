export const calculateScale = (
  containerWidth: number,
  containerHeight: number,
  slideWidth: number,
  slideHeight: number
): { x: number; y: number; uniformScale: number; offset: { x: number; y: number } } => {
  // Calculate scale factors
  const scaleX = containerWidth / slideWidth;
  const scaleY = containerHeight / slideHeight;
  
  // Use uniform scaling to maintain aspect ratio
  const uniformScale = Math.min(scaleX, scaleY);
  
  // Ensure minimum scale
  const minScale = 0.1;
  const finalScale = Math.max(uniformScale, minScale);
  
  // Calculate centered offset
  const scaledWidth = slideWidth * finalScale;
  const scaledHeight = slideHeight * finalScale;
  const offsetX = (containerWidth - scaledWidth) / 2;
  const offsetY = (containerHeight - scaledHeight) / 2;
  
  return {
    x: finalScale,
    y: finalScale,
    uniformScale: finalScale,
    offset: { x: offsetX, y: offsetY }
  };
};

export const scaleCoordinates = (
  x: number,
  y: number,
  scale: { x: number; y: number },
  offset: { x: number; y: number }
): { x: number; y: number } => {
  return {
    x: x * scale.x + offset.x,
    y: y * scale.y + offset.y
  };
};

export const scaleBbox = (
  bbox: [number, number, number, number],
  scale: { x: number; y: number },
  offset: { x: number; y: number }
): [number, number, number, number] => {
  const [x, y, width, height] = bbox;
  
  return [
    x * scale.x + offset.x,
    y * scale.y + offset.y,
    width * scale.x,
    height * scale.y
  ];
};
