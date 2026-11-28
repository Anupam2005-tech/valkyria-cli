'use client';

import { useEffect, useRef, type CSSProperties } from 'react';

export interface OrbProps {
  colors?: string[];
  hue?: number;
  backgroundColor?: string;
  size?: number;
  glow?: number;
  bleed?: number;
  wobble?: number;
  highlight?: number;
  trail?: number;
  tiltX?: number;
  tiltY?: number;
  speed?: number;
  hoverIntensity?: number;
  rotateOnHover?: boolean;
  forceHoverState?: boolean;
  followCursor?: boolean;
  clickPulse?: boolean;
  intro?: boolean;
  opacity?: number;
  paused?: boolean;
  dpr?: number;
  className?: string;
  style?: CSSProperties;
}

type Settings = {
  colors: string[];
  hue: number;
  backgroundColor: string;
  size: number;
  glow: number;
  bleed: number;
  wobble: number;
  highlight: number;
  trail: number;
  tiltX: number;
  tiltY: number;
  speed: number;
  hoverIntensity: number;
  rotateOnHover: boolean;
  forceHoverState: boolean;
  followCursor: boolean;
  clickPulse: boolean;
  intro: boolean;
  opacity: number;
  paused: boolean;
};

const VERT = `#version 300 es
in vec2 position;
out vec2 vUv;
void main() {
  vUv = position * 0.5 + 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}`;

