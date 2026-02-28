import { LayoutDashboard, MessageSquare, Layers, TrendingUp, Users, MapPinPlus, Rocket, Home } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import ConutLogo from "@/components/ConutLogo";
import BranchSelector from "@/components/BranchSelector";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";

const navItems = [
  { title: "Home", url: "/", icon: Home },
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "Agent Chat", url: "/agent", icon: MessageSquare },
  { title: "Combos", url: "/combos", icon: Layers },
  { title: "Forecast", url: "/forecast", icon: TrendingUp },
  { title: "Staffing", url: "/staffing", icon: Users },
  { title: "Expansion", url: "/expansion", icon: MapPinPlus },
  { title: "Growth", url: "/growth", icon: Rocket },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <div className="flex items-center gap-3 px-4 py-5">
          <ConutLogo className="h-9 w-9 shrink-0" />
          {!collapsed && (
            <div className="leading-tight">
              <span className="font-syne text-base font-bold text-sidebar-foreground">Conut Ops</span>
              <span className="block text-[10px] font-medium tracking-widest text-sidebar-primary uppercase">AI Agent</span>
            </div>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground/50">Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={isActive(item.url)}>
                    <NavLink to={item.url} end className="hover:bg-sidebar-accent/50" activeClassName="bg-sidebar-accent text-sidebar-primary font-semibold">
                      <item.icon className="mr-2 h-4 w-4" />
                      {!collapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="p-3">
        {!collapsed && <BranchSelector className="w-full" />}
      </SidebarFooter>
    </Sidebar>
  );
}
