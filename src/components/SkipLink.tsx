import React from 'react';

export const SkipLink: React.FC = () => {
  return (
    <a 
      href="#main-content" 
      className="
        absolute left-[-9999px] top-4 z-[100]
        bg-primary text-primary-foreground 
        px-4 py-2 rounded-md
        font-medium
        focus:left-4 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2
        transition-all
      "
    >
      Перейти к основному контенту
    </a>
  );
};