const FRAG = `#version 300 es
precision highp float;

uniform float iTime;
uniform vec3 iResolution;
uniform float hue;
uniform float hover;
uniform float rot;
uniform float hoverIntensity;
uniform vec3 backgroundColor;
uniform vec3 color1;
uniform vec3 color2;
uniform vec3 color3;
uniform float orbSize;
uniform float glowAmount;
uniform float bleedAmount;
uniform float wobbleAmount;
uniform float highlightAmount;
uniform float trailAmount;
uniform float tiltX;
uniform float tiltY;
uniform float hoverAngle;
uniform float followMix;
uniform float pulse;
uniform float introScale;
uniform float introGlow;
uniform float opacity;

in vec2 vUv;
out vec4 fragColor;

vec3 rgb2yiq(vec3 c) {
  float y = dot(c, vec3(0.299, 0.587, 0.114));
  float i = dot(c, vec3(0.596, -0.274, -0.322));
  float q = dot(c, vec3(0.211, -0.523, 0.312));
  return vec3(y, i, q);
}

vec3 yiq2rgb(vec3 c) {
  float r = c.x + 0.956 * c.y + 0.621 * c.z;
  float g = c.x - 0.272 * c.y - 0.647 * c.z;
  float b = c.x - 1.106 * c.y + 1.703 * c.z;
  return vec3(r, g, b);
}

vec3 adjustHue(vec3 color, float hueDeg) {
  float hueRad = hueDeg * 3.14159265 / 180.0;
  vec3 yiq = rgb2yiq(color);
  float cosA = cos(hueRad);
  float sinA = sin(hueRad);
  float i = yiq.y * cosA - yiq.z * sinA;
  float q = yiq.y * sinA + yiq.z * cosA;
  yiq.y = i;
  yiq.z = q;
  return yiq2rgb(yiq);
}

vec3 hash33(vec3 p3) {
  p3 = fract(p3 * vec3(0.1031, 0.11369, 0.13787));
  p3 += dot(p3, p3.yxz + 19.19);
  return -1.0 + 2.0 * fract(vec3(p3.x + p3.y, p3.x + p3.z, p3.y + p3.z) * p3.zyx);
}

float snoise3(vec3 p) {
  const float K1 = 0.333333333;
  const float K2 = 0.166666667;
  vec3 i = floor(p + (p.x + p.y + p.z) * K1);
  vec3 d0 = p - (i - (i.x + i.y + i.z) * K2);
  vec3 e = step(vec3(0.0), d0 - d0.yzx);
  vec3 i1 = e * (1.0 - e.zxy);
  vec3 i2 = 1.0 - e.zxy * (1.0 - e);
  vec3 d1 = d0 - (i1 - K2);
  vec3 d2 = d0 - (i2 - K1);
  vec3 d3 = d0 - 0.5;
  vec4 h = max(0.6 - vec4(dot(d0, d0), dot(d1, d1), dot(d2, d2), dot(d3, d3)), 0.0);
  vec4 n = h * h * h * h * vec4(dot(d0, hash33(i)), dot(d1, hash33(i + i1)), dot(d2, hash33(i + i2)), dot(d3, hash33(i + 1.0)));
  return dot(vec4(31.316), n);
}

vec4 extractAlpha(vec3 colorIn) {
  float a = max(max(colorIn.r, colorIn.g), colorIn.b);
  return vec4(colorIn.rgb / (a + 1e-5), a);
}

const float innerRadius = 0.6;
const float noiseScale = 0.65;

float light1(float intensity, float attenuation, float dist) {
  return intensity / (1.0 + dist * attenuation);
}

float light2(float intensity, float attenuation, float dist) {
  return intensity / (1.0 + dist * dist * attenuation);
}

vec4 draw(vec2 uv) {
  vec3 c1 = adjustHue(color1, hue);
  vec3 c2 = adjustHue(color2, hue);
  vec3 c3 = adjustHue(color3, hue);

  float ang = atan(uv.y, uv.x);
  float len = length(uv);
  float v0, v1, v2, v3, cl;
  float r0, d0, n0;
  float d;

  float idleTime = iTime * 0.5;
  float idleGlow = 0.5 + 0.5 * sin(idleTime);
  float idleBreath = sin(idleTime * 1.3) * 0.015 * wobbleAmount;

  n0 = snoise3(vec3(uv * noiseScale, iTime * 0.5)) * 0.5 + 0.5;
  r0 = mix(mix(innerRadius, 1.0, 0.4), mix(innerRadius, 1.0, 0.6), n0);
  r0 += idleBreath + pulse * 0.06;

  vec2 uvLight = vec2(uv.x, uv.y);
  d0 = distance(uvLight, (r0 / max(len, 1e-4)) * uvLight);
  v0 = light1(1.0 + idleGlow * 0.12 + pulse * 0.4, 10.0 / max(glowAmount, 0.05), d0);
  v0 *= smoothstep(r0 * 1.05, r0, len);
  float innerFade = smoothstep(r0 * (0.72 - 0.14 * bleedAmount), r0 * 0.96, len);
  float bgLum = dot(backgroundColor, vec3(0.299, 0.587, 0.114));
  float darkBg = 1.0 - smoothstep(0.35, 0.65, bgLum);
  v0 *= mix(1.0, innerFade, darkBg);

  cl = cos(ang + iTime * 2.0) * 0.5 + 0.5;

  float baseA = iTime * -1.0;
  float a = baseA;
  float trailFactor = clamp(trailAmount, 0.0, 1.0);
  if (followMix > 0.001) {
    float diff = mod(hoverAngle - baseA + 3.14159265, 6.2831853) - 3.14159265;
    a = baseA + diff * followMix;
  }
  vec2 pos = vec2(cos(a), sin(a)) * r0;
  d = distance(uv, pos);

  float tailDiff = mod(a - ang, 6.2831853);
  float tailArc = exp(-tailDiff * (3.2 - 1.5 * trailFactor)) * smoothstep(0.35, 0.05, abs(len - r0));
  v1 = light2(1.5 * highlightAmount * (1.0 + pulse * 0.5), 5.0, d) + tailArc * 0.28 * trailFactor * highlightAmount;
  v1 *= light1(1.0, 50.0, d0);

  v2 = smoothstep(1.0, mix(innerRadius, 1.0, n0 * 0.5), len);
  v3 = smoothstep(innerRadius, mix(innerRadius, 1.0, 0.5), len);

  vec3 col = mix(c1, c2, cl);
  col = mix(c3, col, v0);
  col = (col + v1) * v2 * v3;
  col = clamp(col, 0.0, 1.0);

  return extractAlpha(col);
}

vec4 mainImage(vec2 fragCoord) {
  vec2 center = iResolution.xy * 0.5;
  float size = min(iResolution.x, iResolution.y) * orbSize * introScale;
  vec2 uv = (fragCoord - center) / max(size, 1.0) * 2.0;

  if (abs(tiltX) > 0.001 || abs(tiltY) > 0.001) {
    vec3 p = vec3(uv, 0.0);
    float rx = tiltX * 3.14159265 / 180.0;
    float ry = tiltY * 3.14159265 / 180.0;
    p = vec3(p.x, p.y * cos(rx) - p.z * sin(rx), p.y * sin(rx) + p.z * cos(rx));
    p = vec3(p.x * cos(ry) + p.z * sin(ry), p.y, -p.x * sin(ry) + p.z * cos(ry));
    float persp = 2.6 / max(2.6 - p.z, 0.6);
    uv = p.xy * persp;
  }

  float angle = rot;
  float s = sin(angle);
  float c = cos(angle);
  uv = vec2(c * uv.x - s * uv.y, s * uv.x + c * uv.y);

  float hoverStrength = hover * hoverIntensity;
  uv.x += hoverStrength * 0.1 * sin(uv.y * 10.0 + iTime);
  uv.y += hoverStrength * 0.1 * sin(uv.x * 10.0 + iTime);

  return draw(uv);
}

void main() {
  vec2 fragCoord = vUv * iResolution.xy;
  vec4 col = mainImage(fragCoord);
  col *= introGlow;
  vec3 finalRgb = mix(backgroundColor, col.rgb, col.a) * opacity;
  fragColor = vec4(finalRgb, col.a * opacity);
}`;

