import React from 'react';
import { VirtualizedList } from './VirtualizedList';
import { Slide } from '@/lib/api';

interface SlideListProps {
  slides: Slide[];
  currentSlide: number;
  onSlideSelect: (slideId: number) => void;
  height?: number;
}

export const VirtualizedSlideList: React.FC<SlideListProps> = ({
  slides,
  currentSlide,
  onSlideSelect,
  height = 400
}) => {
  const renderSlideItem = ({ index, style, item: slide }: {
    index: number;
    style: React.CSSProperties;
    item: Slide;
  }) => {
    const isActive = currentSlide === slide.id;
    const slideTitle = `Слайд ${slide.id}`;
    
    return (
      <div
        style={style}
        role="button"
        tabIndex={0}
        aria-label={`${slideTitle}${isActive ? ' (текущий)' : ''}. ${slide.cues.length} реплик, ${slide.elements.length} элементов`}
        aria-pressed={isActive}
        className={`flex items-center p-2 cursor-pointer hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 ${
          isActive ? 'bg-blue-100 border-l-4 border-blue-500' : ''
        }`}
        onClick={() => onSlideSelect(slide.id)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onSlideSelect(slide.id);
          }
        }}
      >
        <div className="flex-shrink-0 w-16 h-12 bg-gray-200 rounded mr-3 overflow-hidden">
          <img
            src={`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${slide.image}`}
            alt={slideTitle}
            className="w-full h-full object-cover"
          />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium text-gray-900 truncate">
            {slideTitle}
          </div>
          <div className="text-xs text-gray-500">
            {slide.cues.length} реплик • {slide.elements.length} элементов
          </div>
          {slide.speaker_notes && (
            <div className="text-xs text-gray-600 truncate mt-1">
              {typeof slide.speaker_notes === 'string' 
                ? slide.speaker_notes.substring(0, 100) + '...'
                : Array.isArray(slide.speaker_notes) 
                  ? slide.speaker_notes.map(note => note.text).join(' ').substring(0, 100) + '...'
                  : 'Заметки докладчика доступны'}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <VirtualizedList
      items={slides}
      height={height}
      itemHeight={80}
      renderItem={renderSlideItem}
      className="border rounded-lg"
    />
  );
};