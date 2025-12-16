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

        if (!imageA || !imageB || !textA || !textB || !aiSide) {
            return NextResponse.json({ error: 'Missing required fields' }, { status: 400 });
        }

        // Upload images (Cloudinary or Local)
        const [imageAPath, imageBPath] = await Promise.all([
            uploadImage(imageA),
            uploadImage(imageB)
        ]);

        // Save to Database via Prisma
        const newPair = await prisma.contentPair.create({
            data: {
                imageA: imageAPath,
                imageB: imageBPath,
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
