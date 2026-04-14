import { NextResponse } from "next/server";
import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request) {
  return updateSession(request);
}

export const config = {
  matcher: ["/dashboard/:path*", "/signin", "/signup", "/auth/callback"],
};
