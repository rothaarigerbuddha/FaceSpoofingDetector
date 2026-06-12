import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function proxy(request: NextRequest) {
  // Get the token from cookies
  const token = request.cookies.get('access_token')?.value;

  const { pathname } = request.nextUrl;

  // Protect dashboard routes
  if (pathname.startsWith('/dashboard')) {
    if (!token) {
      // Redirect to login if user is not authenticated
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  // Prevent logged-in users from accessing the login/register pages
  if (pathname === '/login' || pathname === '/register') {
    if (token) {
      // Redirect to dashboard if user is already authenticated
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  // Apply middleware to dashboard, login, and register routes
  matcher: ['/dashboard/:path*', '/login', '/register'],
};
