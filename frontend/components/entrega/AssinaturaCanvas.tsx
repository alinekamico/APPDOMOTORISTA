"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";

export type AssinaturaCanvasHandle = {
  obterAssinatura: () => Promise<File | null>;
  limpar: () => void;
  temAssinatura: () => boolean;
};

const ALTURA_CSS_PX = 160;

export const AssinaturaCanvas = forwardRef<AssinaturaCanvasHandle>(function AssinaturaCanvas(_props, ref) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const desenhandoRef = useRef(false);
  const [vazio, setVazio] = useState(true);

  // O canvas precisa ter a resolução interna (width/height) igual ao tamanho exibido
  // (que varia por tela, já que a largura é responsiva) — senão o toque registra na
  // posição errada em qualquer celular com largura diferente de 340px.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    function ajustarResolucao() {
      const dpr = window.devicePixelRatio || 1;
      const larguraCss = canvas!.clientWidth;
      canvas!.width = larguraCss * dpr;
      canvas!.height = ALTURA_CSS_PX * dpr;
      const ctx = canvas!.getContext("2d");
      ctx?.scale(dpr, dpr);
    }

    ajustarResolucao();
    window.addEventListener("resize", ajustarResolucao);
    return () => window.removeEventListener("resize", ajustarResolucao);
  }, []);

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
