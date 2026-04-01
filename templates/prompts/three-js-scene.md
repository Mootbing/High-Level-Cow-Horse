# Three.js Scene Generation Reference

Reference for generating React Three Fiber (R3F) scenes in client websites.
Every 3D scene must be: industry-appropriate, performant, scroll-interactive, and mobile-safe.

## Core Setup Pattern

Every Three.js scene follows this exact pattern:

```tsx
// components/Scene3D.tsx — ALWAYS 'use client', ALWAYS dynamic import
'use client'

import { useRef, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Float, Environment, useScroll } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'

function SceneContent() {
  const meshRef = useRef<THREE.Mesh>(null)
  const { viewport } = useThree()
  
  useFrame((state, delta) => {
    if (!meshRef.current) return
    meshRef.current.rotation.y += delta * 0.15
    // Mouse parallax
    meshRef.current.position.x = THREE.MathUtils.lerp(
      meshRef.current.position.x,
      (state.pointer.x * viewport.width) / 4,
      0.05
    )
    meshRef.current.position.y = THREE.MathUtils.lerp(
      meshRef.current.position.y,
      (state.pointer.y * viewport.height) / 4,
      0.05
    )
  })

  return (
    <>
      <Environment preset="city" />
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 5, 5]} intensity={1.5} />
      
      <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.5}>
        <mesh ref={meshRef}>
          {/* Geometry + Material here */}
        </mesh>
      </Float>

      <EffectComposer>
        <Bloom luminanceThreshold={0.8} intensity={0.4} levels={3} mipmapBlur />
      </EffectComposer>
    </>
  )
}

export default function Scene3D() {
  return (
    <Canvas
      camera={{ position: [0, 0, 5], fov: 45 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      dpr={[1, 2]}
    >
      <SceneContent />
    </Canvas>
  )
}
```

```tsx
// In Hero.tsx — dynamic import, NEVER server-render Three.js
import dynamic from 'next/dynamic'

const Scene3D = dynamic(() => import('@/components/Scene3D'), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-background" />,
})
```

## Scene Recipes by Industry

### Glass Geometric (Professional / Law / Finance)
```tsx
<mesh>
  <icosahedronGeometry args={[1.5, 1]} />
  <meshPhysicalMaterial
    transmission={1}
    thickness={2}
    roughness={0}
    ior={2.4}
    chromaticAberration={0.4}
    envMapIntensity={2}
    color="#ffffff"
  />
</mesh>
// Post-processing: ChromaticAberration + Vignette
// Lighting: cool directional + rim light
// Colors: glass is neutral, refracts environment
```

### Warm Organic (Restaurant / Bakery / Cafe)
```tsx
// Floating spheres with warm materials
{[...Array(12)].map((_, i) => (
  <Float key={i} speed={0.5 + i * 0.1} floatIntensity={0.3}>
    <mesh position={[
      Math.sin(i * 0.8) * 3,
      Math.cos(i * 0.5) * 2,
      Math.sin(i * 1.2) * 1.5
    ]}>
      <sphereGeometry args={[0.2 + Math.random() * 0.3, 32, 32]} />
      <meshStandardMaterial
        color={warmColors[i % warmColors.length]}
        roughness={0.4}
        metalness={0.1}
      />
    </mesh>
  </Float>
))}
// Post-processing: Bloom (warm, high threshold)
// Lighting: warm point lights (amber, orange)
// No chromatic aberration — keep it warm and inviting
```

### Iridescent Fluid (Salon / Beauty / Spa)
```tsx
<mesh>
  <torusKnotGeometry args={[1, 0.4, 256, 64]} />
  <meshPhysicalMaterial
    transmission={0.9}
    thickness={1.5}
    roughness={0.05}
    ior={1.5}
    iridescence={1}
    iridescenceIOR={1.8}
    iridescenceThicknessRange={[100, 800]}
    color="#f0e6ff"
    envMapIntensity={2}
  />
</mesh>
// Post-processing: Bloom (soft) + ChromaticAberration (very subtle)
// Lighting: soft pink/lavender point lights
```

