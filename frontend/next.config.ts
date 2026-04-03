import type { NextConfig } from "next";

// We default to the LIVE GCP Cloud Run Backend if a local API URL is not explicitly passed.
// This ensures that running `npm run dev` instantly connects to the real data stream without 
// dropping ECONNREFUSED errors if the local FastAPI instance isn't active.
// The cloudbuild.yaml explicitly passes NEXT_PUBLIC_API_URL locally during Docker build.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://revsight-backend-ski7hmysfa-el.a.run.app";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
