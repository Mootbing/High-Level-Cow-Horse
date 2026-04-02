import SmoothScroller from "@/components/SmoothScroller";
import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Marquee from "@/components/Marquee";
import Process from "@/components/Process";
import Work from "@/components/Work";
import Pricing from "@/components/Pricing";
import Founder from "@/components/Founder";
import CTA from "@/components/CTA";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <SmoothScroller>
      <Navigation />
      <main>
        <Hero />
        <Marquee />
        <Process />
        <div className="section-divider" />
        <Work />
        <div className="section-divider" />
        <Founder />
        <div className="section-divider" />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </SmoothScroller>
  );
}
