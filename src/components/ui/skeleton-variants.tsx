import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { Card } from '@/components/ui/card';

export const VideoCardSkeleton: React.FC = () => (
  <Card className="p-4">
    <div className="flex space-x-4">
      <Skeleton className="h-20 w-32 rounded flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
  </Card>
);

export const VideoListSkeleton: React.FC<{ count?: number }> = ({ count = 3 }) => (
  <div className="space-y-4">
    {[...Array(count)].map((_, i) => (
      <VideoCardSkeleton key={i} />
    ))}
  </div>
);

export const SlideListSkeleton: React.FC<{ count?: number }> = ({ count = 5 }) => (
  <div className="space-y-2">
    {[...Array(count)].map((_, i) => (
      <div key={i} className="flex items-center space-x-3 p-2">
        <Skeleton className="h-12 w-16 rounded flex-shrink-0" />
        <div className="flex-1 space-y-1">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-2 w-32" />
        </div>
      </div>
    ))}
  </div>
);

export const PlayerSkeleton: React.FC = () => (
  <div className="space-y-4">
    {/* Video player skeleton */}
    <Skeleton className="w-full aspect-video rounded-lg" />
    
    {/* Controls skeleton */}
    <Card className="p-6 space-y-4">
      <Skeleton className="h-2 w-full" />
      <div className="flex justify-center space-x-2">
        <Skeleton className="h-10 w-10 rounded-full" />
        <Skeleton className="h-12 w-12 rounded-full" />
        <Skeleton className="h-10 w-10 rounded-full" />
      </div>
    </Card>
  </div>
);

export const FormSkeleton: React.FC = () => (
  <div className="space-y-4">
    <div className="space-y-2">
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-full" />
    </div>
    <div className="space-y-2">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-10 w-full" />
    </div>
    <Skeleton className="h-10 w-full" />
  </div>
);

export const NavigationSkeleton: React.FC = () => (
  <div className="flex items-center justify-between p-4">
    <div className="flex items-center space-x-2">
      <Skeleton className="h-8 w-8 rounded" />
      <Skeleton className="h-6 w-24" />
    </div>
    <div className="flex items-center space-x-2">
      <Skeleton className="h-9 w-24 rounded-md" />
      <Skeleton className="h-9 w-20 rounded-md" />
    </div>
  </div>
);
