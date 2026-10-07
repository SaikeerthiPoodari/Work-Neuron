import { useEffect, useState } from "react";

export default function NeuralFlowBackground({ intensity = "ambient", className = "" }) {
  const [pointer, setPointer] = useState({ x: 50, y: 35 });
  const [scroll, setScroll] = useState(0);

  useEffect(() => {
    if (intensity === "minimal") return undefined;
    const move = (event) => {
      setPointer({ x: (event.clientX / window.innerWidth) * 100, y: (event.clientY / window.innerHeight) * 100 });
    };
    const scrollPage = () => setScroll(window.scrollY * 0.08);
    window.addEventListener("pointermove", move, { passive: true });
    window.addEventListener("scroll", scrollPage, { passive: true });
    return () => { window.removeEventListener("pointermove", move); window.removeEventListener("scroll", scrollPage); };
  }, [intensity]);

  return <div className={`neural-flow neural-flow-${intensity} ${className}`} aria-hidden="true" style={{ "--pointer-x": `${pointer.x}%`, "--pointer-y": `${pointer.y}%`, "--scroll-shift": `${scroll}px` }}>
    <div className="neural-aurora" />
    <svg className="neural-ribbons" viewBox="0 0 1440 760" preserveAspectRatio="none">
      <defs>
        <linearGradient id="neural-blue-flow" x1="0" x2="1">
          <stop offset="0" stopColor="#155EEF" stopOpacity="0" />
          <stop offset=".45" stopColor="#38BDF8" stopOpacity=".72" />
          <stop offset="1" stopColor="#22D3EE" stopOpacity="0" />
        </linearGradient>
        <filter id="neural-glow"><feGaussianBlur stdDeviation="8" /></filter>
      </defs>
      <path className="neural-ribbon neural-ribbon-glow" d="M-80 530 C 190 260, 330 720, 620 420 S 1050 120, 1520 300" filter="url(#neural-glow)" />
      <path className="neural-ribbon neural-ribbon-one" d="M-80 530 C 190 260, 330 720, 620 420 S 1050 120, 1520 300" />
      <path className="neural-ribbon neural-ribbon-two" d="M-100 160 C 260 520, 420 40, 730 260 S 1160 630, 1510 490" />
      <path className="neural-ribbon neural-ribbon-three" d="M-100 680 C 260 610, 370 180, 790 500 S 1180 710, 1520 180" />
      <path className="neural-trail neural-trail-one" d="M-100 160 C 260 520, 420 40, 730 260 S 1160 630, 1510 490" />
      <path className="neural-trail neural-trail-two" d="M-100 680 C 260 610, 370 180, 790 500 S 1180 710, 1520 180" />
      <g className="neural-nodes" fill="#BAE6FD">
        <circle cx="245" cy="390" r="3" /><circle cx="620" cy="420" r="4" /><circle cx="1010" cy="235" r="3" /><circle cx="1180" cy="540" r="4" />
      </g>
    </svg>
    <span className="neural-particle particle-a" /><span className="neural-particle particle-b" /><span className="neural-particle particle-c" /><span className="neural-particle particle-d" /><span className="neural-particle particle-e" />
    <span className="neural-node node-a" /><span className="neural-node node-b" /><span className="neural-node node-c" />
  </div>;
}
