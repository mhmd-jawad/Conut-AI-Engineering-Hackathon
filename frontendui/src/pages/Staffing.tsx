import { useState } from "react";
import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api, isApiError, StaffingResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "sonner";
import { Users, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { motion } from "framer-motion";

const SHIFTS = ["morning", "midday", "evening"] as const;

export default function StaffingPage() {
  const branch = useAppStore((s) => s.branch);
  const [shift, setShift] = useState<string>("morning");
  const [data, setData] = useState<StaffingResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.staffing({ branch, shift });
      setData(res);
      toast.success("Staffing estimate ready");
    } catch (err) {
      toast.error(isApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const demandTrendIcon =
    data?.demand_trend === "growing" ? <TrendingUp className="h-3.5 w-3.5" /> :
    data?.demand_trend === "declining" ? <TrendingDown className="h-3.5 w-3.5" /> :
    <Minus className="h-3.5 w-3.5" />;

  return (
    <PageShell>
      <div className="flex items-center gap-3 mb-6">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-pistachio/10 text-pistachio">
          <Users className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-syne text-2xl font-bold">Shift Staffing</h1>
          <p className="text-sm text-muted-foreground">Optimize crew size for every shift</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <Card className="h-fit">
          <CardHeader><CardTitle className="text-base">Parameters</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Shift</Label>
              <Select value={shift} onValueChange={setShift}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {SHIFTS.map((s) => (
                    <SelectItem key={s} value={s} className="capitalize">{s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={submit} disabled={loading} className="w-full">
              {loading ? "Estimating…" : "Estimate Staff"}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {loading && <Skeleton className="h-48 w-full rounded-lg" />}
          {!loading && !data && (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground text-sm">
                <Users className="mx-auto h-10 w-10 mb-3 opacity-40" />
                Run the estimation to see results.
              </CardContent>
            </Card>
          )}
          {!loading && data && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
              {/* Main recommendation */}
              <Card>
                <CardContent className="py-8 text-center">
                  <p className="text-muted-foreground text-sm mb-1">Recommended Staff</p>
                  <p className="font-syne text-5xl font-extrabold text-primary">{data.recommended_staff}</p>
                  <div className="flex flex-wrap justify-center gap-2 mt-3">
                    <Badge variant="outline" className="gap-1">
                      Confidence: {data.confidence}
                    </Badge>
                    <Badge variant="secondary" className="gap-1">
                      Demand Factor: {data.demand_factor.toFixed(2)}
                    </Badge>
                    <Badge variant="secondary" className="gap-1">
                      {demandTrendIcon} {data.demand_trend}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Scenarios */}
              {data.scenarios && (
                <div className="grid gap-4 sm:grid-cols-3">
                  {(["low", "base", "high"] as const).map((s) => (
                    <Card key={s} className={s === "base" ? "border-primary ring-1 ring-primary/20" : ""}>
                      <CardContent className="py-6 text-center">
                        <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">{s} Scenario</p>
                        <p className="font-syne text-3xl font-bold">{data.scenarios![s]}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Explanation */}
              <Card>
                <CardHeader><CardTitle className="text-base">Explanation</CardTitle></CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">{data.explanation}</p>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </div>
      </div>
    </PageShell>
  );
}
