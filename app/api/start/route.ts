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
    } catch (error: any) {
        console.error('Start error:', error);
        // Debug info for user
        return NextResponse.json({
            error: error.message || 'Internal Server Error',
            stack: error.stack,
            envCheck: process.env.DATABASE_URL ? 'DB_URL_PRESENT' : 'DB_URL_MISSING'
        }, { status: 500 });
    }
}
}
```
