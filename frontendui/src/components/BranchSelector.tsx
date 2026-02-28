import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAppStore, BRANCHES } from "@/lib/store";
import { MapPin } from "lucide-react";

export default function BranchSelector({ className = "" }: { className?: string }) {
  const { branch, setBranch } = useAppStore();
  return (
    <Select value={branch} onValueChange={(v) => setBranch(v as any)}>
      <SelectTrigger className={`w-[200px] ${className}`}>
        <MapPin className="mr-2 h-4 w-4 text-primary" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {BRANCHES.map((b) => (
          <SelectItem key={b} value={b}>{b === "all" ? "All Branches" : b}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
