import type { NextConfig } from "next";

const API_HOST = process.env.API_HOST || "localhost";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `http://${API_HOST}:8000/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
