import { motion } from "framer-motion";
import { ReactNode } from "react";

export default function PageShell({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.35 }}
      className={`flex-1 overflow-auto p-4 md:p-8 ${className}`}
    >
      {children}
    </motion.div>
  );
}
