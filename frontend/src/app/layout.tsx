import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-serif",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "BookSoul · Books that understand you",
  description: "A premium literary discovery engine matching you with books based on your unique emotional DNA, themes, and tropes.",
  keywords: ["books", "recommendation engine", "book DNA", "tropes", "reading matches", "literature"],
  authors: [{ name: "BookSoul Team" }],
  openGraph: {
    title: "BookSoul · Books that understand you",
    description: "Discover literature tailored to your exact emotional DNA, themes, and tropes.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${playfair.variable} h-full antialiased dark`}
      style={{ colorScheme: "dark" }}
    >
      <body className="min-h-full flex bg-background text-foreground overflow-hidden font-sans">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto relative">
          <Header />
          <main className="flex-1 flex flex-col px-8 py-6 max-w-7xl w-full mx-auto relative z-10">
            {children}
          </main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
