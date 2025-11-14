/**
 * VFX Test Page - для отладки визуальных эффектов
 */
import React, { useRef, useEffect, useState } from 'react';
import { VisualEffectsEngine } from '@/components/VisualEffects';

const testManifest: any = {
  version: '2.0',
  id: 'test_slide',
  timeline: {
    total_duration: 10.0,
    events: [
      {
        time: 0.0,
        type: 'SLIDE_START',
        metadata: { slide_duration: 10.0 }
      },
      {
        time: 1.0,
        type: 'START',
        effect_id: 'effect_test_1',
        metadata: {
          effect_id: 'effect_test_1',
          effect_type: 'spotlight',
          confidence: 0.95
        }
      },
      {
        time: 5.0,
        type: 'END',
        effect_id: 'effect_test_1',
        metadata: {
          effect_id: 'effect_test_1',
          effect_type: 'spotlight'
        }
      },
      {
        time: 10.0,
        type: 'SLIDE_END'
      }
    ],
    effects_count: 1
  },
  effects: [
    {
      id: 'effect_test_1',
      type: 'spotlight',
      target: {
        element_id: 'test_elem',
        bbox: [200, 150, 600, 400],
        group_id: 'test_group'
      },
      timing: {
        t0: 1.0,
        t1: 5.0,
        duration: 4.0,
        source: 'manual'
      },
      params: {
        intensity: 'dramatic',
        color: '#ffcc00',
        radius: 150
      }
    }
  ],
  quality: {
    score: 100,
    confidence_avg: 0.95,
    high_confidence_count: 1,
    total_effects: 1
  }
};

export const VFXTest: React.FC = () => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => {
      setCurrentTime(audio.currentTime);
    };

    audio.addEventListener('timeupdate', updateTime);
    return () => audio.removeEventListener('timeupdate', updateTime);
  }, []);

  const handlePlay = () => {
    audioRef.current?.play();
    setIsPlaying(true);
  };

  const handlePause = () => {
    audioRef.current?.pause();
    setIsPlaying(false);
  };

  const handleReset = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">🎨 Visual Effects Test</h1>
        <p className="text-gray-400 mb-8">Testing VFX rendering and synchronization</p>

        {/* Info Panel */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-2">Test Manifest</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Version:</span> {testManifest.version}
            </div>
            <div>
              <span className="text-gray-400">Effects:</span> {testManifest.effects.length}
            </div>
            <div>
              <span className="text-gray-400">Timeline Events:</span> {testManifest.timeline.events.length}
            </div>
            <div>
              <span className="text-gray-400">Quality Score:</span> {testManifest.quality.score}/100
            </div>
          </div>
        </div>

        {/* Effect Details */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-semibold mb-2">Effect Details</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-400">Type:</span> <span className="text-yellow-400">{testManifest.effects[0].type}</span>
            </div>
            <div>
              <span className="text-gray-400">Timing:</span> {testManifest.effects[0].timing.t0}s → {testManifest.effects[0].timing.t1}s
            </div>
            <div>
              <span className="text-gray-400">Target:</span> bbox [{testManifest.effects[0].target.bbox.join(', ')}]
            </div>
            <div>
              <span className="text-gray-400">Intensity:</span> {testManifest.effects[0].params.intensity}
            </div>
          </div>
        </div>

        {/* Viewer */}
        <div className="bg-black rounded-lg overflow-hidden relative" style={{ aspectRatio: '16/9' }}>
          {/* Background image */}
          <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <div className="text-2xl font-bold mb-2">Visual Effects Test</div>
              <div className="text-gray-400">Effect should appear at 1s-5s</div>
            </div>
          </div>

          {/* VFX Overlay */}
          <div className="absolute inset-0 pointer-events-none">
            <VisualEffectsEngine
              manifest={testManifest as any}
              audioElement={audioRef.current}
              preferredRenderer="auto"
              debug={true}
            />
          </div>

          {/* Time indicator */}
          <div className="absolute bottom-4 left-4 bg-black/70 text-white px-4 py-2 rounded-md font-mono">
            {currentTime.toFixed(2)}s / {testManifest.timeline.total_duration}s
          </div>

          {/* Effect active indicator */}
          {currentTime >= 1.0 && currentTime <= 5.0 && (
            <div className="absolute top-4 left-4 bg-yellow-500 text-black px-4 py-2 rounded-md font-bold">
              🎬 EFFECT ACTIVE
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="mt-6 flex gap-4">
          <button
            onClick={handlePlay}
            disabled={isPlaying}
            className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-semibold transition"
          >
            ▶️ Play
          </button>
          <button
            onClick={handlePause}
            disabled={!isPlaying}
            className="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-semibold transition"
          >
            ⏸️ Pause
          </button>
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-semibold transition"
          >
            🔄 Reset
          </button>
        </div>

        {/* Hidden audio element (using silent audio or dummy) */}
        <audio
          ref={audioRef}
          src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA="
          loop
        />

        {/* Debug Console */}
        <div className="mt-6 bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-2">Debug Console</h2>
          <div className="font-mono text-sm text-gray-300">
            <div>Open browser DevTools Console (F12) to see VFX logs</div>
            <div className="mt-2 text-gray-500">Look for:</div>
            <ul className="ml-4 mt-1 space-y-1 text-gray-400">
              <li>• [VisualEffectsEngine] logs</li>
              <li>• [Canvas2DRenderer] or [CSSRenderer] logs</li>
              <li>• Effect START/END events</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VFXTest;
