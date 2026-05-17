/**
 * Stripe webhook that re-forwards events to the Python API so all billing
 * state lives in one place.
 */
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const body = await req.text();
  const sig = req.headers.get('stripe-signature');
  const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
  const r = await fetch(`${baseUrl}/webhooks/stripe`, {
    method: 'POST',
    headers: sig ? { 'stripe-signature': sig, 'content-type': 'application/json' } : {},
    body,
  });
  return new NextResponse(await r.text(), { status: r.status });
}
