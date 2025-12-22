'use client';

import { useState, useRef } from 'react';

export default function AdminUploadPage() {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const formRef = useRef<HTMLFormElement>(null);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        setIsSubmitting(true);
        const formData = new FormData(e.currentTarget);

        try {
            const res = await fetch('/api/admin/upload', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) throw new Error('Upload failed');

            alert('Pair uploaded successfully!');
            formRef.current?.reset();
        } catch (error) {
            console.error(error);
            alert('Error uploading pair. Please check inputs.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <main className="min-h-screen p-8 bg-slate-50 text-slate-800 font-sans">
            <div className="max-w-2xl mx-auto space-y-8">
                <header className="border-b border-slate-200 pb-6">
                    <h1 className="text-3xl font-bold text-slate-800">Upload New Pair</h1>
                    <p className="text-slate-500 mt-2">Add a new comparison pair to the voting pool.</p>
                </header>

                <form ref={formRef} onSubmit={handleSubmit} className="glass-panel p-8 rounded-2xl space-y-8 bg-white shadow-lg">

                    {/* Option A */}
                    <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <h3 className="font-semibold text-lg text-slate-700">Option A</h3>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-600">Image A (Optional)</label>
                            <input type="file" name="imageA" accept="image/*" className="w-full text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 transition-all" />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-600">Text A</label>
                            <textarea name="textA" required placeholder="Description for Option A..." className="w-full rounded-lg border-slate-200 p-3 text-sm focus:ring-2 focus:ring-sky-500 bg-white min-h-[80px]" />
                        </div>
                    </div>

                    {/* Option B */}
                    <div className="space-y-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <h3 className="font-semibold text-lg text-slate-700">Option B</h3>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-600">Image B (Optional)</label>
                            <input type="file" name="imageB" accept="image/*" className="w-full text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-sky-50 file:text-sky-700 hover:file:bg-sky-100 transition-all" />
                        </div>
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-slate-600">Text B</label>
                            <textarea name="textB" required placeholder="Description for Option B..." className="w-full rounded-lg border-slate-200 p-3 text-sm focus:ring-2 focus:ring-sky-500 bg-white min-h-[80px]" />
                        </div>
                    </div>

                    {/* AI Selection */}
                    <div className="space-y-4">
                        <h3 className="font-semibold text-lg text-slate-700">Metadata</h3>
                        <div className="space-y-2">
                            <span className="block text-sm font-medium text-slate-600 mb-2">Which side is AI?</span>
                            <div className="flex gap-4">
                                <label className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 w-full transition-colors">
                                    <input type="radio" name="aiSide" value="A" required className="text-sky-500 focus:ring-sky-500" />
                                    <span className="font-medium text-slate-700">Option A is AI</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 w-full transition-colors">
                                    <input type="radio" name="aiSide" value="B" required className="text-sky-500 focus:ring-sky-500" />
                                    <span className="font-medium text-slate-700">Option B is AI</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div className="pt-4 flex gap-4">
                        <button type="button" onClick={() => window.history.back()} className="btn-outline flex-1">
                            Cancel
                        </button>
                        <button type="submit" disabled={isSubmitting} className="btn-primary flex-1">
                            {isSubmitting ? 'Uploading...' : 'Upload Pair'}
                        </button>
                    </div>
                </form>
            </div>
        </main>
    );
}
