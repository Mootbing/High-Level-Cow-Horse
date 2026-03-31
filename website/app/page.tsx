import SmoothScroller from "@/components/SmoothScroller";
import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Marquee from "@/components/Marquee";
import Problem from "@/components/Problem";
import Services from "@/components/Services";
import Process from "@/components/Process";
import Work from "@/components/Work";
import Stats from "@/components/Stats";
import Testimonials from "@/components/Testimonials";
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
        <Problem />
        <div className="section-divider" />
        <Services />
        <div className="section-divider" />
        <Process />
        <Stats />
        <Work />
        <div className="section-divider" />
        <Testimonials />
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
