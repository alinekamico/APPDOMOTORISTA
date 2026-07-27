"use client";

import { useRef, useState } from "react";

export function CameraCapture({
  label,
  onCapture,
}: {
  label: string;
  onCapture: (arquivo: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const arquivo = e.target.files?.[0];
    if (!arquivo) return;
    setPreview(URL.createObjectURL(arquivo));
    onCapture(arquivo);
  }

  return (
    <div className="flex flex-col gap-2">
      <span className="text-sm font-medium text-kami-charcoal">{label}</span>
      {preview ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={preview} alt={label} className="h-40 w-full rounded-lg object-cover" />
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex h-40 w-full items-center justify-center rounded-lg border-2 border-dashed border-black/15 text-sm text-kami-charcoal-light"
        >
          Toque para tirar a foto
        </button>
      )}
      {preview && (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="self-start text-xs font-medium text-kami-red"
        >
          Tirar outra foto
        </button>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleChange}
      />
    </div>
  );
}
