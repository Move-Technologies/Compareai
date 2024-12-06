import { cn } from "@/lib/utils";
import React from "react";

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
}

function Container({ children, className }: ContainerProps) {
  return (
    <div className={cn("max-w-5xl mx-auto px-5", className)}>{children}</div>
  );
}

export default Container;
