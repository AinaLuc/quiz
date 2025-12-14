import { NextResponse } from 'next/server';
import { prisma } from '../../lib/prisma';

export async function POST(request: Request) {
    try {
        const body = await request.json();
        const { pairId, userGuessForAI, preference, isCorrect } = body;

        const vote = await prisma.vote.create({
            data: {
                pairId,
                userGuessForAI,
                preference,
                isCorrect,
            },
        });

        return NextResponse.json({ success: true, vote });
    } catch (error) {
        console.error('Vote error:', error);
        return NextResponse.json({ error: 'Failed to record vote' }, { status: 500 });
    }
}
