'use client';

import { useEffect, useState } from 'react';

interface Stats {
    totalVotes: number;
    accuracy: number;
    votes: any[];
}

export default function AdminDashboard() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/admin/stats')
            .then(res => res.json())
            .then(data => {
                setStats(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-500">
                <div className="animate-pulse">Loading stats...</div>
            </div>
        );
    }

    if (!stats) {
        return <div className="text-red-500 text-center p-8">Failed to load stats</div>;
    }

    return (
        <main className="min-h-screen p-8 bg-slate-50 text-slate-800 font-sans">
            <div className="max-w-6xl mx-auto space-y-8">
                <header className="flex justify-between items-center border-b border-slate-200 pb-6">
                    <h1 className="text-3xl font-bold text-slate-800">Admin Dashboard</h1>
                    <div className="flex gap-3 items-center">
                        <a href="/admin/upload" className="btn-primary text-sm py-2 px-4 shadow-sm hover:shadow-md flex items-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                            </svg>
                            Upload New
                        </a>
                        <div className="text-sm text-slate-500 font-medium bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
                            Live Results
                        </div>
                    </div>
                </header>

                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="glass-panel p-6 rounded-xl border border-slate-200 bg-white shadow-sm">
                        <h3 className="text-slate-500 text-sm font-medium uppercase tracking-wider">Total Votes</h3>
                        <p className="text-4xl font-bold mt-2 text-slate-800">{stats.totalVotes}</p>
                    </div>
                    <div className="glass-panel p-6 rounded-xl border border-slate-200 bg-white shadow-sm">
                        <h3 className="text-slate-500 text-sm font-medium uppercase tracking-wider">Human Accuracy</h3>
                        <p className="text-4xl font-bold mt-2 text-emerald-500">
                            {stats.accuracy.toFixed(1)}%
                        </p>
                        <p className="text-xs text-slate-400 mt-1">Correctly identified AI</p>
                    </div>
                    <div className="glass-panel p-6 rounded-xl border border-slate-200 bg-white shadow-sm">
                        <h3 className="text-slate-500 text-sm font-medium uppercase tracking-wider">Pairs Evaluated</h3>
                        <p className="text-4xl font-bold mt-2 text-slate-800">20</p>
                    </div>
                </div>

                {/* Recent Votes Table */}
                <div className="glass-panel rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                        <h2 className="text-xl font-semibold text-slate-700">Recent Votes</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-50 text-slate-500">
                                <tr>
                                    <th className="p-4 font-medium">Time</th>
                                    <th className="p-4 font-medium">Pair ID</th>
                                    <th className="p-4 font-medium">User Guess</th>
                                    <th className="p-4 font-medium">Preference</th>
                                    <th className="p-4 font-medium">Result</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {stats.votes.slice().reverse().map((vote: any) => (
                                    <tr key={vote.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="p-4 text-slate-500">
                                            {new Date(vote.timestamp).toLocaleTimeString()}
                                        </td>
                                        <td className="p-4 font-mono text-xs text-slate-400">{vote.pairId}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${vote.userGuessForAI === 'A' ? 'bg-sky-100 text-sky-700' : 'bg-indigo-100 text-indigo-700'}`}>
                                                Option {vote.userGuessForAI}
                                            </span>
                                        </td>
                                        <td className="p-4 text-slate-600">Option {vote.preference}</td>
                                        <td className="p-4">
                                            {vote.isCorrect ? (
                                                <span className="text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full text-xs font-bold flex items-center w-fit gap-1 border border-emerald-100">
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                                    Correct
                                                </span>
                                            ) : (
                                                <span className="text-red-600 bg-red-50 px-2 py-1 rounded-full text-xs font-bold flex items-center w-fit gap-1 border border-red-100">
                                                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
                                                    Incorrect
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                                {stats.votes.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="p-8 text-center text-slate-400 italic">No votes recorded yet.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>
    );
}
