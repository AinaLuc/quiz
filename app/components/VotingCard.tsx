'use client';

import { useState } from 'react';
import { ContentPair } from '../data/content';

interface VotingCardProps {
    pair: ContentPair;
    onVote: (pairId: string, userGuessForAI: 'A' | 'B', preference: 'A' | 'B') => void;
}

export default function VotingCard({ pair, onVote }: VotingCardProps) {
    const [selectedAiGuess, setSelectedAiGuess] = useState<'A' | 'B' | null>(null);
    const [selectedPreference, setSelectedPreference] = useState<'A' | 'B' | null>(null);

    const handleSubmit = () => {
        if (selectedAiGuess && selectedPreference) {
            onVote(pair.id, selectedAiGuess, selectedPreference);
            setSelectedAiGuess(null);
            setSelectedPreference(null);
        }
    };

    return (
        <div className="glass-panel p-6 sm:p-12 rounded-3xl max-w-5xl w-full mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500 shadow-xl shadow-slate-200/50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                {/* Option A */}
                <div className="space-y-4 flex flex-col h-full">
                    <div className="relative aspect-square bg-slate-100 rounded-2xl overflow-hidden border border-slate-200 group shadow-sm transition-all hover:shadow-md">
                        {/* Image or Placeholder */}
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-100">
                            {pair.imageA ? (
                                pair.imageA.includes('placeholder') ? (
                                    <span className="text-lg font-bold text-slate-300 tracking-wider">IMAGE A</span>
                                ) : (
                                    <img src={pair.imageA} alt="Option A" className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105" />
                                )
                            ) : (
                                <div className="flex flex-col items-center justify-center space-y-2 text-slate-300">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-12 h-12">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                    </svg>
                                    <span className="text-xl font-black tracking-widest uppercase">No Image</span>
                                </div>
                            )}
                        </div>
                        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full text-sm font-bold border border-slate-200 shadow-sm text-slate-700 z-10">
                            Option A
                        </div>
                    </div>
                    <div className="p-6 bg-white rounded-2xl border border-slate-100 flex-1 flex items-center justify-center text-center shadow-sm">
                        <p className="text-slate-600 text-lg leading-relaxed font-medium">{pair.textA}</p>
                    </div>
                </div>

                {/* Option B */}
                <div className="space-y-4 flex flex-col h-full">
                    <div className="relative aspect-square bg-slate-100 rounded-2xl overflow-hidden border border-slate-200 group shadow-sm transition-all hover:shadow-md">
                        {/* Image or Placeholder */}
                        <div className="absolute inset-0 flex items-center justify-center bg-slate-100">
                            {pair.imageB ? (
                                pair.imageB.includes('placeholder') ? (
                                    <span className="text-lg font-bold text-slate-300 tracking-wider">IMAGE B</span>
                                ) : (
                                    <img src={pair.imageB} alt="Option B" className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105" />
                                )
                            ) : (
                                <div className="flex flex-col items-center justify-center space-y-2 text-slate-300">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-12 h-12">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                                    </svg>
                                    <span className="text-xl font-black tracking-widest uppercase">No Image</span>
                                </div>
                            )}
                        </div>
                        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full text-sm font-bold border border-slate-200 shadow-sm text-slate-700 z-10">
                            Option B
                        </div>
                    </div>
                    <div className="p-6 bg-white rounded-2xl border border-slate-100 flex-1 flex items-center justify-center text-center shadow-sm">
                        <p className="text-slate-600 text-lg leading-relaxed font-medium">{pair.textB}</p>
                    </div>
                </div>
            </div>

            <div className="space-y-10 border-t border-slate-200 pt-10">
                {/* Question 1: Which is AI? */}
                <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-center text-slate-800">1. Which one do you think is created by AI?</h3>
                    <div className="flex flex-col sm:flex-row justify-center gap-4">
                        <button
                            onClick={() => setSelectedAiGuess('A')}
                            className={`w-full sm:w-auto px-8 py-4 rounded-2xl font-semibold transition-all duration-200 flex items-center justify-center sm:justify-start gap-3 ${selectedAiGuess === 'A'
                                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 scale-[1.02] sm:scale-105 ring-4 ring-sky-100'
                                : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${selectedAiGuess === 'A' ? 'border-white' : 'border-slate-300'}`}>
                                {selectedAiGuess === 'A' && <div className="w-3 h-3 bg-white rounded-full" />}
                            </div>
                            <span>Option A is AI</span>
                        </button>
                        <button
                            onClick={() => setSelectedAiGuess('B')}
                            className={`w-full sm:w-auto px-8 py-4 rounded-2xl font-semibold transition-all duration-200 flex items-center justify-center sm:justify-start gap-3 ${selectedAiGuess === 'B'
                                ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 scale-[1.02] sm:scale-105 ring-4 ring-sky-100'
                                : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${selectedAiGuess === 'B' ? 'border-white' : 'border-slate-300'}`}>
                                {selectedAiGuess === 'B' && <div className="w-3 h-3 bg-white rounded-full" />}
                            </div>
                            <span>Option B is AI</span>
                        </button>
                    </div>
                </div>

                {/* Question 2: Which is Better? */}
                <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-center text-slate-800">2. Which one do you prefer?</h3>
                    <div className="flex flex-col sm:flex-row justify-center gap-4">
                        <button
                            onClick={() => setSelectedPreference('A')}
                            className={`w-full sm:w-auto px-8 py-4 rounded-2xl font-semibold transition-all duration-200 flex items-center justify-center sm:justify-start gap-3 ${selectedPreference === 'A'
                                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 scale-[1.02] sm:scale-105 ring-4 ring-emerald-100'
                                : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${selectedPreference === 'A' ? 'border-white' : 'border-slate-300'}`}>
                                {selectedPreference === 'A' && <div className="w-3 h-3 bg-white rounded-full" />}
                            </div>
                            <span>I prefer A</span>
                        </button>
                        <button
                            onClick={() => setSelectedPreference('B')}
                            className={`w-full sm:w-auto px-8 py-4 rounded-2xl font-semibold transition-all duration-200 flex items-center justify-center sm:justify-start gap-3 ${selectedPreference === 'B'
                                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 scale-[1.02] sm:scale-105 ring-4 ring-emerald-100'
                                : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${selectedPreference === 'B' ? 'border-white' : 'border-slate-300'}`}>
                                {selectedPreference === 'B' && <div className="w-3 h-3 bg-white rounded-full" />}
                            </div>
                            <span>I prefer B</span>
                        </button>
                    </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-center pt-8">
                    <button
                        onClick={handleSubmit}
                        disabled={!selectedAiGuess || !selectedPreference}
                        className={`btn-primary w-full md:w-auto min-w-[240px] text-lg py-4 ${!selectedAiGuess || !selectedPreference ? 'opacity-50 cursor-not-allowed grayscale' : ''
                            }`}
                    >
                        Next Pair →
                    </button>
                </div>
            </div>
        </div>
    );
}
