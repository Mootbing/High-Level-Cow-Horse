# WebGL Shader Backgrounds Reference

Lightweight WebGL shader effects for section backgrounds. These are simpler and more
performant than full Three.js scenes — use them for atmospheric section backgrounds
where a full 3D scene would be overkill.

## When to Use Shaders vs Three.js

| Use Case | Approach |
|----------|----------|
| Hero with 3D object interaction | Three.js (Scene3D) |
| Animated gradient background | Shader background |
| Noise/aurora atmosphere | Shader background |
| Particle field (simple) | Shader background |
| 3D product showcase | Three.js |
| Section ambient texture | Shader background |

## Pattern: Canvas Shader Background

A self-contained component that renders a fullscreen WebGL shader.
No Three.js required — uses raw WebGL for minimal bundle impact (~5KB vs ~200KB).

```tsx
'use client'

import { useEffect, useRef, useCallback } from 'react'

interface ShaderBackgroundProps {
  fragmentShader: string
  className?: string
  colors?: string[] // Hex colors to pass as uniforms
  speed?: number
}

export default function ShaderBackground({ 
  fragmentShader, className = '', colors = ['#000000'], speed = 1.0 
}: ShaderBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const hexToVec3 = useCallback((hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16) / 255
    const g = parseInt(hex.slice(3, 5), 16) / 255
    const b = parseInt(hex.slice(5, 7), 16) / 255
    return [r, g, b] as const
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl')
    if (!gl) return

    // Vertex shader (fullscreen quad)
    const vertSrc = `
      attribute vec2 position;
      void main() { gl_Position = vec4(position, 0.0, 1.0); }
    `

    const compile = (type: number, src: string) => {
      const shader = gl.createShader(type)!
      gl.shaderSource(shader, src)
      gl.compileShader(shader)
      return shader
    }

    const program = gl.createProgram()!
    gl.attachShader(program, compile(gl.VERTEX_SHADER, vertSrc))
    gl.attachShader(program, compile(gl.FRAGMENT_SHADER, fragmentShader))
    gl.linkProgram(program)
    gl.useProgram(program)

    // Fullscreen quad
    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW)
    const pos = gl.getAttribLocation(program, 'position')
    gl.enableVertexAttribArray(pos)
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0)

    // Uniforms
    const uTime = gl.getUniformLocation(program, 'uTime')
    const uResolution = gl.getUniformLocation(program, 'uResolution')
    const uMouse = gl.getUniformLocation(program, 'uMouse')

    // Pass colors
    colors.forEach((hex, i) => {
      const loc = gl.getUniformLocation(program, `uColor${i}`)
      if (loc) gl.uniform3fv(loc, hexToVec3(hex))
    })

    let mx = 0.5, my = 0.5
    const onMove = (e: MouseEvent) => {
      mx = e.clientX / window.innerWidth
      my = 1 - e.clientY / window.innerHeight
    }
    window.addEventListener('mousemove', onMove)

    let animId: number
    const startTime = performance.now()

    const render = () => {
      canvas.width = canvas.clientWidth * Math.min(devicePixelRatio, 2)
      canvas.height = canvas.clientHeight * Math.min(devicePixelRatio, 2)
      gl.viewport(0, 0, canvas.width, canvas.height)

      gl.uniform1f(uTime, ((performance.now() - startTime) / 1000) * speed)
      gl.uniform2f(uResolution, canvas.width, canvas.height)
      gl.uniform2f(uMouse, mx, my)

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      animId = requestAnimationFrame(render)
    }
    render()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('mousemove', onMove)
      gl.deleteProgram(program)
    }
  }, [fragmentShader, colors, speed, hexToVec3])

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 w-full h-full ${className}`}
      style={{ pointerEvents: 'none' }}
    />
  )
}
```

## Shader Recipes

### 1. Animated Noise Gradient

Smooth morphing gradient using simplex noise. Great for hero backgrounds.

```glsl
precision highp float;
uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uColor0; // Primary brand color
uniform vec3 uColor1; // Secondary brand color

