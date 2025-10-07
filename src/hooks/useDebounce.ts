import { useState, useEffect } from 'react';

/**
 * Hook для debouncing значений
 * Полезен для оптимизации поисковых запросов и других частых обновлений
 * 
 * @param value - Значение для debounce
 * @param delay - Задержка в миллисекундах (по умолчанию 500)
 * @returns Debounced значение
 */
export const useDebounce = <T,>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Устанавливаем таймер для обновления debounced значения
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Очищаем таймер при изменении value или unmount
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook для debouncing функций
 * Полезен когда нужно debounce саму функцию, а не значение
 * 
 * @param callback - Функция для debounce
 * @param delay - Задержка в миллисекундах (по умолчанию 500)
 * @returns Debounced функция
 */
export const useDebouncedCallback = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number = 500
): ((...args: Parameters<T>) => void) => {
  const [timer, setTimer] = useState<NodeJS.Timeout | null>(null);

  const debouncedCallback = (...args: Parameters<T>) => {
    if (timer) {
      clearTimeout(timer);
    }

    const newTimer = setTimeout(() => {
      callback(...args);
    }, delay);

    setTimer(newTimer);
  };

  useEffect(() => {
    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [timer]);

  return debouncedCallback;
};