### Wireframe Data (Tech / SaaS / AI)
```tsx
// Network of connected nodes
function DataNetwork() {
  const nodes = useMemo(() => 
    Array.from({ length: 50 }, () => ({
      pos: new THREE.Vector3(
        (Math.random() - 0.5) * 6,
        (Math.random() - 0.5) * 4,
        (Math.random() - 0.5) * 4,
      ),
      connections: [] as number[],
    })),
    []
  )

  // Connect nodes within distance threshold
  const lines = useMemo(() => {
    const positions: number[] = []
    nodes.forEach((node, i) => {
      nodes.forEach((other, j) => {
        if (i >= j) return
        if (node.pos.distanceTo(other.pos) < 1.5) {
          positions.push(
            node.pos.x, node.pos.y, node.pos.z,
            other.pos.x, other.pos.y, other.pos.z,
          )
        }
      })
    })
    return new Float32Array(positions)
  }, [nodes])

  return (
    <group>
      {nodes.map((node, i) => (
        <mesh key={i} position={node.pos}>
          <sphereGeometry args={[0.04, 16, 16]} />
          <meshBasicMaterial color="#00ff88" />
        </mesh>
      ))}
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[lines, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color="#00ff8844" transparent opacity={0.3} />
      </lineSegments>
    </group>
  )
}
// Post-processing: Bloom (high, neon glow) + Noise (subtle scanline)
// Background: dark (nearly black)
```

### Golden Architecture (Real Estate / Luxury)
```tsx
<mesh>
  <boxGeometry args={[1.5, 2, 1.5]} />
  <meshPhysicalMaterial
    color="#d4a574"
    metalness={0.6}
    roughness={0.2}
    clearcoat={1}
    clearcoatRoughness={0.05}
  />
</mesh>
// Multiple geometric forms (columns, arches) as a composition
// Lighting: warm directional (golden hour angle), subtle ambient
// Post-processing: Bloom (warm), Vignette
```

## Scroll-Driven 3D Interactions

### Camera Path on Scroll
```tsx
import { useScroll } from '@react-three/drei'
import * as THREE from 'three'

function ScrollCamera() {
  const scroll = useScroll()
  const cameraPath = useMemo(() => new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 5),    // Start: front view
    new THREE.Vector3(3, 1, 3),    // Section 2: orbit right
    new THREE.Vector3(0, 2, 2),    // Section 3: above
    new THREE.Vector3(-2, 0, 4),   // Section 4: orbit left
    new THREE.Vector3(0, 0, 5),    // End: back to front
  ]), [])

  useFrame(({ camera }) => {
    const t = scroll.offset // 0-1 based on scroll position
    const point = cameraPath.getPointAt(t)
    camera.position.copy(point)
    camera.lookAt(0, 0, 0)
  })

  return null
}

// Usage: wrap Canvas contents in <ScrollControls pages={5}>
```

### Object Morph on Scroll
```tsx
function MorphingObject() {
  const scroll = useScroll()
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame(() => {
    if (!meshRef.current) return
    const t = scroll.offset
    
    // Scale morphs from sphere to stretched form
    meshRef.current.scale.set(
      1 + t * 0.5,
      1 + Math.sin(t * Math.PI) * 0.3,
      1 + t * 0.5
    )
    
    // Material shifts
    const mat = meshRef.current.material as THREE.MeshPhysicalMaterial
    mat.roughness = THREE.MathUtils.lerp(0, 0.5, t)
    mat.transmission = THREE.MathUtils.lerp(1, 0, t)
    mat.metalness = THREE.MathUtils.lerp(0, 0.8, t)
  })

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[1, 64, 64]} />
      <meshPhysicalMaterial />
    </mesh>
  )
}
```

### Particles React to Scroll
```tsx
function ScrollParticles({ count = 500 }) {
  const scroll = useScroll()
  const pointsRef = useRef<THREE.Points>(null)
  
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 10
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10
    }
    return pos
  }, [count])

  useFrame(() => {
    if (!pointsRef.current) return
    const t = scroll.offset
    // Particles expand outward as user scrolls
    pointsRef.current.scale.setScalar(1 + t * 2)
    pointsRef.current.rotation.y = t * Math.PI * 0.5
  })

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color="#ffffff" transparent opacity={0.6} sizeAttenuation />
    </points>
  )
}
```

## Post-Processing Recipes

