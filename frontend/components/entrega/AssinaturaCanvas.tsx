"use client";

import { forwardRef, useImperativeHandle, useRef, useState } from "react";

export type AssinaturaCanvasHandle = {
  obterAssinatura: () => Promise<File | null>;
  limpar: () => void;
  temAssinatura: () => boolean;
};

export const AssinaturaCanvas = forwardRef<AssinaturaCanvasHandle>(function AssinaturaCanvas(_props, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const desenhandoRef = useRef(false);
  const [vazio, setVazio] = useState(true);

  function posicaoRelativa(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function handlePointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    desenhandoRef.current = true;
    const ctx = canvas.getContext("2d")!;
    const { x, y } = posicaoRelativa(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
  }

  function handlePointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!desenhandoRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#463D3F";
    const { x, y } = posicaoRelativa(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    setVazio(false);
  }

  function handlePointerUp() {
    desenhandoRef.current = false;
  }

  function limpar() {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setVazio(true);
  }

  useImperativeHandle(ref, () => ({
    limpar,
    temAssinatura: () => !vazio,
    obterAssinatura: () =>
      new Promise((resolve) => {
        const canvas = canvasRef.current;
        if (!canvas) return resolve(null);
        canvas.toBlob((blob) => {
          if (!blob) return resolve(null);
          resolve(new File([blob], "assinatura.png", { type: "image/png" }));
        }, "image/png");
      }),
  }));

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-kami-charcoal">Assinatura do cliente</span>
      <canvas
        ref={canvasRef}
        width={340}
        height={160}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        className="w-full touch-none rounded-lg border border-black/15 bg-white"
      />
      <button type="button" onClick={limpar} className="self-start text-xs font-medium text-kami-red">
        Limpar assinatura
      </button>
    </div>
  );
});
