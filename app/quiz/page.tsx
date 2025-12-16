'use client';

import { useState, useEffect } from 'react';
import VotingCard from '../components/VotingCard';

interface ContentPair {
  id: string;
  imageA: string;
  imageB: string;
  textA: string;
  textB: string;
  aiSide: 'A' | 'B';
}

export default function Home() {
  const [contentPairs, setContentPairs] = useState<ContentPair[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/content')
      .then(res => res.json())
      .then(data => {
        setContentPairs(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load content', err);
        setLoading(false);
      });
  }, []);

  const handleVote = async (pairId: string, userGuessForAI: 'A' | 'B', preference: 'A' | 'B') => {
    const currentPair = contentPairs[currentIndex];
    const isCorrect = userGuessForAI === currentPair.aiSide;

    try {
      await fetch('/api/vote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pairId,
          userGuessForAI,
          preference,
          isCorrect
        }),
      });

      if (currentIndex < contentPairs.length - 1) {
        setCurrentIndex(prev => prev + 1);
      } else {
        setIsFinished(true);
      }
    } catch (error) {
      console.error('Failed to submit vote:', error);
      alert('Something went wrong. Please try again.');
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-pulse text-slate-400 font-medium">Loading content...</div>
      </main>
    );
  }

  if (contentPairs.length === 0) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500">
        <div className="text-center space-y-4">
          <p className="text-lg">No content available to vote on.</p>
          <p className="text-sm">Please ask the admin to upload some pairs.</p>
        </div>
      </main>
    );
  }

  if (isFinished) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-8 bg-slate-50 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-50 via-slate-50 to-white">
        <div className="glass-panel p-12 rounded-3xl max-w-2xl w-full text-center space-y-6 animate-in zoom-in-95 duration-500 shadow-xl shadow-sky-100">
          <div className="w-20 h-20 bg-gradient-to-br from-sky-400 to-blue-600 rounded-full mx-auto flex items-center justify-center mb-6 shadow-lg shadow-sky-500/30">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-10 h-10 text-white">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-slate-800">Thank You for Voting!</h1>
          <p className="text-slate-500 text-lg leading-relaxed">
            Your responses have been recorded. We are analyzing the ability of humans to distinguish AI-generated content.
          </p>
          <div className="pt-8">
            <button
              onClick={() => window.location.reload()}
              className="btn-outline"
            >
              Start Over
            </button>
          </div>
        </div>
      </main>
    );
  }

  const currentPair = contentPairs[currentIndex];

  return (
    <main className="min-h-screen flex flex-col p-6 md:p-12 bg-slate-50 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-sky-50 via-slate-50 to-white">
      <header className="w-full max-w-6xl mx-auto flex justify-between items-center mb-16">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-lg shadow-sky-500/20 flex items-center justify-center">
            <span className="text-white font-bold text-lg">T</span>
          </div>
          <span className="font-bold text-2xl tracking-tight text-slate-700">Turing<span className="text-slate-400">Test</span></span>
        </div>
        <div className="text-sm font-semibold text-slate-500 bg-white/50 px-5 py-2.5 rounded-full border border-slate-200 shadow-sm backdrop-blur-sm">
          <span className="text-sky-600 px-1">{currentIndex + 1}</span>
          <span className="text-slate-300">/</span>
          <span className="px-1">{contentPairs.length}</span>
        </div>
      </header>

      <div className="flex-1 flex flex-col items-center justify-center w-full max-w-6xl mx-auto">
        <div className="text-center mb-12 space-y-4">
          <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-slate-800">
            AI <span className="text-slate-400 font-light mx-2">vs</span> <span className="gradient-text">Human</span>
          </h1>
          <p className="text-slate-500 max-w-xl mx-auto text-lg leading-relaxed">
            Analyze the nuances. Discern the artificial. Vote on which creation transcends the algorithm.
          </p>
        </div>

        <VotingCard
          key={currentPair.id} // Force remount on change
          pair={currentPair}
          onVote={handleVote}
        />
      </div>

      <footer className="w-full text-center py-10 text-slate-400 text-sm">
        &copy; 2024 AI Research Study &middot; <a href="/admin" className="hover:text-sky-500 transition-colors">Admin</a>
      </footer>
    </main>
  );
}
