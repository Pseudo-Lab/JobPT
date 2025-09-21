import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Canvas 패키지를 서버사이드에서만 사용하도록 설정
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        canvas: false,
        fs: false,
      };
    }
    return config;
  },
  
  // 성능 최적화
  experimental: {
    optimizePackageImports: ['react-pdf', 'pdfjs-dist'],
  },
  
  // 이미지 최적화
  images: {
    formats: ['image/webp', 'image/avif'],
  },
  
  // 압축
  compress: true,
  
  // 환경 변수 검증
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
};

export default nextConfig;
