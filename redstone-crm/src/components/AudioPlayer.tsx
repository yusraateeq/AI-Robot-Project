"use client";

import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

export function AudioPlayer({ url }: { url: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    // WaveSurfer initialization
    waveSurferRef.current = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#4b5563', // Border-soft jaisa grey
      progressColor: '#3DDC84', // Aapka Signal green
      cursorColor: '#ffffff',
      height: 40,
      barWidth: 2,
    });

    waveSurferRef.current.load(url);

    // Cleanup function
    return () => {
      waveSurferRef.current?.destroy();
    };
  }, [url]);

  const togglePlay = () => {
    if (waveSurferRef.current) {
      waveSurferRef.current.playPause();
      setIsPlaying(!isPlaying);
    }
  };

  return (
    <div className="flex items-center gap-3 w-full">
      <button 
        onClick={togglePlay}
        className="text-text-primary hover:text-signal transition-colors"
      >
        {isPlaying ? "⏸" : "▶"}
      </button>
      <div ref={containerRef} className="flex-1" />
    </div>
  );
}