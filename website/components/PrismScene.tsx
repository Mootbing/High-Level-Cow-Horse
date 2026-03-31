"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function PrismScene() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    if (width === 0 || height === 0) return;

    // ---- Renderer (NO alpha — scene needs a background for glass refraction) ----
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    renderer.setClearColor(0xfafaf8, 1);
    container.appendChild(renderer.domElement);

    // ---- Scene + Camera ----
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xfafaf8);
    const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
    camera.position.set(0, 0.3, 7);

    // ---- Rich environment for glass refraction ----
    const envScene = new THREE.Scene();
    envScene.background = new THREE.Color(0xf5f3f0);

    // Colored gradient spheres — the prism refracts THESE through the glass
    const envSphereGeo = new THREE.SphereGeometry(1, 32, 32);
    [
      { color: 0x8b5cf6, pos: [3, 2, -4], scale: 2.5 },
      { color: 0xec4899, pos: [-3, -1, -5], scale: 3 },
      { color: 0x3b82f6, pos: [0, 3, -6], scale: 3.5 },
      { color: 0xf59e0b, pos: [4, -2, -3], scale: 2 },
      { color: 0x10b981, pos: [-4, 2, -4], scale: 2.5 },
      { color: 0xf43f5e, pos: [2, -3, -5], scale: 2 },
      { color: 0x6366f1, pos: [-2, 3, -3], scale: 1.5 },
    ].forEach(({ color, pos, scale }) => {
      const m = new THREE.Mesh(envSphereGeo, new THREE.MeshBasicMaterial({ color }));
      m.position.set(pos[0], pos[1], pos[2]);
      m.scale.setScalar(scale);
      envScene.add(m);
    });

    // Large colored backdrop planes
    const bgGeo = new THREE.PlaneGeometry(30, 30);
    [
      { color: 0xf0e6ff, pos: [0, 0, -10], rot: [0, 0, 0] },
      { color: 0xffe6f0, pos: [10, 0, 0], rot: [0, -Math.PI / 2, 0] },
      { color: 0xe6f5ff, pos: [-10, 0, 0], rot: [0, Math.PI / 2, 0] },
      { color: 0xfff5e6, pos: [0, 10, 0], rot: [Math.PI / 2, 0, 0] },
      { color: 0xe6ffe6, pos: [0, -10, 0], rot: [-Math.PI / 2, 0, 0] },
      { color: 0xf5e6ff, pos: [0, 0, 10], rot: [0, Math.PI, 0] },
    ].forEach(({ color, pos, rot }) => {
      const m = new THREE.Mesh(bgGeo, new THREE.MeshBasicMaterial({ color, side: THREE.DoubleSide }));
      m.position.set(pos[0], pos[1], pos[2]);
      m.rotation.set(rot[0], rot[1], rot[2]);
      envScene.add(m);
    });

    envScene.add(new THREE.AmbientLight(0xffffff, 3));
    const eDir = new THREE.DirectionalLight(0xffffff, 5);
    eDir.position.set(5, 5, 5);
    envScene.add(eDir);

    const pmrem = new THREE.PMREMGenerator(renderer);
    const envMap = pmrem.fromScene(envScene, 0.04).texture;
    scene.environment = envMap;
    pmrem.dispose();

    // ---- Background color orbs (visible through the glass) ----
    const orbGeo = new THREE.SphereGeometry(1, 32, 32);
    const orbs = [
      { color: 0xc4b5fd, pos: [-2, 1.5, -4], scale: 0.6, speed: 0.3 },
      { color: 0xfda4af, pos: [2.5, -0.5, -3.5], scale: 0.5, speed: 0.4 },
      { color: 0x93c5fd, pos: [0, 2, -5], scale: 0.7, speed: 0.2 },
      { color: 0xfde68a, pos: [-1.5, -1.5, -3], scale: 0.4, speed: 0.35 },
      { color: 0xa7f3d0, pos: [1.8, 1, -4.5], scale: 0.45, speed: 0.25 },
    ].map(({ color, pos, scale, speed }) => {
      const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.35 });
      const mesh = new THREE.Mesh(orbGeo, mat);
      mesh.position.set(pos[0], pos[1], pos[2]);
      mesh.scale.setScalar(scale);
      mesh.userData = { speed, baseY: pos[1], baseX: pos[0] };
      scene.add(mesh);
      return mesh;
    });

    // ---- Glass material (with dispersion for rainbow refraction!) ----
    const glass = new THREE.MeshPhysicalMaterial({
      transmission: 1,
      thickness: 3,
      roughness: 0,
      ior: 2.4,
      dispersion: 0.5,
      iridescence: 1,
      iridescenceIOR: 1.8,
      iridescenceThicknessRange: [100, 800],
      clearcoat: 1,
      clearcoatRoughness: 0,
      envMapIntensity: 2.5,
      color: new THREE.Color(0xffffff),
      specularIntensity: 1,
      specularColor: new THREE.Color(0xffffff),
      side: THREE.DoubleSide,
    });

    // ---- Main Pyramid (4-sided base, pointed top) ----
    const pyramidGeo = new THREE.ConeGeometry(1.2, 1.8, 4, 1);
    pyramidGeo.rotateY(Math.PI / 4); // align edges to camera

    const prism = new THREE.Mesh(pyramidGeo, glass);
    prism.scale.setScalar(1.0);
    scene.add(prism);

    // ---- Floating glass crystals ----
    const geoPool = [
      new THREE.IcosahedronGeometry(1, 0),
      new THREE.DodecahedronGeometry(1, 0),
      new THREE.OctahedronGeometry(1, 0),
      new THREE.TetrahedronGeometry(1, 0),
    ];

    const crystalDefs = [
      { pos: [2.6, 1.2, -0.5], scale: 0.28, speed: 1.2, gi: 0 },
      { pos: [-2.3, -0.9, 0.3], scale: 0.2, speed: 1.7, gi: 1 },
      { pos: [1.6, -1.7, -0.3], scale: 0.16, speed: 1.5, gi: 2 },
      { pos: [-1.6, 1.9, -1], scale: 0.22, speed: 1.0, gi: 3 },
      { pos: [2.8, -0.3, -1.2], scale: 0.14, speed: 2.0, gi: 2 },
    ];

    const crystals = crystalDefs.map(({ pos, scale, speed, gi }) => {
      const mat = glass.clone();
      mat.thickness = 1.5;
      mat.ior = 1.6 + Math.random() * 0.6;
      const mesh = new THREE.Mesh(geoPool[gi], mat);
      mesh.position.set(pos[0], pos[1], pos[2]);
      mesh.scale.setScalar(scale);
      mesh.userData = { speed, baseY: pos[1], baseX: pos[0] };
      scene.add(mesh);
      return mesh;
    });

    // ---- Rainbow spectrum lines (behind prism, like Pink Floyd) ----
    const spectrumGroup = new THREE.Group();
    spectrumGroup.position.set(1.8, -0.1, -0.5);
    spectrumGroup.rotation.z = -0.2;

    const spectrumColors = [0xff3333, 0xff8833, 0xffee33, 0x33dd55, 0x3388ff, 0x5533ff, 0xaa33ff];
    spectrumColors.forEach((color, i) => {
      const geo = new THREE.PlaneGeometry(4, 0.04);
      const mat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.y = (i - 3) * 0.12;
      mesh.position.x = 2;
      spectrumGroup.add(mesh);
    });
    scene.add(spectrumGroup);

    // ---- Lights ----
    scene.add(new THREE.AmbientLight(0xffffff, 0.7));

    const sun = new THREE.DirectionalLight(0xffffff, 2.5);
    sun.position.set(-4, 4, 5);
    scene.add(sun);

    const fill = new THREE.DirectionalLight(0xeeddff, 1);
    fill.position.set(3, -2, 3);
    scene.add(fill);

    const rim = new THREE.DirectionalLight(0xffd0e0, 0.6);
    rim.position.set(0, 0, -5);
    scene.add(rim);

    // Colored points for caustic-like colored reflections
    [
      { color: 0x6366f1, pos: [-2, 2, 3], i: 1.5 },
      { color: 0xec4899, pos: [2, -1, 3], i: 1 },
      { color: 0x3b82f6, pos: [0, 3, 2], i: 0.8 },
    ].forEach(({ color, pos, i: intensity }) => {
      const l = new THREE.PointLight(color, intensity, 12);
      l.position.set(pos[0], pos[1], pos[2]);
      scene.add(l);
    });

    // ---- Drag rotation (mouse + touch) ----
    let mx = 0, my = 0;
    let dragging = false;
    let dragX = 0, dragY = 0;
    let dragRotX = 0, dragRotY = 0;
    let velocityX = 0, velocityY = 0;
    let lastPointerX = 0, lastPointerY = 0;

    const onPointerDown = (e: PointerEvent) => {
      dragging = true;
      lastPointerX = e.clientX;
      lastPointerY = e.clientY;
      velocityX = 0;
      velocityY = 0;
      renderer.domElement.setPointerCapture(e.pointerId);
    };
    const onPointerMove = (e: PointerEvent) => {
      // Always update parallax
      mx = (e.clientX / window.innerWidth - 0.5) * 2;
      my = (e.clientY / window.innerHeight - 0.5) * 2;
      if (!dragging) return;
      const dx = e.clientX - lastPointerX;
      const dy = e.clientY - lastPointerY;
      velocityX = dx * 0.01;
      velocityY = dy * 0.01;
      dragRotY += dx * 0.01;
      dragRotX += dy * 0.01;
      lastPointerX = e.clientX;
      lastPointerY = e.clientY;
    };
    const onPointerUp = () => {
      dragging = false;
    };

    const el = renderer.domElement;
    el.style.touchAction = "none";
    el.addEventListener("pointerdown", onPointerDown);
    el.addEventListener("pointermove", onPointerMove);
    el.addEventListener("pointerup", onPointerUp);
    el.addEventListener("pointercancel", onPointerUp);

    // ---- Animation loop ----
    let animId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      const t = clock.getElapsedTime();

      // Apply drag velocity as inertia when not dragging
      if (!dragging) {
        dragRotY += velocityX;
        dragRotX += velocityY;
        velocityX *= 0.95;
        velocityY *= 0.95;
      }

      // Main pyramid — slow auto-rotation + drag rotation + parallax
      prism.rotation.y = t * 0.1 + dragRotY + (dragging ? 0 : mx * 0.25);
      prism.rotation.x = Math.sin(t * 0.07) * 0.12 + 0.2 + dragRotX + (dragging ? 0 : my * 0.1);
      prism.rotation.z = Math.sin(t * 0.04) * 0.04;
      prism.position.y = Math.sin(t * 0.35) * 0.1 + 0.1;

      // Crystals orbit gently
      crystals.forEach((c) => {
        const s = c.userData.speed as number;
        const by = c.userData.baseY as number;
        const bx = c.userData.baseX as number;
        c.rotation.x = t * s * 0.35;
        c.rotation.y = t * s * 0.25;
        c.rotation.z = t * s * 0.15;
        c.position.y = by + Math.sin(t * s * 0.5) * 0.2;
        c.position.x = bx + Math.sin(t * s * 0.3 + 1) * 0.08;
      });

      // Background orbs drift
      orbs.forEach((o) => {
        const s = o.userData.speed as number;
        const by = o.userData.baseY as number;
        const bx = o.userData.baseX as number;
        o.position.y = by + Math.sin(t * s) * 0.3;
        o.position.x = bx + Math.cos(t * s * 0.7) * 0.2;
      });

      // Spectrum shimmer
      spectrumGroup.children.forEach((child, i) => {
        const mat = (child as THREE.Mesh).material as THREE.MeshBasicMaterial;
        mat.opacity = 0.1 + Math.sin(t * 0.6 + i * 0.4) * 0.08;
      });

      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };
    animate();

    // ---- Resize ----
    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // ---- Cleanup ----
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", onResize);
      el.removeEventListener("pointerdown", onPointerDown);
      el.removeEventListener("pointermove", onPointerMove);
      el.removeEventListener("pointerup", onPointerUp);
      el.removeEventListener("pointercancel", onPointerUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      envMap.dispose();
      glass.dispose();
      pyramidGeo.dispose();
      orbGeo.dispose();
      envSphereGeo.dispose();
      bgGeo.dispose();
      geoPool.forEach((g) => g.dispose());
    };
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        position: "absolute",
        inset: 0,
        borderRadius: "inherit",
        overflow: "hidden",
      }}
    />
  );
}
