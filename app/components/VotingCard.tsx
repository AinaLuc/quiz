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
        <div className="glass-panel p-8 rounded-2xl max-w-4xl w-full mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500 shadow-xl shadow-slate-200/50">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                {/* Option A */}
                <div className="space-y-4">
                    <div className="relative aspect-square bg-slate-50 rounded-xl overflow-hidden border border-slate-200 group shadow-md transition-shadow hover:shadow-lg">
                        {/* Placeholder for Image A */}
                        <div className="absolute inset-0 flex items-center justify-center text-slate-400 bg-slate-50">
                            {pair.imageA.includes('placeholder') ? (
                                <span className="text-lg font-medium tracking-wide">Image A</span>
                            ) : (
                                <img src={pair.imageA} alt="Option A" className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105" />
                            )}
                        </div>
                        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full text-sm font-bold border border-slate-200 shadow-sm text-slate-700">
                            Option A
                        </div>
                    </div>
                    <div className="p-5 bg-white rounded-xl border border-slate-100 min-h-[100px] shadow-sm">
                        <p className="text-slate-600 text-sm leading-relaxed">{pair.textA}</p>
                    </div>
                </div>

                {/* Option B */}
                <div className="space-y-4">
                    <div className="relative aspect-square bg-slate-50 rounded-xl overflow-hidden border border-slate-200 group shadow-md transition-shadow hover:shadow-lg">
                        {/* Placeholder for Image B */}
                        <div className="absolute inset-0 flex items-center justify-center text-slate-400 bg-slate-50">
                            {pair.imageB.includes('placeholder') ? (
                                <span className="text-lg font-medium tracking-wide">Image B</span>
                            ) : (
                                <img src={pair.imageB} alt="Option B" className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-105" />
                            )}
                        </div>
                        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full text-sm font-bold border border-slate-200 shadow-sm text-slate-700">
                            Option B
                        </div>
                    </div>
                    <div className="p-5 bg-white rounded-xl border border-slate-100 min-h-[100px] shadow-sm">
                        <p className="text-slate-600 text-sm leading-relaxed">{pair.textB}</p>
                    </div>
                </div>
            </div>

            <div className="space-y-10 border-t border-slate-200 pt-10">
                {/* Question 1: Which is AI? */}
                <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-center text-slate-800">1. Which one do you think is created by AI?</h3>
                    <div className="flex flex-wrap justify-center gap-4">
                        <button
                            onClick={() => setSelectedAiGuess('A')}
                            className={`px-8 py-3.5 rounded-2xl font-semibold transition-all duration-200 ${selectedAiGuess === 'A'
                                    ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 scale-105 ring-2 ring-sky-300'
                                    : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            Option A is AI
                        </button>
                        <button
                            onClick={() => setSelectedAiGuess('B')}
                            className={`px-8 py-3.5 rounded-2xl font-semibold transition-all duration-200 ${selectedAiGuess === 'B'
                                    ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/30 scale-105 ring-2 ring-sky-300'
                                    : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            Option B is AI
                        </button>
                    </div>
                </div>

                {/* Question 2: Which is Better? */}
                <div className="space-y-6">
                    <h3 className="text-xl font-semibold text-center text-slate-800">2. Which one do you prefer?</h3>
                    <div className="flex flex-wrap justify-center gap-4">
                        <button
                            onClick={() => setSelectedPreference('A')}
                            className={`px-8 py-3.5 rounded-2xl font-semibold transition-all duration-200 ${selectedPreference === 'A'
                                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 scale-105 ring-2 ring-emerald-300'
                                    : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            I prefer A
                        </button>
                        <button
                            onClick={() => setSelectedPreference('B')}
                            className={`px-8 py-3.5 rounded-2xl font-semibold transition-all duration-200 ${selectedPreference === 'B'
                                    ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30 scale-105 ring-2 ring-emerald-300'
                                    : 'bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700 border border-slate-200 shadow-sm'
                                }`}
                        >
                            I prefer B
                        </button>
                    </div>
                </div>

                {/* Submit Button */}
                <div className="flex justify-center pt-2">
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
