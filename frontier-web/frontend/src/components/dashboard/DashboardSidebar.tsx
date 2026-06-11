import { getNavItemsByPermissions } from "@/lib/navItems"

import { NavSection } from "@/types/dashboard.types"
import DashboardSidebarContent from "./DashboardSidebarContent"
import { getUserInfo, getUserPermissions } from "@/services/auth.service"
import { UserInfo } from "@/types/user.types"
import { redirect } from "next/navigation"

const DashboardSidebar = async () => {
  const userInfo = await getUserInfo();

  // Middleware should catch this, but guard here too
  if (!userInfo) redirect("/login");

  const userPermissions = await getUserPermissions(userInfo.username);
  const navItems: NavSection[] = getNavItemsByPermissions(userPermissions);

//   const dashboardHome = getDefaultDashboardRoute(userInfo.roles)
  const dashboardHome = "/dashboard"
  return (
    <DashboardSidebarContent userInfo={userInfo as UserInfo} navItems={navItems} dashboardHome={dashboardHome}/>
  )
}

export default DashboardSidebar