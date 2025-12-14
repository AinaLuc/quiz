export interface ContentPair {
  id: string;
  imageA: string; // URL or path
  imageB: string; // URL or path
  textA: string;
  textB: string;
  // We need to know which one is AI, but we won't expose this easily to the client if possible,
  // or we just obscure it. For a simple app, we might send it but not display it.
  // Better: Don't send "isAi" to client. Keep it server-side?
  // But for simplicity in this prototype, we might just keep it here and "blind" the UI.
  aiSide: 'A' | 'B'; 
}

export const contentPairs: ContentPair[] = Array.from({ length: 20 }, (_, i) => ({
  id: `pair-${i + 1}`,
  imageA: `/placeholders/img-${i + 1}-a.jpg`, 
  imageB: `/placeholders/img-${i + 1}-b.jpg`,
  textA: `Sample text A for pair ${i + 1}. This is a creative description.`,
  textB: `Sample text B for pair ${i + 1}. This is a creative description.`,
  aiSide: Math.random() > 0.5 ? 'A' : 'B',
}));
