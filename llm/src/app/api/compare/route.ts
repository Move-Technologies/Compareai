import { NextResponse } from 'next/server';
import https from 'https';

export async function POST(request) {
    try {
        const formData = await request.formData();
        
        // Create custom HTTPS agent that ignores SSL validation
        const httpsAgent = new https.Agent({
            rejectUnauthorized: false
        });

        const response = await fetch('http://127.0.0.1:5000/api/compare', {
            method: 'POST',
            body: formData,
            agent: httpsAgent,
            headers: {
                'Accept': 'application/json',
            },
        });

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error:', error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
