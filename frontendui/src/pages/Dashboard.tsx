import PageShell from "@/components/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Layers, TrendingUp, Users, MapPinPlus, Rocket, Activity } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

const cards = [
  { icon: Layers, title: "Combo Optimization", desc: "Discover top-selling product combos", link: "/combos", color: "bg-caramel/10 text-caramel" },
  { icon: TrendingUp, title: "Demand Forecast", desc: "Branch demand projections", link: "/forecast", color: "bg-deep-teal/10 text-deep-teal" },
  { icon: Users, title: "Shift Staffing", desc: "Right-size your crew", link: "/staffing", color: "bg-pistachio/10 text-pistachio" },
  { icon: MapPinPlus, title: "Expansion", desc: "New location feasibility", link: "/expansion", color: "bg-copper/10 text-copper" },
  { icon: Rocket, title: "Growth Strategy", desc: "Coffee & milkshake growth", link: "/growth", color: "bg-primary/10 text-primary" },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };

export default function DashboardPage() {
  const { data: health, isLoading, isError } = useQuery({ queryKey: ["health"], queryFn: api.health, retry: 1 });

  return (
    <PageShell>
      {/* Health Hero */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-syne text-3xl font-extrabold">Operations Dashboard</h1>
          <p className="text-muted-foreground mt-1">Real-time intelligence for your sweet empire</p>
        </div>
        <div className="flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium">
          <Activity className="h-4 w-4" />
          {isLoading ? <Skeleton className="h-4 w-20" /> : isError ? <span className="text-destructive">Backend Offline</span> : <span className="text-pistachio">Backend Online</span>}
        </div>
      </div>

      {/* Objective Cards */}
      <motion.div variants={container} initial="hidden" animate="show" className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <motion.div key={c.title} variants={item}>
            <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="pb-2">
                <div className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${c.color} mb-2`}>
                  <c.icon className="h-5 w-5" />
                </div>
                <CardTitle className="font-syne text-lg">{c.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">{c.desc}</p>
                <Button variant="outline" size="sm" asChild>
                  <Link to={c.link}>Explore →</Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>
    </PageShell>
  );
}
