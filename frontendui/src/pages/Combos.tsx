import { useState } from "react";
import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { api, isApiError, ComboPair, ComboResponse } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Layers } from "lucide-react";

export default function CombosPage() {
  const branch = useAppStore((s) => s.branch);
  const [topK, setTopK] = useState(10);
  const [includeModifiers, setIncludeModifiers] = useState(false);
  const [minSupport, setMinSupport] = useState(0.02);
  const [minConfidence, setMinConfidence] = useState(0.15);
  const [minLift, setMinLift] = useState(1.0);
  const [data, setData] = useState<ComboResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.combo({ branch, top_k: topK, include_modifiers: includeModifiers, min_support: minSupport, min_confidence: minConfidence, min_lift: minLift });
      setData(res);
      toast.success(`Found ${res.recommendations.length} combos`);
    } catch (err) {
      toast.error(isApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const results = data?.recommendations ?? [];

  return (
    <PageShell>
      <div className="flex items-center gap-3 mb-6">
        <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-caramel/10 text-caramel">
          <Layers className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-syne text-2xl font-bold">Combo Optimization</h1>
          <p className="text-sm text-muted-foreground">Discover the most profitable product pairings</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <Card className="h-fit">
          <CardHeader><CardTitle className="text-base">Parameters</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Top K</Label>
              <Input type="number" value={topK} onChange={(e) => setTopK(+e.target.value)} min={1} max={20} />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={includeModifiers} onCheckedChange={setIncludeModifiers} />
              <Label>Include Modifiers</Label>
            </div>
            <div>
              <Label>Min Support</Label>
              <Input type="number" step={0.01} value={minSupport} onChange={(e) => setMinSupport(+e.target.value)} />
            </div>
            <div>
              <Label>Min Confidence</Label>
              <Input type="number" step={0.05} value={minConfidence} onChange={(e) => setMinConfidence(+e.target.value)} />
            </div>
            <div>
              <Label>Min Lift</Label>
              <Input type="number" step={0.1} value={minLift} onChange={(e) => setMinLift(+e.target.value)} />
            </div>
            <Button onClick={submit} disabled={loading} className="w-full">
              {loading ? "Analyzing…" : "Find Combos"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Results</CardTitle>
              {data && (
                <Badge variant="secondary" className="text-xs">
                  {data.total_baskets.toLocaleString()} baskets analysed
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading && <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>}
            {!loading && !data && <p className="text-muted-foreground text-sm py-8 text-center">Run the analysis to see combos.</p>}
            {!loading && data && results.length === 0 && <p className="text-muted-foreground text-sm py-8 text-center">No combos found for these parameters.</p>}
            {!loading && results.length > 0 && (
              <div className="overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item A</TableHead>
                      <TableHead>Item B</TableHead>
                      <TableHead className="text-right">Support</TableHead>
                      <TableHead className="text-right">Conf A→B</TableHead>
                      <TableHead className="text-right">Lift</TableHead>
                      <TableHead className="text-right">Baskets</TableHead>
                      <TableHead className="text-right">Combo $</TableHead>
                      <TableHead className="text-right">Savings</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {results.map((r, i) => (
                      <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.03 }} className="border-b">
                        <TableCell className="font-medium">{r.item_a}</TableCell>
                        <TableCell className="font-medium">{r.item_b}</TableCell>
                        <TableCell className="text-right">{r.support.toFixed(3)}</TableCell>
                        <TableCell className="text-right">{(r.confidence_a_to_b * 100).toFixed(1)}%</TableCell>
                        <TableCell className="text-right">{r.lift.toFixed(2)}</TableCell>
                        <TableCell className="text-right">{r.basket_count}</TableCell>
                        <TableCell className="text-right">${r.suggested_combo_price.toFixed(2)}</TableCell>
                        <TableCell className="text-right text-pistachio">${r.savings.toFixed(2)}</TableCell>
                      </motion.tr>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            {/* Explanation */}
            {data?.explanation && (
              <p className="mt-4 text-xs text-muted-foreground whitespace-pre-line border-t pt-3">{data.explanation}</p>
            )}
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
