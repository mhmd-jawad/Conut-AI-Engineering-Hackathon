import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Activity } from "lucide-react";

export default function StatusBadge() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30000,
    retry: 1,
  });

  const online = !isLoading && !isError && data?.status;

  return (
    <div className="flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium">
      <span className={`h-2 w-2 rounded-full ${online ? "bg-pistachio" : "bg-destructive"}`} />
      <Activity className="h-3 w-3" />
      {isLoading ? "Checking…" : online ? "API Online" : "API Offline"}
    </div>
  );
}
