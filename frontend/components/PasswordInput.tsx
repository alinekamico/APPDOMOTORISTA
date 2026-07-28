"use client";

import { useState } from "react";

export function PasswordInput({
  value,
  onChange,
  placeholder,
  required,
  minLength,
  className,
  autoFocus,
}: {
  value: string;
  onChange: (valor: string) => void;
  placeholder?: string;
  required?: boolean;
  minLength?: number;
  className?: string;
  autoFocus?: boolean;
}) {
  const [mostrar, setMostrar] = useState(false);

  return (
    <div className="relative">
      <input
        type={mostrar ? "text" : "password"}
        required={required}
        minLength={minLength}
        autoFocus={autoFocus}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={
          className ??
          "w-full rounded-lg border border-black/10 px-3 py-2 pr-10 text-sm outline-none focus:border-kami-red"
        }
      />
      <button
        type="button"
        onClick={() => setMostrar((v) => !v)}
        aria-label={mostrar ? "Ocultar senha" : "Mostrar senha"}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-kami-charcoal-light hover:text-kami-charcoal"
      >
        {mostrar ? (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a21.86 21.86 0 0 1 5.06-6.06M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a21.86 21.86 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
            <line x1="1" y1="1" x2="23" y2="23" />
          </svg>
        ) : (
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
        )}
      </button>
    </div>
  );
}