// Simplex noise function
vec3 mod289(vec3 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0/289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
  m = m*m; m = m*m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0*a0+h*h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution.xy;
  float n = snoise(uv * 3.0 + uTime * 0.15);
  float n2 = snoise(uv * 5.0 - uTime * 0.1);
  float blend = smoothstep(-0.5, 0.5, n + n2 * 0.5);
  vec3 color = mix(uColor0, uColor1, blend);
  // Subtle vignette
  float vignette = 1.0 - smoothstep(0.3, 0.9, length(uv - 0.5));
  color *= 0.8 + 0.2 * vignette;
  gl_FragColor = vec4(color, 1.0);
}
```

### 2. Aurora / Northern Lights

Flowing colored light bands. Great for premium/luxury sections.

```glsl
precision highp float;
uniform float uTime;
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform vec3 uColor0;
uniform vec3 uColor1;

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution.xy;
  uv.x *= uResolution.x / uResolution.y;

  float t = uTime * 0.3;
  
  // Layer multiple sine waves
  float wave1 = sin(uv.x * 4.0 + t) * 0.3 + sin(uv.x * 7.0 - t * 0.7) * 0.15;
  float wave2 = sin(uv.x * 3.0 - t * 0.5) * 0.25 + cos(uv.x * 6.0 + t * 0.8) * 0.1;
  float wave3 = sin(uv.x * 5.0 + t * 1.2) * 0.2;

  // Aurora bands
  float band1 = smoothstep(0.02, 0.0, abs(uv.y - 0.5 - wave1));
  float band2 = smoothstep(0.03, 0.0, abs(uv.y - 0.4 - wave2));
  float band3 = smoothstep(0.015, 0.0, abs(uv.y - 0.6 - wave3));

  vec3 color = vec3(0.02); // Near-black base
  color += uColor0 * band1 * 2.0;
  color += uColor1 * band2 * 1.5;
  color += mix(uColor0, uColor1, 0.5) * band3 * 1.0;

  // Mouse influence
  float mouseGlow = smoothstep(0.4, 0.0, length(uv - uMouse));
  color += mix(uColor0, uColor1, 0.5) * mouseGlow * 0.15;

  gl_FragColor = vec4(color, 1.0);
}
```

### 3. Liquid / Fluid Background

Organic flowing fluid. Great for beauty/spa/organic brands.

```glsl
precision highp float;
uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uColor0;
uniform vec3 uColor1;

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution.xy;
  float t = uTime * 0.2;

  // Domain warping for fluid look
  vec2 p = uv * 3.0;
  float x = sin(p.x + t) + sin(p.y * 0.7 + t * 0.7);
  float y = cos(p.y + t * 0.8) + cos(p.x * 0.6 - t * 0.6);
  float z = sin((p.x + p.y) * 0.5 + t * 0.5);
  
  float pattern = sin(x + y + z) * 0.5 + 0.5;
  float pattern2 = cos(x * 0.7 - y * 0.3 + z) * 0.5 + 0.5;

  vec3 color = mix(uColor0, uColor1, pattern);
  color = mix(color, uColor1 * 1.3, pattern2 * 0.3);
  
  // Soft glow
  color *= 0.6 + 0.4 * smoothstep(0.3, 0.7, pattern);

  gl_FragColor = vec4(color, 1.0);
}
```

### 4. Grid / Matrix (Tech backgrounds)

Subtle animated grid with pulsing intersections.

```glsl
precision highp float;
uniform float uTime;
uniform vec2 uResolution;
uniform vec3 uColor0; // Grid color (e.g. cyan #00ffcc)

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution.xy;
  uv.x *= uResolution.x / uResolution.y;

  // Grid
  vec2 grid = fract(uv * 20.0);
  float lineX = smoothstep(0.02, 0.0, abs(grid.x - 0.5) - 0.48);
  float lineY = smoothstep(0.02, 0.0, abs(grid.y - 0.5) - 0.48);
  float gridLine = max(lineX, lineY);

  // Intersection glow
  vec2 cell = floor(uv * 20.0);
  float pulse = sin(cell.x * 0.5 + cell.y * 0.7 + uTime * 2.0) * 0.5 + 0.5;
  float intersection = lineX * lineY * pulse;

  vec3 color = vec3(0.02); // Dark base
  color += uColor0 * gridLine * 0.15;
  color += uColor0 * intersection * 0.8;

  // Scan line effect
  float scan = smoothstep(0.01, 0.0, abs(fract(uv.y * 2.0 - uTime * 0.3) - 0.5) - 0.49);
  color += uColor0 * scan * 0.3;

  gl_FragColor = vec4(color, 1.0);
}
```

## Usage in Sections

```tsx
// In any section component
import ShaderBackground from '@/components/ShaderBackground'

// Import the shader as a string
const noiseGradientShader = `...` // paste the GLSL code

export default function AboutSection() {
  return (
    <section className="relative min-h-screen flex items-center">
      <ShaderBackground
        fragmentShader={noiseGradientShader}
        colors={['#1a1a2e', '#16213e']} // Brand colors
        speed={0.8}
      />
      <div className="relative z-10 px-6 md:px-16">
        {/* Section content */}
      </div>
    </section>
  )
}
```

## Shader Selection by Industry

| Industry | Shader | Speed | Colors |
|----------|--------|-------|--------|
| Restaurant | Noise Gradient | 0.3 (very slow) | Warm: cream → amber |
| Law/Finance | Aurora | 0.2 | Cool: navy → silver |
| Salon/Beauty | Liquid | 0.4 | Soft: pink → lavender |
| Tech/SaaS | Grid | 1.0 | Neon: cyan → blue |
| Real Estate | Noise Gradient | 0.2 | Golden: gold → cream |
| Creative | Any — be bold | 0.8 | Brand accent colors |

## Performance Notes

- Canvas shaders are ~5KB bundled vs ~200KB for Three.js
- Run on GPU — no main thread impact
- Use `Math.min(devicePixelRatio, 2)` to cap resolution
- Set `pointerEvents: 'none'` on the canvas so content is clickable
- On mobile: consider reducing to half resolution or using CSS gradients instead
