'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const router = useRouter();

    const handleStart = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setLoading(true);
        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });

            if (res.ok) {
                router.push('/quiz');
            } else {
                alert('Something went wrong. Please try again.');
                setLoading(false);
            }
        } catch (error) {
            console.error(error);
            setLoading(false);
            alert('Error connecting to server.');
        }
    };

    return (
        <div className="min-h-screen bg-white text-slate-900 font-serif selection:bg-slate-200 selection:text-black">

            {/* Consulting Header */}
            <header className="px-8 py-8 md:px-16 md:py-10 border-b border-black">
                <div className="max-w-4xl mx-auto flex items-end justify-between">
                    <div className="text-2xl font-bold tracking-tight text-black font-sans uppercase">
                        Global Insight Group
                    </div>
                    <div className="hidden md:block text-xs font-sans tracking-widest text-slate-500 uppercase">
                        Digital Authenticity Report • Q4 2024
                    </div>
                </div>
            </header>

            <main className="max-w-4xl mx-auto px-8 py-16 md:px-16 md:py-20">

                {/* Title Section */}
                <section className="mb-16 space-y-6">
                    <span className="inline-block border-b-2 border-black pb-1 text-xs font-bold tracking-widest uppercase font-sans">
                        Executive Research
                    </span>
                    <h1 className="text-5xl md:text-6xl font-normal leading-tight mx-auto max-w-3xl">
                        Benchmarking Human Discerment in Generative AI.
                    </h1>
                </section>

                {/* Two Column Layout */}
                <div className="grid md:grid-cols-12 gap-12 md:gap-20 items-start border-t border-slate-200 pt-12">

                    {/* Left: Context */}
                    <div className="md:col-span-7 space-y-8">
                        <p className="text-xl leading-relaxed text-slate-700 font-light">
                            We invite you to participate in a foundational study assessing the current state of digital literacy. Participants will evaluate 20 unique content pairs to distinguish between synthesized (AI) and organic (Human) origins.
                        </p>

                        <div className="grid grid-cols-2 gap-8 py-6">
                            <div>
                                <h4 className="font-sans text-xs font-bold uppercase tracking-widest mb-2 text-slate-400">Publication Date</h4>
                                <p className="text-2xl">December 23rd</p>
                            </div>
                            <div>
                                <h4 className="font-sans text-xs font-bold uppercase tracking-widest mb-2 text-slate-400">Deliverable</h4>
                                <p className="text-2xl">Analysis PDF</p>
                            </div>
                        </div>

                        <div className="font-sans text-xs text-slate-400 max-w-xs leading-normal">
                            *All individual responses are anonymized and aggregated to form the global baseline metric.
                        </div>
                    </div>

                    {/* Right: Action */}
                    <div className="md:col-span-5 bg-slate-50 p-8 border border-slate-100">
                        <form onSubmit={handleStart} className="space-y-6 font-sans">
                            <div className="space-y-4">
                                <h3 className="font-bold text-lg">Begin Assessment</h3>
                                <div className="space-y-2">
                                    <label htmlFor="email" className="text-xs font-semibold text-slate-500 uppercase">
                                        Professional Email
                                    </label>
                                    <input
                                        type="email"
                                        id="email"
                                        required
                                        placeholder="name@organization.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full h-12 px-4 bg-white border border-slate-300 focus:border-black focus:ring-0 outline-none transition-colors rounded-none placeholder:text-slate-300"
                                    />
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full h-12 bg-black text-white hover:bg-slate-800 transition-colors uppercase text-xs font-bold tracking-wider"
                            >
                                {loading ? 'Processing...' : 'Proceed to Survey'}
                            </button>
                        </form>
                    </div>

                </div>
            </main>
        </div>
    );
}
