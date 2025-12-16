import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
    try {
        const totalVotes = await prisma.vote.count();
        const correctVotes = await prisma.vote.count({
            where: { isCorrect: true },
        });

        // Get recent votes with limited fields
        const votes = await prisma.vote.findMany({
            take: 50,
            orderBy: { createdAt: 'desc' },
            select: {
                id: true,
                pairId: true,
                userGuessForAI: true,
                preference: true,
                isCorrect: true,
                createdAt: true, // Prisma uses createdAt, mapped to timestamp in frontend if needed
            }
        });

        const accuracy = totalVotes > 0 ? (correctVotes / totalVotes) * 100 : 0;

        return NextResponse.json({
            totalVotes,
            accuracy,
            votes: votes.map(v => ({
                ...v,
                timestamp: v.createdAt // Map for frontend compatibility
            }))
        });
    } catch (error) {
        console.error('Stats error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
