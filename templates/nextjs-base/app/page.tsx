import { HeroVideo } from '@/components/HeroVideo'
import { ParallaxSection } from '@/components/ParallaxSection'
import { ScrollCards } from '@/components/ScrollCards'
import { TextReveal } from '@/components/TextReveal'

export default function Home() {
  return (
    <main>
      <HeroVideo
        videoSrc="/hero.mp4"
        title="Your Brand, Elevated"
        subtitle="Premium digital experiences crafted by AI"
      />
      <TextReveal text="We build websites that move people." />
      <ParallaxSection
        images={['/keyframe-1.png', '/keyframe-2.png', '/keyframe-3.png']}
        title="Our Work"
      />
      <ScrollCards
        cards={[
          { title: 'Design', description: 'AI-generated visuals that captivate' },
          { title: 'Build', description: 'Next.js sites with buttery smooth scroll' },
          { title: 'Launch', description: 'Deployed to Vercel in minutes' },
        ]}
      />
    </main>
  )
}
