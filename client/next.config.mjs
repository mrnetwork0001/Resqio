/** @type {import('next').NextConfig} */
// The browser talks only to this Next.js server; API routes are proxied to the
// Resqio runtime, so one origin (and one public entry point) serves everything.
// Rewrites are resolved at build time: set RESQIO_API_ORIGIN before `next build`.
const API_ORIGIN = process.env.RESQIO_API_ORIGIN ?? "http://127.0.0.1:5001";

const nextConfig = {
  async rewrites() {
    return [
      { source: "/status", destination: `${API_ORIGIN}/status` },
      { source: "/cycle", destination: `${API_ORIGIN}/cycle` },
      { source: "/demo/:path*", destination: `${API_ORIGIN}/demo/:path*` },
      { source: "/sms", destination: `${API_ORIGIN}/sms` },
    ];
  },
};

export default nextConfig;
