/**
 * Advanced Visual Effects для AI лектора
 * Реализует расширенные визуальные эффекты:
 * - Ken Burns (zoom + pan)
 * - Typewriter (печатание текста)
 * - Particle highlight (частицы)
 * - Arrow pointer (стрелки)
 * - Circle draw (обводка)
 * - И другие
 * 
 * Note: Использует стандартные CSS анимации вместо framer-motion
 */

import React, { useEffect, useRef, useState } from 'react';

interface EffectConfig {
  type: string;
  bbox: [number, number, number, number];
  duration: number;
  intensity?: string;
  particleCount?: number;
  charsPerSecond?: number;
  direction?: string;
}

interface AdvancedEffectProps {
  config: EffectConfig;
  active: boolean;
  text?: string;
  onComplete?: () => void;
}

/**
 * Ken Burns Effect - медленный zoom и pan
 */
export const KenBurnsEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const [x, y, width, height] = config.bbox;
  const [animation, setAnimation] = useState({ scale: 1, translateX: 0, translateY: 0 });

  useEffect(() => {
    if (active) {
      const panX = Math.random() * 50 - 25;
      const panY = Math.random() * 50 - 25;
      
      setAnimation({ scale: 1.2, translateX: panX, translateY: panY });
      
      const timer = setTimeout(() => {
        onComplete?.();
      }, (config.duration || 8) * 1000);
      
      return () => clearTimeout(timer);
    } else {
      setAnimation({ scale: 1, translateX: 0, translateY: 0 });
    }
  }, [active, config.duration, onComplete]);

  if (!active) return null;

  return (
    <div
      className="absolute pointer-events-none transition-all ease-in-out"
      style={{
        left: x,
        top: y,
        width,
        height,
        border: '2px solid rgba(59, 130, 246, 0.5)',
        borderRadius: '4px',
        overflow: 'hidden',
        transform: `scale(${animation.scale}) translate(${animation.translateX}px, ${animation.translateY}px)`,
        transitionDuration: `${config.duration || 8}s`,
      }}
    />
  );
};

/**
 * Typewriter Effect - печатание текста
 */
