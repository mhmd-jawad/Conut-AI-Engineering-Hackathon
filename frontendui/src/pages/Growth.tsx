import { useState, type ReactNode } from "react";
import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, isApiError, GrowthResponse, BranchBeverageProfile } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "sonner";
import { Rocket, Star, AlertTriangle, Coffee, CheckCircle, TrendingUp, TrendingDown, Minus, Users, Repeat } from "lucide-react";
import { motion } from "framer-motion";

export default function GrowthPage() {
  const branch = useAppStore((s) => s.branch);
  const [data, setData] = useState<GrowthResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.growth({ branch });
      setData(res);
      toast.success("Growth strategy ready");
    } catch (err) {
      toast.error(isApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const momentumIcon = (trend: string) =>
    trend === "growing" ? <TrendingUp className="h-3.5 w-3.5 text-pistachio" /> :
    trend === "declining" ? <TrendingDown className="h-3.5 w-3.5 text-destructive" /> :
    <Minus className="h-3.5 w-3.5" />;

  return (
    <PageShell>
      <div className="flex items-center gap-3 mb-6">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Rocket className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-syne text-2xl font-bold">Growth Strategy</h1>
          <p className="text-sm text-muted-foreground">Coffee & milkshake revenue growth</p>
        </div>
      </div>

      <div className="mb-6">
        <Button onClick={submit} disabled={loading}>
          {loading ? "Analyzing…" : "Generate Growth Strategy"}
        </Button>
      </div>

      {loading && <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32 w-full rounded-lg" />)}</div>}
      {!loading && !data && (
        <Card>
          <CardContent className="py-16 text-center text-muted-foreground text-sm">
            <Rocket className="mx-auto h-10 w-10 mb-3 opacity-40" />
            Run the analysis to see growth insights.
          </CardContent>
        </Card>
      )}

      {!loading && data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* If multiple branches, use tabs */}
          {data.branches.length > 1 ? (
            <Tabs defaultValue={data.branches[0].branch}>
              <TabsList className="flex-wrap h-auto gap-1 mb-4">
                {data.branches.map((b) => (
                  <TabsTrigger key={b.branch} value={b.branch} className="text-xs">
                    {b.branch}
                  </TabsTrigger>
                ))}
              </TabsList>
              {data.branches.map((bp) => (
                <TabsContent key={bp.branch} value={bp.branch}>
                  <BranchProfile bp={bp} momentumIcon={momentumIcon} />
                </TabsContent>
              ))}
            </Tabs>
          ) : data.branches.length === 1 ? (
            <BranchProfile bp={data.branches[0]} momentumIcon={momentumIcon} />
          ) : null}

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

/* ───── Sub-component for a single branch profile ───── */
function BranchProfile({ bp, momentumIcon }: { bp: BranchBeverageProfile; momentumIcon: (t: string) => ReactNode }) {
  return (
    <div className="space-y-5">
      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="py-5 text-center">
            <p className="text-xs text-muted-foreground">Beverage Penetration</p>
            <p className="font-syne text-3xl font-extrabold text-primary">{bp.beverage_penetration_pct.toFixed(1)}%</p>
            <Badge variant="outline" className="mt-1 text-[10px]">Rank #{bp.penetration_rank}</Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-5 text-center">
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1"><Coffee className="h-3 w-3" /> Coffee</p>
            <p className="font-syne text-2xl font-bold">{bp.coffee_qty}</p>
            <p className="text-[10px] text-muted-foreground">${bp.coffee_revenue.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-5 text-center">
            <p className="text-xs text-muted-foreground">Milkshake</p>
            <p className="font-syne text-2xl font-bold">{bp.milkshake_qty}</p>
            <p className="text-[10px] text-muted-foreground">${bp.milkshake_revenue.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-5 text-center">
            <p className="text-xs text-muted-foreground">Frappé</p>
            <p className="font-syne text-2xl font-bold">{bp.frappe_qty}</p>
            <p className="text-[10px] text-muted-foreground">${bp.frappe_revenue.toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Hero items */}
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Star className="h-4 w-4 text-caramel" /> Hero Coffee Items</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {bp.hero_coffee_items.map((h, i) => (
                <div key={i} className="flex items-center justify-between text-sm rounded-lg border px-3 py-2">
                  <span className="font-medium">#{h.rank} {h.item}</span>
                  <span className="text-xs text-muted-foreground">{h.qty} units · ${h.revenue.toLocaleString()}</span>
                </div>
              ))}
            </div>
            {bp.hero_milkshake_items.length > 0 && (
              <>
                <p className="text-xs font-medium text-muted-foreground mt-4 mb-2">Hero Milkshake Items</p>
                <div className="space-y-2">
                  {bp.hero_milkshake_items.map((h, i) => (
                    <div key={i} className="flex items-center justify-between text-sm rounded-lg border px-3 py-2">
                      <span className="font-medium">#{h.rank} {h.item}</span>
                      <span className="text-xs text-muted-foreground">{h.qty} units · ${h.revenue.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Underperformers */}
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-destructive" /> Underperformers</CardTitle></CardHeader>
          <CardContent>
            {bp.underperforming_items.length === 0 ? (
              <p className="text-sm text-muted-foreground">No underperforming items detected.</p>
            ) : (
              <div className="space-y-2">
                {bp.underperforming_items.map((u, i) => (
                  <div key={i} className="rounded-lg border px-3 py-2">
                    <p className="font-medium text-sm">{u.item}</p>
                    <p className="text-[11px] text-muted-foreground">
                      You: {u.your_qty} · Best: {u.best_branch} ({u.best_qty}) · Gap: {u.gap_pct.toFixed(0)}%
                    </p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Bundle recommendations */}
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><Coffee className="h-4 w-4 text-pistachio" /> Bundle Recommendations</CardTitle></CardHeader>
          <CardContent>
            {bp.bundle_recommendations.length === 0 ? (
              <p className="text-sm text-muted-foreground">No bundles to recommend.</p>
            ) : (
              <div className="space-y-2">
                {bp.bundle_recommendations.map((b, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border px-3 py-2">
                    <div>
                      <p className="font-medium text-sm">{b.dessert} + {b.beverage}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px]">{b.co_occurrence_count} baskets</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Metrics */}
        <div className="space-y-4">
          {/* Revenue momentum */}
          <Card>
            <CardHeader><CardTitle className="text-sm flex items-center gap-2">{momentumIcon(bp.revenue_momentum.trend)} Revenue Momentum</CardTitle></CardHeader>
            <CardContent className="text-sm">
              <p>{bp.revenue_momentum.months_available} months data · Latest: {bp.revenue_momentum.latest_month}</p>
              <p className="text-muted-foreground">MoM Growth: {bp.revenue_momentum.mom_growth_pct.toFixed(1)}% · Trend: {bp.revenue_momentum.trend}</p>
            </CardContent>
          </Card>

          {/* Customer metrics */}
          <Card>
            <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Users className="h-3.5 w-3.5" /> Customer Metrics</CardTitle></CardHeader>
            <CardContent className="text-sm space-y-1">
              <p>Total: {bp.customer_metrics.total_customers.toLocaleString()} customers · ${bp.customer_metrics.total_sales.toLocaleString()}</p>
              <p className="text-muted-foreground">Avg Ticket: ${bp.customer_metrics.avg_ticket.toFixed(2)}</p>
            </CardContent>
          </Card>

          {/* Delivery repeat rate */}
          <Card>
            <CardHeader><CardTitle className="text-sm flex items-center gap-2"><Repeat className="h-3.5 w-3.5" /> Delivery Repeat Rate</CardTitle></CardHeader>
            <CardContent className="text-sm space-y-1">
              <p>{bp.delivery_repeat_rate.repeat_rate_pct.toFixed(1)}% repeat rate · {bp.delivery_repeat_rate.avg_orders_per_customer.toFixed(1)} orders/customer</p>
              <p className="text-muted-foreground">{bp.delivery_repeat_rate.delivery_customers} delivery · {bp.delivery_repeat_rate.repeat_customers} repeating</p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Channel insight */}
      {bp.channel_insight && (
        <Card>
          <CardContent className="py-4">
            <p className="text-sm"><strong>Channel Insight:</strong> {bp.channel_insight}</p>
          </CardContent>
        </Card>
      )}

      {/* Action plan */}
      {bp.actions.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2"><CheckCircle className="h-4 w-4 text-deep-teal" /> Action Plan</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {bp.actions.map((a, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  {a}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
