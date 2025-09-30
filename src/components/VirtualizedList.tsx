import React, { useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';

interface VirtualizedListProps<T> {
  items: T[];
  height: number;
  itemHeight: number;
  renderItem: (props: { index: number; style: React.CSSProperties; item: T }) => React.ReactNode;
  className?: string;
}

export function VirtualizedList<T>({
  items,
  height,
  itemHeight,
  renderItem,
  className = ''
}: VirtualizedListProps<T>) {
  const itemData = useMemo(() => items, [items]);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const item = itemData[index];
    return renderItem({ index, style, item });
  };

  return (
    <div className={`virtualized-list ${className}`}>
      <List
        height={height}
        itemCount={items.length}
        itemSize={itemHeight}
        itemData={itemData}
        overscanCount={5} // Render 5 extra items for smooth scrolling
      >
        {Row}
      </List>
    </div>
  );
}

// Hook for virtualized list with dynamic sizing
export function useVirtualizedList<T>(
  items: T[],
  containerHeight: number,
  estimatedItemHeight: number = 50
) {
  const itemCount = items.length;
  const totalHeight = itemCount * estimatedItemHeight;
  
  return {
    itemCount,
    totalHeight,
    isVirtualized: totalHeight > containerHeight,
    itemHeight: estimatedItemHeight
  };
}