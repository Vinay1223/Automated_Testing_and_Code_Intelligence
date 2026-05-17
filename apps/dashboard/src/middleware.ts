import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublic = createRouteMatcher(['/', '/sign-in(.*)', '/sign-up(.*)', '/api/health']);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublic(req)) {
    const { protect } = await auth();
    await protect();
  }
});

export const config = {
  matcher: ['/((?!_next|.*\\..*).*)', '/(api|trpc)(.*)'],
};
