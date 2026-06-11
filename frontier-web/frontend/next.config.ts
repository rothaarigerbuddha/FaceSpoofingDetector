import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output keeps the production Docker image small.
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "5160",
        pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "127.0.0.1",
        port: "5160",
        pathname: "/**",
      },
      {
        // Docker Compose service name — the Next.js server fetches/optimizes
        // backend images container-to-container over the internal network.
        protocol: "http",
        hostname: "backend",
        port: "5160",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
