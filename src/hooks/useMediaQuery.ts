import { useState, useEffect } from 'react';

/**
 * Hook для отслеживания media queries
 * Полезен для адаптивного поведения компонентов
 * 
 * @param query - Media query строка (например, '(max-width: 768px)')
 * @returns boolean - true если media query совпадает
 */
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);
    
    // Обработчик изменения
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Устанавливаем начальное значение
    setMatches(mediaQuery.matches);

    // Подписываемся на изменения
    mediaQuery.addEventListener('change', handleChange);

    // Очистка
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [query]);

  return matches;
};

/**
 * Предопределенные breakpoints
 */
export const useBreakpoints = () => {
  const isMobile = useMediaQuery('(max-width: 640px)');
  const isTablet = useMediaQuery('(min-width: 641px) and (max-width: 1024px)');
  const isDesktop = useMediaQuery('(min-width: 1025px)');
  const isSmall = useMediaQuery('(max-width: 768px)');
  const isMedium = useMediaQuery('(min-width: 769px) and (max-width: 1279px)');
  const isLarge = useMediaQuery('(min-width: 1280px)');

  return {
    isMobile,
    isTablet,
    isDesktop,
    isSmall,
    isMedium,
    isLarge,
  };
};
