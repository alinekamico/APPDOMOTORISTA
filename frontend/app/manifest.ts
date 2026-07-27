import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "KAMI CO. — Romaneios",
    short_name: "KAMI Romaneios",
    description: "Gestão de romaneios e entregas para transportadoras e motoristas da KAMI CO.",
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#463D3F",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
