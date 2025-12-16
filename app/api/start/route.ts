import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(request: Request) {
    try {
        const { email } = await request.json();

        if (!email || !email.includes('@')) {
            return NextResponse.json({ error: 'Invalid email address' }, { status: 400 });
        }

        try {
            await prisma.participant.create({
                data: { email },
            });
        } catch (e: any) {
            // If email exists (unique constraint), just proceed
            if (e.code !== 'P2002') {
                throw e;
            }
        }

        return NextResponse.json({ success: true });
    } catch (error) {
        console.error('Start error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