### Premium / Luxury
```tsx
<EffectComposer>
  <Bloom luminanceThreshold={0.9} intensity={0.3} levels={3} mipmapBlur />
  <ChromaticAberration offset={[0.0003, 0.0003]} />
  <Vignette darkness={0.4} offset={0.3} />
</EffectComposer>
```

### Neon / Tech
```tsx
<EffectComposer>
  <Bloom luminanceThreshold={0.3} intensity={1.5} levels={5} mipmapBlur />
  <Noise opacity={0.05} />
</EffectComposer>
```

### Warm / Cinematic
```tsx
<EffectComposer>
  <Bloom luminanceThreshold={0.8} intensity={0.5} levels={3} mipmapBlur />
  <Vignette darkness={0.5} offset={0.2} />
</EffectComposer>
```

### Clean / Minimal
```tsx
<EffectComposer>
  <Bloom luminanceThreshold={0.95} intensity={0.2} levels={2} mipmapBlur />
</EffectComposer>
// Minimal post-processing — let the scene speak for itself
```

## GPU Quality Scaling

Detect GPU capability and scale scene quality automatically. Add `detect-gpu` package
to the scaffold (already included in dependencies).

```tsx
'use client'
import { useEffect, useState } from 'react'

type QualityTier = 'high' | 'medium' | 'low' | 'none'

export function useGPUTier(): QualityTier {
  const [tier, setTier] = useState<QualityTier>('medium') // Safe default

  useEffect(() => {
    // Quick heuristic based on device pixel ratio and screen size
    const isMobile = window.innerWidth < 768 || 'ontouchstart' in window
    if (isMobile) { setTier('none'); return } // No 3D on mobile

    // Check WebGL capabilities
    const canvas = document.createElement('canvas')
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    if (!gl) { setTier('none'); return }

    const renderer = (gl as WebGLRenderingContext).getParameter(
      (gl as WebGLRenderingContext).RENDERER
    )
    const maxTexture = (gl as WebGLRenderingContext).getParameter(
      (gl as WebGLRenderingContext).MAX_TEXTURE_SIZE
    )

    // High-end: dedicated GPU, large textures
    if (maxTexture >= 8192 && !renderer.includes('Intel')) setTier('high')
    // Medium: integrated GPU or smaller textures
    else if (maxTexture >= 4096) setTier('medium')
    // Low: minimal GPU
    else setTier('low')
  }, [])

  return tier
}
```

Apply quality tier to scene:
- **high**: full post-processing, dpr=[1,2], max geometry
- **medium**: 1 post-processing effect, dpr=[1,1.5], simpler geometry
- **low**: no post-processing, dpr=[1,1], basic geometry
- **none**: static image fallback, no Three.js

## Performance Guardrails

1. **Max 10,000 triangles** in the scene (check with `renderer.info.render.triangles`)
2. **Max 2 post-processing effects** active at once
3. **Dispose in cleanup**: every geometry, material, and texture
4. **Dynamic import with `ssr: false`** — Three.js must NEVER run on server
5. **Single Canvas per page** — use groups and visibility, not multiple canvases
6. **dpr={[1, 2]}** — limit pixel ratio on high-DPI screens
7. **`powerPreference: 'high-performance'`** on the WebGL context
8. **Fallback image on mobile**: detect with `window.innerWidth < 768`

```tsx
// Mobile detection + fallback
const [isMobile, setIsMobile] = useState(false)
useEffect(() => {
  setIsMobile(window.innerWidth < 768 || 'ontouchstart' in window)
}, [])

return isMobile ? (
  <img src="/assets/hero-fallback.png" className="object-cover w-full h-full" alt="" />
) : (
  <Scene3D />
)
```

## DO NOT

- Render Three.js on the server (causes hydration mismatch + crash)
- Use more than one Canvas element per page
- Create scenes with > 10k triangles
- Use uncompressed textures (always WebP or compressed PNG)
- Forget to dispose resources in the useEffect cleanup
- Skip the mobile fallback (3D is too heavy for most phones)
- Use `OrbitControls` for non-interactive showcases (use programmatic camera instead)
- Add complex physics simulations (heavy, unnecessary for landing pages)
- Use HDR environment maps > 2MB (use presets from drei instead)