function parseColor(input: string): [number, number, number] {
  const s = input.trim();
  if (s.startsWith('#')) {
    const h = s.slice(1);
    const full =
      h.length === 3
        ? h
            .split('')
            .map((c) => c + c)
            .join('')
        : h;
    if (full.length === 6) {
      return [
        parseInt(full.slice(0, 2), 16) / 255,
        parseInt(full.slice(2, 4), 16) / 255,
        parseInt(full.slice(4, 6), 16) / 255
      ];
    }
  }
  const m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (m) return [+m[1] / 255, +m[2] / 255, +m[3] / 255];
  return [0, 0, 0];
}

function compileShader(gl: WebGL2RenderingContext, type: number, source: string): WebGLShader | null {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

export default function Orb({
  colors = ['#9c43fe', '#4cc2e9', '#101499'],
  hue = 0,
  backgroundColor = '#000000',
  size = 1,
  glow = 1,
  bleed = 1,
  wobble = 1,
  highlight = 1,
  trail = 1,
  tiltX = 0,
  tiltY = 0,
  speed = 1,
  hoverIntensity = 1,
  rotateOnHover = true,
  forceHoverState = false,
  followCursor = true,
  clickPulse = true,
  intro = true,
  opacity = 1,
  paused = false,
  dpr,
  className = '',
  style
}: OrbProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const settingsRef = useRef<Settings>({
    colors,
    hue,
    backgroundColor,
    size,
    glow,
    bleed,
    wobble,
    highlight,
    trail,
    tiltX,
    tiltY,
    speed,
    hoverIntensity,
    rotateOnHover,
    forceHoverState,
    followCursor,
    clickPulse,
    intro,
    opacity,
    paused
  });

  settingsRef.current = {
    colors,
    hue,
    backgroundColor,
    size,
    glow,
    bleed,
    wobble,
    highlight,
    trail,
    tiltX,
    tiltY,
    speed,
    hoverIntensity,
    rotateOnHover,
    forceHoverState,
    followCursor,
    clickPulse,
    intro,
    opacity,
    paused
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.display = 'block';
    container.appendChild(canvas);

    const gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: false,
      antialias: true
    });
    if (!gl) {
      container.removeChild(canvas);
      return;
    }

    const vs = compileShader(gl, gl.VERTEX_SHADER, VERT);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) {
      if (vs) gl.deleteShader(vs);
      if (fs) gl.deleteShader(fs);
      container.removeChild(canvas);
      return;
    }

    const program = gl.createProgram();
    if (!program) {
      gl.deleteShader(vs);
      gl.deleteShader(fs);
      container.removeChild(canvas);
      return;
    }
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      gl.deleteProgram(program);
      container.removeChild(canvas);
      return;
    }

    const vao = gl.createVertexArray();
    gl.bindVertexArray(vao);
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const posLoc = gl.getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);

    const u = (name: string) => gl.getUniformLocation(program, name);
    const loc = {
      iTime: u('iTime'),
      iResolution: u('iResolution'),
      hue: u('hue'),
      hover: u('hover'),
      rot: u('rot'),
      hoverIntensity: u('hoverIntensity'),
      backgroundColor: u('backgroundColor'),
      color1: u('color1'),
      color2: u('color2'),
      color3: u('color3'),
      orbSize: u('orbSize'),
      glowAmount: u('glowAmount'),
      bleedAmount: u('bleedAmount'),
      wobbleAmount: u('wobbleAmount'),
      highlightAmount: u('highlightAmount'),
      trailAmount: u('trailAmount'),
      tiltX: u('tiltX'),
      tiltY: u('tiltY'),
      hoverAngle: u('hoverAngle'),
      followMix: u('followMix'),
      pulse: u('pulse'),
      introScale: u('introScale'),
      introGlow: u('introGlow'),
      opacity: u('opacity')
    };

    const maxDpr = dpr ?? Math.min(window.devicePixelRatio || 1, 1.5);

    function resize() {
      if (!container || !gl) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (!w || !h) return;
      canvas.width = Math.round(w * maxDpr);
      canvas.height = Math.round(h * maxDpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
    }

    const ro = new ResizeObserver(resize);
    ro.observe(container);
    resize();

    let targetHover = 0;
    let currentHover = 0;
    let targetAngle = 0;
    let currentAngle = 0;
    let followMix = 0;
    let currentRot = 0;
    let pulseValue = 0;
    let pulseVel = 0;
    let introScale = settingsRef.current.intro ? 0.65 : 1;
    let introVel = 0;
    let introGlow = settingsRef.current.intro ? 0 : 1;
    let introElapsed = 0;
    let animTime = 0;
    let lastTime = performance.now();

    function onMove(e: PointerEvent) {
      if (!container) return;
      const s = settingsRef.current;
      const rect = container.getBoundingClientRect();
      const size = Math.min(rect.width, rect.height) * s.size;
      const ux = ((e.clientX - rect.left - rect.width * 0.5) / Math.max(size, 1)) * 2;
      const uy = -((e.clientY - rect.top - rect.height * 0.5) / Math.max(size, 1)) * 2;
      const over = Math.hypot(ux, uy) < 0.85;
      targetHover = over ? 1 : 0;
      if (over && s.followCursor) {
        targetAngle = Math.atan2(uy, ux) - currentRot;
      }
    }

    function onLeave() {
      targetHover = 0;
    }

    function onDown() {
      if (!settingsRef.current.clickPulse) return;
      pulseValue = 1;
      pulseVel = 3.5;
    }

    container.addEventListener('pointermove', onMove);
    container.addEventListener('pointerleave', onLeave);
    container.addEventListener('pointerdown', onDown);

    let raf = 0;
    let visible = true;
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

    function render(now: number) {
      raf = 0;
      if (!visible) return;
      if (!reduced) {
        raf = requestAnimationFrame(render);
      }
      if (!gl) return;
      const dt = Math.min((now - lastTime) * 0.001, 0.05);
      lastTime = now;
      const s = settingsRef.current;

      if (!s.paused) {
        animTime += dt * s.speed;
      }

      if (s.intro && introElapsed < 2.2) {
        introElapsed += dt;
        const accel = (1 - introScale) * 90 - introVel * 11;
        introVel += accel * dt;
        introScale += introVel * dt;
        introGlow = Math.min(1, introGlow + dt * 1.4);
      } else {
        introScale = 1;
        introGlow = 1;
      }

      const effHover = s.forceHoverState ? 1 : targetHover;
      currentHover += (effHover - currentHover) * Math.min(1, dt * 8);

      const angleDiff = Math.atan2(Math.sin(targetAngle - currentAngle), Math.cos(targetAngle - currentAngle));
      currentAngle += angleDiff * Math.min(1, dt * 8);
      const wantFollow = s.followCursor && effHover > 0.5 ? 1 : 0;
      followMix += (wantFollow - followMix) * Math.min(1, dt * 6);

      if (s.rotateOnHover && effHover > 0.5 && !s.paused) {
        currentRot += dt * 0.3;
      }

      if (pulseValue > 0.001 || Math.abs(pulseVel) > 0.001) {
        const accel = -pulseValue * 55 - pulseVel * 8;
        pulseVel += accel * dt;
        pulseValue += pulseVel * dt;
        if (Math.abs(pulseValue) < 0.001 && Math.abs(pulseVel) < 0.001) {
          pulseValue = 0;
          pulseVel = 0;
        }
      }

      if (!canvas.width || !canvas.height) return;

      const c1 = parseColor(s.colors[0] ?? '#9c43fe');
      const c2 = parseColor(s.colors[1] ?? '#4cc2e9');
      const c3 = parseColor(s.colors[2] ?? '#101499');
      const bg = parseColor(s.backgroundColor);

      gl.clearColor(0, 0, 0, 0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      gl.bindVertexArray(vao);

      gl.uniform1f(loc.iTime, animTime);
      gl.uniform3f(loc.iResolution, canvas.width, canvas.height, canvas.width / canvas.height);
      gl.uniform1f(loc.hue, s.hue);
      gl.uniform1f(loc.hover, currentHover);
      gl.uniform1f(loc.rot, currentRot);
      gl.uniform1f(loc.hoverIntensity, s.hoverIntensity);
      gl.uniform3f(loc.backgroundColor, bg[0], bg[1], bg[2]);
      gl.uniform3f(loc.color1, c1[0], c1[1], c1[2]);
      gl.uniform3f(loc.color2, c2[0], c2[1], c2[2]);
      gl.uniform3f(loc.color3, c3[0], c3[1], c3[2]);
      gl.uniform1f(loc.orbSize, s.size);
      gl.uniform1f(loc.glowAmount, s.glow);
      gl.uniform1f(loc.bleedAmount, s.bleed);
      gl.uniform1f(loc.wobbleAmount, s.wobble);
      gl.uniform1f(loc.highlightAmount, s.highlight);
      gl.uniform1f(loc.trailAmount, s.trail);
      gl.uniform1f(loc.tiltX, s.tiltX);
      gl.uniform1f(loc.tiltY, s.tiltY);
      gl.uniform1f(loc.hoverAngle, currentAngle);
      gl.uniform1f(loc.followMix, followMix);
      gl.uniform1f(loc.pulse, pulseValue);
      gl.uniform1f(loc.introScale, introScale);
      gl.uniform1f(loc.introGlow, introGlow);
      gl.uniform1f(loc.opacity, s.opacity);

      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }

    const io = new IntersectionObserver((entries) => {
      visible = entries.some((e) => e.isIntersecting);
      if (visible && !raf) {
        lastTime = performance.now();
        raf = requestAnimationFrame(render);
      } else if (!visible && raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
    });
    io.observe(container);

    raf = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(raf);
      io.disconnect();
      ro.disconnect();
      container.removeEventListener('pointermove', onMove);
      container.removeEventListener('pointerleave', onLeave);
      container.removeEventListener('pointerdown', onDown);
      gl.deleteBuffer(buf);
      gl.deleteVertexArray(vao);
      gl.deleteProgram(program);
      if (canvas.parentNode === container) container.removeChild(canvas);
    };
  }, [dpr]);

  return (
    <div
      ref={containerRef}
      className={className}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        ...style
      }}
    />
  );
}

