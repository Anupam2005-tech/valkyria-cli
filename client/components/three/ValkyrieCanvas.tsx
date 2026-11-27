"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { scrollStore } from "@/lib/scroll-store";
import { Logo } from "@/components/ui/Logo";

export function ValkyrieCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [webglFailed, setWebglFailed] = useState(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const isMobile = window.innerWidth <= 720;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch {
      setWebglFailed(true);
      return;
    }

    const dpr = isMobile ? 1 : Math.min(window.devicePixelRatio || 1, 1.75);
    renderer.setPixelRatio(dpr);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      window.innerWidth / window.innerHeight,
      0.1,
      120
    );

    // Lighting: soft cloud-white key, yellow rim from behind, low ambient
    const ambient = new THREE.AmbientLight(0xf2f4f1, 0.25);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0xf2f4f1, 1.6);
    keyLight.position.set(5, 6, 7);
    scene.add(keyLight);

    const rimLight = new THREE.PointLight(0xffc929, 4.5, 28);
    rimLight.position.set(-4, 2, -6);
    scene.add(rimLight);

    // Materials
    const graphiteMat = new THREE.MeshStandardMaterial({
      color: 0x26282c,
      metalness: 0.65,
      roughness: 0.35,
    });
    const edgeMat = new THREE.LineBasicMaterial({
      color: 0xffc929,
      transparent: true,
      opacity: 0.85,
    });
    const cloudWireMat = new THREE.MeshStandardMaterial({
      color: 0xf2f4f1,
      metalness: 0.4,
      roughness: 0.5,
      transparent: true,
      opacity: 0.28,
    });
    const sunEmissiveMat = new THREE.MeshStandardMaterial({
      color: 0xffc929,
      emissive: 0xffc929,
      emissiveIntensity: 0.75,
      metalness: 0.3,
      roughness: 0.25,
    });

    // 1. Hero Group: 6-plate Hex Shield + Feather-blade Wings + 3 Orbiting Provider Orbs
    const heroGroup = new THREE.Group();
    heroGroup.position.set(1.9, 0.1, 0);
    scene.add(heroGroup);

    const shieldPlates: THREE.Mesh[] = [];
    const plateGeo = new THREE.CylinderGeometry(1.15, 1.15, 0.12, 6);
    for (let i = 0; i < 6; i++) {
      const plate = new THREE.Mesh(plateGeo, i === 2 ? sunEmissiveMat.clone() : graphiteMat.clone());
      plate.rotation.x = Math.PI / 2;
      plate.position.z = (i - 2.5) * 0.16;
      plate.scale.setScalar(1 - Math.abs(i - 2.5) * 0.08);
      const edges = new THREE.EdgesGeometry(plateGeo);
      plate.add(new THREE.LineSegments(edges, edgeMat));
      heroGroup.add(plate);
      shieldPlates.push(plate);
    }

    // Feather-blade wings
    const leftWing = new THREE.Group();
    const rightWing = new THREE.Group();
    const bladeGeo = new THREE.BoxGeometry(1.4, 0.14, 0.06);
    for (let i = 0; i < 4; i++) {
      const lBlade = new THREE.Mesh(bladeGeo, graphiteMat);
      lBlade.position.set(-1.5 - i * 0.22, 0.5 - i * 0.32, -0.1 * i);
      lBlade.rotation.z = 0.28 - i * 0.14;
      lBlade.add(new THREE.LineSegments(new THREE.EdgesGeometry(bladeGeo), edgeMat));
      leftWing.add(lBlade);

      const rBlade = new THREE.Mesh(bladeGeo, graphiteMat);
      rBlade.position.set(1.5 + i * 0.22, 0.5 - i * 0.32, -0.1 * i);
      rBlade.rotation.z = -0.28 + i * 0.14;
      rBlade.add(new THREE.LineSegments(new THREE.EdgesGeometry(bladeGeo), edgeMat));
      rightWing.add(rBlade);
    }
    heroGroup.add(leftWing, rightWing);

    // 3 orbiting provider orbs on tilted rings
    const orbGroup = new THREE.Group();
    const orbitRingGeo = new THREE.TorusGeometry(2.35, 0.015, 8, 64);
    const orbitRing = new THREE.Mesh(orbitRingGeo, cloudWireMat);
    orbitRing.rotation.x = 1.1;
    orbitRing.rotation.y = 0.4;
    orbGroup.add(orbitRing);

    const orbGeo = new THREE.OctahedronGeometry(0.16, 1);
    const orbs: THREE.Mesh[] = [];
    for (let i = 0; i < 3; i++) {
      const orb = new THREE.Mesh(orbGeo, i === 0 ? sunEmissiveMat : cloudWireMat);
      orbGroup.add(orb);
      orbs.push(orb);
    }
    heroGroup.add(orbGroup);

    // 2. Tunnel Rings (How it works)
    const tunnelGroup = new THREE.Group();
    tunnelGroup.position.set(0, -4.5, -14);
    scene.add(tunnelGroup);
    const tunnelRings: THREE.Mesh[] = [];
    const ringGeo = new THREE.TorusGeometry(2.4, 0.06, 12, 48);
    for (let i = 0; i < 4; i++) {
      const r = new THREE.Mesh(ringGeo, graphiteMat.clone());
      r.position.z = -i * 3.8;
      tunnelGroup.add(r);
      tunnelRings.push(r);
    }

    // 3. Setup ascending hex stairs + yellow spear
    const stairsGroup = new THREE.Group();
    stairsGroup.position.set(1.4, -10.5, -30);
    scene.add(stairsGroup);
    const stepHexGeo = new THREE.CylinderGeometry(0.75, 0.75, 0.16, 6);
    const stepMeshes: THREE.Mesh[] = [];
    for (let i = 0; i < 5; i++) {
      const m = new THREE.Mesh(stepHexGeo, graphiteMat.clone());
      m.position.set((i - 2) * 0.9, i * 0.65, -i * 0.8);
      m.add(new THREE.LineSegments(new THREE.EdgesGeometry(stepHexGeo), edgeMat));
      stairsGroup.add(m);
      stepMeshes.push(m);
    }
    const spearGeo = new THREE.ConeGeometry(0.18, 0.7, 4);
    const spear = new THREE.Mesh(spearGeo, sunEmissiveMat);
    stairsGroup.add(spear);

    // 4. Dust / Shard Particles (InstancedMesh)
    const particleCount = isMobile ? 300 : 800;
    const shardGeo = new THREE.TetrahedronGeometry(0.055, 0);
    const shardInstanced = new THREE.InstancedMesh(shardGeo, cloudWireMat, particleCount);
    const dummy = new THREE.Object3D();
    const shardPositions: { x: number; y: number; z: number; speed: number }[] = [];
    for (let i = 0; i < particleCount; i++) {
      const p = {
        x: (Math.random() - 0.5) * 20,
        y: (Math.random() - 0.5) * 20 - 4,
        z: (Math.random() - 0.5) * 42 - 10,
        speed: 0.2 + Math.random() * 0.6,
      };
      shardPositions.push(p);
      dummy.position.set(p.x, p.y, p.z);
      dummy.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0);
      dummy.updateMatrix();
      shardInstanced.setMatrixAt(i, dummy.matrix);
    }
    scene.add(shardInstanced);

    // Camera CatmullRomCurve3 waypoints across 7 sections
    const cameraCurve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(0.4, 0.3, 6.2),   // 0 Hero
      new THREE.Vector3(0.0, -4.4, -11.5), // 1 How it works
      new THREE.Vector3(-2.5, -5.8, -19),  // 2 Different (recedes)
      new THREE.Vector3(1.8, 0.2, 5.2),    // 3 Under the hood (orbits shield)
      new THREE.Vector3(-1.2, -3.0, -4.0), // 4 Q&A (calm)
      new THREE.Vector3(1.2, -9.2, -25.5), // 5 Setup stairs
      new THREE.Vector3(0.0, 0.0, 7.6),    // 6 Footer frontal pull-back
    ]);

    let mouseX = 0;
    let mouseY = 0;
    const onMouseMove = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = (e.clientY / window.innerHeight - 0.5) * 2;
    };
    window.addEventListener("mousemove", onMouseMove, { passive: true });

    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", onResize);

    const clock = new THREE.Clock();
    const targetCamPos = new THREE.Vector3();
    let rafId = 0;
    let isHidden = document.hidden;

    const onVisibility = () => {
      isHidden = document.hidden;
    };
    document.addEventListener("visibilitychange", onVisibility);

    const renderFrame = () => {
      rafId = requestAnimationFrame(renderFrame);
      if (isHidden) return;

      const elapsed = clock.getElapsedTime();
      const { progress, section, velocity } = scrollStore.getState();

      // Sample curve
      const safeP = Math.max(0, Math.min(0.999, progress));
      cameraCurve.getPointAt(safeP, targetCamPos);

      const dt = Math.min(clock.getDelta(), 0.05) || 0.016;
      camera.position.x = THREE.MathUtils.damp(
        camera.position.x,
        targetCamPos.x + mouseX * 0.35,
        4,
        dt
      );
      camera.position.y = THREE.MathUtils.damp(
        camera.position.y,
        targetCamPos.y - mouseY * 0.25,
        4,
        dt
      );
      camera.position.z = THREE.MathUtils.damp(camera.position.z, targetCamPos.z, 4, dt);

      // Look target based on section
      if (section === 1) {
        camera.lookAt(0, -4.5, -24);
      } else if (section === 5) {
        camera.lookAt(1.4, -9.2, -31);
      } else {
        camera.lookAt(heroGroup.position.x * 0.35, heroGroup.position.y * 0.35, 0);
      }

      // Hero shield explode on Under The Hood (section 3) & fan wings on scroll
      const explodeFactor = section === 3 ? 1 : 0;
      shieldPlates.forEach((plate, i) => {
        const targetY = explodeFactor * (i - 2.5) * 0.52;
        plate.position.y = THREE.MathUtils.damp(plate.position.y, targetY, 5, dt);
        const mat = plate.material as THREE.MeshStandardMaterial;
        const isActive = section === 3 ? i === Math.floor((progress * 20) % 6) : i === 2;
        mat.emissive.setHex(isActive ? 0xffc929 : 0x000000);
        mat.emissiveIntensity = isActive ? 0.55 : 0;
      });

      // Wings fan open with scroll + velocity micro-rotation
      const fanAngle = Math.min(0.45, progress * 1.4);
      leftWing.rotation.y = THREE.MathUtils.damp(leftWing.rotation.y, -fanAngle, 5, dt);
      rightWing.rotation.y = THREE.MathUtils.damp(rightWing.rotation.y, fanAngle, 5, dt);
      heroGroup.rotation.y = Math.sin(elapsed * 0.45) * 0.14 + velocity * 0.002;

      // Orbiting orbs
      orbs.forEach((orb, idx) => {
        const angle = elapsed * (0.65 + idx * 0.15) + idx * ((Math.PI * 2) / 3);
        orb.position.set(
          Math.cos(angle) * 2.35,
          Math.sin(angle) * 0.85,
          Math.sin(angle) * 2.0
        );
      });

      // Tunnel ring active highlight
      const activeRing = Math.floor((progress * 10) % 4);
      tunnelRings.forEach((ring, idx) => {
        const mat = ring.material as THREE.MeshStandardMaterial;
        mat.emissive.setHex(idx === activeRing ? 0xffc929 : 0x000000);
        mat.emissiveIntensity = idx === activeRing ? 0.65 : 0;
      });

      // Setup spear climbing stairs
      const stepFloat = ((progress * 8) % 5);
      const stepIdx = Math.floor(stepFloat);
      spear.position.set(
        (stepFloat - 2) * 0.9,
        stepFloat * 0.65 + 0.6,
        -stepFloat * 0.8
      );
      stepMeshes.forEach((m, idx) => {
        const mat = m.material as THREE.MeshStandardMaterial;
        mat.emissive.setHex(idx <= stepIdx ? 0xffc929 : 0x000000);
        mat.emissiveIntensity = idx <= stepIdx ? 0.35 : 0;
      });

      renderer.render(scene, camera);
    };

    if (reduced) {
      camera.position.copy(cameraCurve.getPointAt(0));
      camera.lookAt(0.7, 0, 0);
      renderer.render(scene, camera);
    } else {
      rafId = requestAnimationFrame(renderFrame);
    }

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", onVisibility);
      renderer.dispose();
      if (renderer.domElement.parentElement === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  if (webglFailed) {
    return (
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 flex items-center justify-end pr-16 opacity-20"
      >
        <Logo size={240} className="text-[#F2F4F1]" />
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0"
    />
  );
}

