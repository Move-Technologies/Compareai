// import type { NextConfig } from "next";

const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  distDir: "build", // Specifies the output directory as "build"
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: 'https://3.227.241.228/:path*', // Now using HTTPS
  //     },
  //   ];
  // },

  output: "export", // Specifies export mode
};

export default nextConfig;
