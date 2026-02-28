import { useState } from "react";
import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api, isApiError, ForecastResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "sonner";
import { TrendingUp, TrendingDown, Minus, BarChart3 } from "lucide-react";
import { XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ComposedChart, Line, Bar } from "recharts";
import { motion } from "framer-motion";

export default function ForecastPage() {
  const branch = useAppStore((s) => s.branch);
  const [horizon, setHorizon] = useState(3);
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.forecast({ branch, horizon_months: horizon });
      setData(res);
      toast.success("Forecast generated");
    } catch (err) {
      toast.error(isApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const trendIcon =
    data?.trend === "up" ? <TrendingUp className="h-4 w-4" /> :
    data?.trend === "down" ? <TrendingDown className="h-4 w-4" /> :
    <Minus className="h-4 w-4" />;

  // Build unified chart data from history + forecasts
  const chartData = [
    ...(data?.history ?? []).map((h) => ({
      month: h.month,
      actual: h.total,
      ensemble: null as number | null,
      naive: null as number | null,
      wma: null as number | null,
    })),
    ...(data?.forecasts ?? []).map((f) => ({
      month: f.month,
      actual: null as number | null,
      ensemble: f.ensemble,
      naive: f.naive,
      wma: f.wma,
    })),
  ];

  return (
    <PageShell>
      <div className="flex items-center gap-3 mb-6">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-deep-teal/10 text-deep-teal">
          <TrendingUp className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-syne text-2xl font-bold">Demand Forecast</h1>
          <p className="text-sm text-muted-foreground">Predict future demand by branch</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        {/* ── Params card ─────────────────────────────────────── */}
        <Card className="h-fit">
          <CardHeader><CardTitle className="text-base">Parameters</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Horizon (months)</Label>
              <Input type="number" value={horizon} onChange={(e) => setHorizon(+e.target.value)} min={1} max={6} />
            </div>
            <Button onClick={submit} disabled={loading} className="w-full">
              {loading ? "Forecasting…" : "Generate Forecast"}
            </Button>
          </CardContent>
        </Card>

        {/* ── Results ─────────────────────────────────────────── */}
        <div className="space-y-6">
          {loading && <Skeleton className="h-64 w-full rounded-lg" />}
          {!loading && !data && (
            <Card>
              <CardContent className="py-16 text-center text-muted-foreground text-sm">
                <BarChart3 className="mx-auto h-10 w-10 mb-3 opacity-40" />
                Run the forecast to see results.
              </CardContent>
            </Card>
          )}
          {!loading && data && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              {/* KPI badges */}
              <div className="flex flex-wrap gap-3">
                <Badge variant="secondary" className="gap-1.5 px-3 py-1">
                  {trendIcon} Trend: {data.trend}
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  Confidence: {data.confidence}
                </Badge>
                {data.demand_index != null && (
                  <Badge variant="outline" className="px-3 py-1">
                    Demand Index: {data.demand_index.toFixed(1)}
                  </Badge>
                )}
                {data.avg_mom_growth_pct != null && (
                  <Badge variant="outline" className="px-3 py-1">
                    Avg MoM Growth: {data.avg_mom_growth_pct.toFixed(1)}%
                  </Badge>
                )}
              </div>

              {/* Chart */}
              {chartData.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-base">Demand Chart</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={340}>
                      <ComposedChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        {/* Historical bars */}
                        <Bar dataKey="actual" fill="hsl(var(--deep-teal))" name="Actual" radius={[4, 4, 0, 0]} />
                        {/* Forecast lines */}
                        <Line dataKey="ensemble" stroke="hsl(var(--caramel))" strokeWidth={2.5} dot={{ r: 4 }} name="Ensemble" connectNulls={false} />
                        <Line dataKey="naive" stroke="hsl(var(--pistachio))" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Naïve" connectNulls={false} />
                        <Line dataKey="wma" stroke="hsl(var(--copper))" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="WMA" connectNulls={false} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}

              {/* Anomaly notes */}
              {data.anomaly_notes && data.anomaly_notes.length > 0 && (
                <Card>
                  <CardHeader><CardTitle className="text-base">⚠️ Anomaly Notes</CardTitle></CardHeader>
                  <CardContent>
                    <ul className="space-y-1 text-sm">
                      {data.anomaly_notes.map((n, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
                          {n}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
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