export const TypewriterEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  text = '',
  onComplete,
}) => {
  const [displayText, setDisplayText] = useState('');
  const [x, y, width, height] = config.bbox;
  const charsPerSecond = config.charsPerSecond || 15;

  useEffect(() => {
    if (active && text) {
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex < text.length) {
          setDisplayText(text.substring(0, currentIndex + 1));
          currentIndex++;
        } else {
          clearInterval(interval);
          onComplete?.();
        }
      }, 1000 / charsPerSecond);

      return () => clearInterval(interval);
    } else {
      setDisplayText('');
    }
  }, [active, text, charsPerSecond, onComplete]);

  if (!active || !text) return null;

  return (
    <div
      className="absolute pointer-events-none z-50"
      style={{
        left: x,
        top: y,
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        className="font-bold text-blue-600"
        style={{
          fontSize: `${Math.min(height / 2, 48)}px`,
          textShadow: '2px 2px 4px rgba(0,0,0,0.2)',
        }}
      >
        {displayText}
        <span className="animate-pulse">|</span>
      </div>
    </div>
  );
};

/**
 * Particle Highlight Effect - частицы вокруг элемента
 */
export const ParticleHighlightEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [x, y, width, height] = config.bbox;
  const particleCount = config.particleCount || 30;

  useEffect(() => {
    if (!active || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Создаём частицы
    interface Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      life: number;
      maxLife: number;
      size: number;
    }

    const particles: Particle[] = [];
    const centerX = width / 2;
    const centerY = height / 2;

    // Инициализация частиц
    for (let i = 0; i < particleCount; i++) {
      const angle = (Math.PI * 2 * i) / particleCount;
      particles.push({
        x: centerX,
        y: centerY,
        vx: Math.cos(angle) * 2,
        vy: Math.sin(angle) * 2,
        life: 0,
        maxLife: config.duration * 60, // 60 FPS
        size: Math.random() * 3 + 2,
      });
    }

    let animationId: number;
    let frame = 0;

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      particles.forEach((particle) => {
        // Обновляем позицию
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life++;

        // Затухание
        const alpha = 1 - particle.life / particle.maxLife;

        // Рисуем частицу
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(59, 130, 246, ${alpha})`;
        ctx.fill();

        // Свечение
        const gradient = ctx.createRadialGradient(
          particle.x,
          particle.y,
          0,
          particle.x,
          particle.y,
          particle.size * 2
        );
        gradient.addColorStop(0, `rgba(147, 197, 253, ${alpha * 0.8})`);
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
        ctx.fillStyle = gradient;
        ctx.fill();
      });

      frame++;
      if (frame < config.duration * 60) {
        animationId = requestAnimationFrame(animate);
      } else {
        onComplete?.();
      }
    };

    animate();

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, [active, width, height, particleCount, config.duration, onComplete]);

  if (!active) return null;

  return (
    <canvas
      ref={canvasRef}
      className="absolute pointer-events-none z-40"
      style={{ left: x, top: y }}
      width={width}
      height={height}
    />
  );
};

/**
 * Circle Draw Effect - обводка кругом
 */
export const CircleDrawEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const [x, y, width, height] = config.bbox;
  const radius = Math.max(width, height) / 2 + 20;
  const centerX = x + width / 2;
  const centerY = y + height / 2;
  const circumference = 2 * Math.PI * (radius - 5);

  useEffect(() => {
    if (active) {
      const timer = setTimeout(onComplete || (() => {}), config.duration * 1000);
      return () => clearTimeout(timer);
    }
  }, [active, config.duration, onComplete]);

  if (!active) return null;

  return (
    <svg
      className="absolute pointer-events-none z-40"
      style={{
        left: centerX - radius,
        top: centerY - radius,
        width: radius * 2,
        height: radius * 2,
      }}
    >
      <circle
        cx={radius}
        cy={radius}
        r={radius - 5}
        fill="none"
        stroke="#3b82f6"
        strokeWidth="3"
        strokeDasharray={circumference}
        strokeDashoffset={circumference}
        style={{
          animation: `drawCircle ${config.duration * 0.8}s ease-in-out forwards`,
        }}
      />
      <style>{`
        @keyframes drawCircle {
          to {
            stroke-dashoffset: 0;
          }
        }
      `}</style>
    </svg>
  );
};

/**
 * Arrow Point Effect - анимированная стрелка
 */
export const ArrowPointEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const [x, y, width, height] = config.bbox;
  const centerX = x + width / 2;
  const centerY = y + height / 2;

  const startY = centerY - 100;

  useEffect(() => {
    if (active) {
      const timer = setTimeout(onComplete || (() => {}), config.duration * 1000);
      return () => clearTimeout(timer);
    }
  }, [active, config.duration, onComplete]);

  if (!active) return null;

  return (
    <svg
      className="absolute pointer-events-none z-40"
      style={{
        left: centerX - 15,
        top: startY,
        width: 30,
        height: 100,
        animation: `arrowBounce ${config.duration / 3}s ease-in-out infinite`,
      }}
    >
      <path
        d="M15 0 L15 70 M15 70 L10 60 M15 70 L20 60"
        stroke="#ef4444"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
      />
      <style>{`
        @keyframes arrowBounce {
          0%, 100% { transform: translateY(0); opacity: 0; }
          20%, 80% { opacity: 1; }
          50% { transform: translateY(20px); opacity: 1; }
        }
      `}</style>
    </svg>
  );
};

/**
 * Pulse Effect - пульсация
 */
export const PulseEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const [x, y, width, height] = config.bbox;

  useEffect(() => {
    if (active) {
      const timer = setTimeout(onComplete || (() => {}), config.duration * 1000);
      return () => clearTimeout(timer);
    }
  }, [active, config.duration, onComplete]);

  if (!active) return null;

  return (
    <div
      className="absolute pointer-events-none rounded-lg border-4 border-yellow-400"
      style={{
        left: x - 10,
        top: y - 10,
        width: width + 20,
        height: height + 20,
        animation: `pulse ${config.duration / 3}s ease-in-out 3`,
      }}
    >
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.1); opacity: 1; }
        }
      `}</style>
    </div>
  );
};

/**
 * Slide In Effect - появление со стороны
 */
export const SlideInEffect: React.FC<AdvancedEffectProps> = ({
  config,
  active,
  onComplete,
}) => {
  const [x, y, width, height] = config.bbox;
  const direction = config.direction || 'left';

  const getTransform = () => {
    switch (direction) {
      case 'left':
        return 'translateX(-100%)';
      case 'right':
        return 'translateX(100%)';
      case 'top':
        return 'translateY(-100%)';
      case 'bottom':
        return 'translateY(100%)';
      default:
        return 'translateX(-100%)';
    }
  };

  useEffect(() => {
    if (active) {
      const timer = setTimeout(onComplete || (() => {}), config.duration * 1000);
      return () => clearTimeout(timer);
    }
  }, [active, config.duration, onComplete]);

  if (!active) return null;

  return (
    <div
      className="absolute pointer-events-none bg-blue-500 bg-opacity-20 rounded"
      style={{
        left: x,
        top: y,
        width,
        height,
        animation: `slideIn ${config.duration}s ease-out forwards`,
      }}
    >
      <style>{`
        @keyframes slideIn {
          0% { transform: ${getTransform()}; opacity: 0; }
          30% { opacity: 1; }
          70% { opacity: 1; }
          100% { transform: translate(0, 0); opacity: 0; }
        }
      `}</style>
    </div>
  );
};

/**
 * Main Effect Renderer - рендерит подходящий эффект
 */
export const AdvancedEffectRenderer: React.FC<{
  cue: any;
  active: boolean;
  text?: string;
}> = ({ cue, active, text }) => {
  const config: EffectConfig = {
    type: cue.effect_type || cue.action,
    bbox: cue.bbox,
    duration: (cue.t1 - cue.t0) || 2,
    intensity: cue.intensity,
    particleCount: cue.particle_count,
    charsPerSecond: cue.chars_per_second,
    direction: cue.direction,
  };

  switch (config.type) {
    case 'ken_burns':
      return <KenBurnsEffect config={config} active={active} />;
    case 'typewriter':
      return <TypewriterEffect config={config} active={active} text={text} />;
    case 'particle_highlight':
      return <ParticleHighlightEffect config={config} active={active} />;
    case 'circle_draw':
      return <CircleDrawEffect config={config} active={active} />;
    case 'arrow_point':
      return <ArrowPointEffect config={config} active={active} />;
    case 'pulse':
      return <PulseEffect config={config} active={active} />;
    case 'slide_in':
      return <SlideInEffect config={config} active={active} />;
    default:
      return null;
  }
};

export default AdvancedEffectRenderer;
