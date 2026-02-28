import { useState } from "react";
import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api, isApiError, ExpansionResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "sonner";
import { MapPinPlus, ShieldCheck, ShieldAlert, ShieldX, Star } from "lucide-react";
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";
import { motion } from "framer-motion";

export default function ExpansionPage() {
  const branch = useAppStore((s) => s.branch);
  const [data, setData] = useState<ExpansionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.expansion({ branch });
      setData(res);
      toast.success("Expansion analysis complete");
    } catch (err) {
      toast.error(isApiError(err));
    } finally {
      setLoading(false);
    }
  };

  // Build radar data from the first scorecard's dimensions
  const radarData = data?.scorecards?.[0]
    ? Object.entries(data.scorecards[0].dimensions).map(([key, dim]) => ({
        metric: key.replace(/_/g, " "),
        value: dim.score,
      }))
    : [];

  const verdictIcon =
    data?.verdict === "GO" ? <ShieldCheck className="h-4 w-4" /> :
    data?.verdict === "CAUTION" ? <ShieldAlert className="h-4 w-4" /> :
    <ShieldX className="h-4 w-4" />;

  const verdictColor =
    data?.verdict === "GO" ? "bg-pistachio/20 text-pistachio border-pistachio/30" :
    data?.verdict === "CAUTION" ? "bg-caramel/20 text-caramel border-caramel/30" :
    "bg-destructive/20 text-destructive border-destructive/30";

  return (
    <PageShell>
      <div className="flex items-center gap-3 mb-6">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-copper/10 text-copper">
          <MapPinPlus className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-syne text-2xl font-bold">Expansion Feasibility</h1>
          <p className="text-sm text-muted-foreground">Evaluate new branch locations</p>
        </div>
      </div>

      <div className="mb-6">
        <Button onClick={submit} disabled={loading}>
          {loading ? "Analyzing…" : "Run Expansion Analysis"}
        </Button>
      </div>

      {loading && <Skeleton className="h-64 w-full rounded-lg" />}
      {!loading && !data && (
        <Card>
          <CardContent className="py-16 text-center text-muted-foreground text-sm">
            <MapPinPlus className="mx-auto h-10 w-10 mb-3 opacity-40" />
            Run the analysis to see expansion insights.
          </CardContent>
        </Card>
      )}

      {!loading && data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Verdict row */}
          <div className="flex flex-wrap gap-3 items-center">
            <Badge className={`text-sm px-4 py-1.5 gap-1.5 ${verdictColor}`}>
              {verdictIcon} {data.verdict}
            </Badge>
            <p className="text-sm text-muted-foreground">{data.verdict_detail}</p>
          </div>

          {/* Best archetype */}
          {data.best_archetype && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Star className="h-4 w-4 text-caramel" /> Best Archetype: {data.best_archetype.branch}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-lg border p-3 text-center">
                    <p className="text-xs text-muted-foreground">Composite Score</p>
                    <p className="font-syne text-2xl font-bold">{data.best_archetype.composite_score.toFixed(1)}</p>
                  </div>
                  <div className="rounded-lg border p-3 text-center">
                    <p className="text-xs text-muted-foreground">Beverage %</p>
                    <p className="font-syne text-2xl font-bold">{data.best_archetype.beverage_pct.toFixed(1)}%</p>
                  </div>
                  <div className="rounded-lg border p-3">
                    <p className="text-xs text-muted-foreground mb-1">Top Categories</p>
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(data.best_archetype.top_categories).slice(0, 4).map(([cat, val]) => (
                        <Badge key={cat} variant="secondary" className="text-[10px]">
                          {cat}: ${(val as number).toLocaleString()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">{data.best_archetype.recommendation}</p>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            {/* Radar chart */}
            {radarData.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-base">Branch Scorecard</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="hsl(var(--border))" />
                      <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10 }} />
                      <Radar dataKey="value" stroke="hsl(var(--copper))" fill="hsl(var(--copper))" fillOpacity={0.3} />
                      <Tooltip />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}

            {/* Candidate locations */}
            {data.candidate_locations && data.candidate_locations.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-base">Top Candidate Locations</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[340px] overflow-auto">
                    {data.candidate_locations.map((c, i) => (
                      <div key={i} className="flex items-start justify-between rounded-lg border p-3 gap-3">
                        <div className="min-w-0">
                          <p className="font-medium truncate">{c.area}</p>
                          <p className="text-xs text-muted-foreground">{c.governorate} · Pop {c.population.toLocaleString()}</p>
                          {c.pros.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {c.pros.map((p, j) => <Badge key={j} variant="secondary" className="text-[10px]">{p}</Badge>)}
                            </div>
                          )}
                        </div>
                        <Badge variant="outline" className="shrink-0">{c.score.toFixed(1)}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Risks */}
          {data.risks && data.risks.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base">⚠️ Risks</CardTitle></CardHeader>
              <CardContent>
                <ul className="space-y-1.5">
                  {data.risks.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-destructive" />
                      {r}
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
    </PageShell>
  );
}
