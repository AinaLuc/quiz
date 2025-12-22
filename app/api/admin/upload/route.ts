import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { uploadImage } from '@/lib/storage';

export async function POST(request: Request) {
    try {
        const formData = await request.formData();
        const imageA = formData.get('imageA') as File;
        const imageB = formData.get('imageB') as File;
        const textA = formData.get('textA') as string;
        const textB = formData.get('textB') as string;
        const aiSide = formData.get('aiSide') as string;

        if (!textA || !textB || !aiSide) {
            return NextResponse.json({ error: 'Missing required text fields' }, { status: 400 });
        }

        // Upload images if present
        const [imageAPath, imageBPath] = await Promise.all([
            imageA && imageA.size > 0 ? uploadImage(imageA) : Promise.resolve(null),
            imageB && imageB.size > 0 ? uploadImage(imageB) : Promise.resolve(null)
        ]);

        // Save to Database via Prisma
        const newPair = await prisma.contentPair.create({
            data: {
                imageA: imageAPath || undefined,
                imageB: imageBPath || undefined,
                textA,
                textB,
                aiSide,
            },
        });

        return NextResponse.json({ success: true, pair: newPair });
    } catch (error) {
        console.error('Upload error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
