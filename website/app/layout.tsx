import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clarmi Design Studio — Award-Winning Websites for Small Businesses",
  description:
    "Award-winning design studio building custom websites that make small businesses look like big ones. Founded by a CSS Design Awards recipient. $250 to launch.",
  openGraph: {
    title: "Clarmi Design Studio",
    description:
      "Custom websites that make small businesses look like big ones. $250 to launch.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
