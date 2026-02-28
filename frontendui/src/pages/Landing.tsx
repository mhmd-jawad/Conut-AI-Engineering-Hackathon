import PageShell from "@/components/PageShell";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import {
  Layers, TrendingUp, Users, MapPinPlus, Rocket,
  ArrowRight, MessageSquare,
} from "lucide-react";
import ConutLogo from "@/components/ConutLogo";

const objectives = [
  {
    icon: Layers, title: "Combo Optimization",
    desc: "AI-driven basket analysis discovers the highest-value product pairings for your menu.",
    link: "/combos",
    gradient: "from-[hsl(25,55%,49%)] to-[hsl(17,52%,48%)]",
    iconBg: "bg-[hsl(25,55%,49%)]/15",
    iconColor: "text-[hsl(25,55%,49%)]",
  },
  {
    icon: TrendingUp, title: "Demand Forecasting",
    desc: "Ensemble forecasting with 3 models predicts branch demand up to 6 months ahead.",
    link: "/forecast",
    gradient: "from-[hsl(178,50%,23%)] to-[hsl(178,50%,33%)]",
    iconBg: "bg-[hsl(178,50%,23%)]/15",
    iconColor: "text-[hsl(178,50%,23%)]",
  },
  {
    icon: Users, title: "Shift Staffing",
    desc: "Data-driven crew recommendations per shift, tuned by demand trends and attendance history.",
    link: "/staffing",
    gradient: "from-[hsl(100,20%,45%)] to-[hsl(100,30%,55%)]",
    iconBg: "bg-[hsl(100,20%,58%)]/15",
    iconColor: "text-[hsl(100,20%,45%)]",
  },
  {
    icon: MapPinPlus, title: "Expansion Feasibility",
    desc: "6-dimension branch scorecards plus ranked Lebanese candidate locations for new stores.",
    link: "/expansion",
    gradient: "from-[hsl(17,52%,48%)] to-[hsl(25,55%,55%)]",
    iconBg: "bg-[hsl(17,52%,48%)]/15",
    iconColor: "text-[hsl(17,52%,48%)]",
  },
  {
    icon: Rocket, title: "Growth Strategy",
    desc: "Deep beverage-penetration analysis with hero items, underperformers, and bundle ideas.",
    link: "/growth",
    gradient: "from-[hsl(25,55%,49%)] to-[hsl(178,50%,28%)]",
    iconBg: "bg-[hsl(25,55%,49%)]/15",
    iconColor: "text-[hsl(25,55%,49%)]",
  },
];

const container = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0, transition: { duration: 0.45 } } };

export default function LandingPage() {
  return (
    <PageShell className="p-0">
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-espresso px-6 min-h-[calc(100vh-3.5rem)] flex flex-col items-center justify-center">
        {/* Layered gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-espresso via-[hsl(20,18%,14%)] to-[hsl(178,40%,12%)]" />
        {/* Subtle radial glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] rounded-full bg-[hsl(25,55%,49%)]/[0.06] blur-[120px]" />
        {/* Texture overlay */}
        <div className="absolute inset-0 opacity-[0.04] bg-texture" />

        <div className="relative mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ scale: 0.6, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
          >
            <ConutLogo className="mx-auto h-24 w-24 mb-8 drop-shadow-lg" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            className="font-syne text-5xl md:text-7xl font-extrabold text-cream tracking-tight mb-5"
          >
            Conut Ops{" "}
            <span className="bg-gradient-to-r from-[hsl(25,55%,55%)] to-[hsl(17,52%,58%)] bg-clip-text text-transparent">
              AI
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="text-cream/60 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Your Chief of Operations Agent — powering smarter combos, demand
            forecasts, staffing, and growth strategy for artisan sweet &amp;
            beverage brands.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45, duration: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3"
          >
            <Button
              asChild
              size="lg"
              className="bg-[hsl(25,55%,49%)] hover:bg-[hsl(25,55%,44%)] text-cream font-syne text-base px-8 h-12 shadow-lg shadow-[hsl(25,55%,49%)]/20 transition-all duration-300"
            >
              <Link to="/dashboard">
                Enter Dashboard <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              className="bg-cream/10 border border-cream/25 text-cream hover:bg-cream/20 font-syne text-base px-8 h-12 transition-all duration-300"
            >
              <Link to="/agent">
                <MessageSquare className="mr-2 h-4 w-4" />
                Ask the Agent
              </Link>
            </Button>
          </motion.div>
        </div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-cream/30"
        >
          <span className="text-[10px] uppercase tracking-widest">Scroll</span>
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            <ArrowRight className="h-4 w-4 rotate-90" />
          </motion.div>
        </motion.div>

        {/* Bottom fade into content */}
        <div className="absolute -bottom-px left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent" />
      </section>

      {/* ── Core Objectives ───────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <p className="text-xs font-semibold uppercase tracking-widest text-[hsl(25,55%,49%)] mb-2">
            What It Does
          </p>
          <h2 className="font-syne text-3xl md:text-4xl font-bold">
            5 Core Objectives
          </h2>
          <p className="text-muted-foreground mt-3 max-w-xl mx-auto text-sm md:text-base">
            Each module is a standalone analytics engine powered by your real
            branch data — no hallucinated numbers.
          </p>
        </motion.div>

        <motion.div
          variants={container}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, amount: 0.15 }}
          className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3"
        >
          {objectives.map((o) => (
            <motion.div key={o.title} variants={item}>
              <Link to={o.link} className="block h-full">
                <div className="group relative h-full rounded-xl border border-border/50 bg-card p-6 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-border cursor-pointer overflow-hidden">
                  {/* Hover gradient bar at top */}
                  <div
                    className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${o.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
                  />
                  <div className={`inline-flex items-center justify-center rounded-lg ${o.iconBg} p-2.5 mb-4`}>
                    <o.icon className={`h-5 w-5 ${o.iconColor}`} />
                  </div>
                  <h3 className="font-syne font-bold text-base mb-2 group-hover:text-[hsl(25,55%,49%)] transition-colors">
                    {o.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {o.desc}
                  </p>
                  <ArrowRight className="mt-4 h-4 w-4 text-muted-foreground/40 group-hover:text-[hsl(25,55%,49%)] group-hover:translate-x-1 transition-all duration-300" />
                </div>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="border-t border-border/50 px-6 py-10">
        <div className="mx-auto max-w-5xl flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <ConutLogo className="h-5 w-5" />
            <span className="font-syne font-semibold text-foreground/70">
              Conut Ops AI
            </span>
          </div>
          <p>AUB AI Engineering Hackathon · Prof. Ammar Mohanna · Built with artisan care ☕</p>
        </div>
      </footer>
    </PageShell>
  );
}
