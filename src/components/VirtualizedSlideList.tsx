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
  }) => (
    <div
      style={style}
      className={`flex items-center p-2 cursor-pointer hover:bg-gray-100 ${
        currentSlide === slide.id ? 'bg-blue-100 border-l-4 border-blue-500' : ''
      }`}
      onClick={() => onSlideSelect(slide.id)}
    >
      <div className="flex-shrink-0 w-16 h-12 bg-gray-200 rounded mr-3 overflow-hidden">
        <img
          src={`${import.meta.env.VITE_API_BASE || 'http://localhost:8000'}${slide.image}`}
          alt={`Slide ${slide.id}`}
          className="w-full h-full object-cover"
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900 truncate">
          Slide {slide.id}
        </div>
        <div className="text-xs text-gray-500">
          {slide.cues.length} cues • {slide.elements.length} elements
        </div>
        {slide.speaker_notes && (
          <div className="text-xs text-gray-600 truncate mt-1">
            {slide.speaker_notes.substring(0, 100)}...
          </div>
        )}
      </div>
    </div>
  );

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