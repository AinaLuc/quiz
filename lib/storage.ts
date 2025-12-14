import { v2 as cloudinary } from 'cloudinary';
import fs from 'fs';
import path from 'path';
import { writeFile } from 'fs/promises';

// Configure Cloudinary if env vars are present
if (process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME) {
    cloudinary.config({
        cloud_name: process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME,
        api_key: process.env.CLOUDINARY_API_KEY,
        api_secret: process.env.CLOUDINARY_API_SECRET,
    });
}

const UPLOAD_DIR = path.join(process.cwd(), 'public/uploads');

// Ensure upload dir exists for local dev
if (!fs.existsSync(UPLOAD_DIR)) {
    fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

export async function uploadImage(file: File): Promise<string> {
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // Check if Cloudinary is configured
    if (process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME && process.env.CLOUDINARY_API_KEY && process.env.CLOUDINARY_API_SECRET) {
        return new Promise((resolve, reject) => {
            // Create a temporary file to upload (Cloudinary node SDK typically uploads from path or stream)
            // Alternatively, use stream upload. Let's use stream upload for cleaner serverless execution.
            // However, converting buffer to stream is verbose.
            // Simplest: Write to /tmp (available in lambda) then upload.

            const tempPath = path.join('/tmp', `${Date.now()}-${file.name}`);
            fs.writeFileSync(tempPath, buffer);

            cloudinary.uploader.upload(tempPath, {
                folder: 'ai-vs-human',
            }, (error, result) => {
                // Cleanup temp file
                try { fs.unlinkSync(tempPath); } catch (e) { }

                if (error) return reject(error);
                if (result) return resolve(result.secure_url);
                return reject(new Error('Upload failed'));
            });
        });
    }

    // Fallback to Local Storage (FileSystem)
    const filename = `${Date.now()}-${file.name.replace(/\s/g, '-')}`;
    const filepath = path.join(UPLOAD_DIR, filename);
    await writeFile(filepath, buffer);
    return `/uploads/${filename}`;
}
