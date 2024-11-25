import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  distDir: 'build', // Specifies the output directory as "build"
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://3.227.241.228/:path*', // Now using HTTPS
      },
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        net: false,
        tls: false,
        fs: false,
      };
    }
    return config;
  },
  output: 'export', // Specifies export mode
};

export default nextConfig;
