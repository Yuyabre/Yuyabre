import * as AvatarPrimitive from "@radix-ui/react-avatar";
import { ReactNode } from "react";

interface AvatarProps {
  src?: string;
  alt?: string;
  fallback: ReactNode;
  className?: string;
}

export function Avatar({ src, alt, fallback, className = "" }: AvatarProps) {
  return (
    <AvatarPrimitive.Root
      className={`inline-flex items-center justify-center align-middle overflow-hidden select-none w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white font-semibold text-sm ${className}`}
    >
      <AvatarPrimitive.Image
        src={src}
        alt={alt}
        className="w-full h-full object-cover rounded-full"
      />
      <AvatarPrimitive.Fallback className="flex items-center justify-center w-full h-full">
        {fallback}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  );
}

