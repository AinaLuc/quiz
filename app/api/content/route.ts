import { NextResponse } from 'next/server';
import { prisma } from '../../../lib/prisma';

export async function GET() {
    try {
        const content = await prisma.contentPair.findMany({
            orderBy: {
                createdAt: 'desc', // Newest first
            },
        });
        return NextResponse.json(content);
    } catch (e) {
        console.error('Content fetch error:', e);
        return NextResponse.json([], { status: 500 });
    }
}
