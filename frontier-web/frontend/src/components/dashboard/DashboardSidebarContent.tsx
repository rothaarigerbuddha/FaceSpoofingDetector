"use client"

import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
// import { getIconComponent } from "@/lib/iconMapper"
import { cn } from "@/lib/utils"
import { NavSection } from "@/types/dashboard.types"
import { UserInfo } from "@/types/user.types"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import UserDropdown from "./UserDropdown"
import Logo from "../shared/Logo"


interface DashboardSidebarContentProps {
    userInfo : UserInfo,
    navItems : NavSection[],
    dashboardHome : string,

}



const DashboardSidebarContent = ({dashboardHome, navItems, userInfo} : DashboardSidebarContentProps) => {
    const pathname = usePathname()
  return (
    <div className="hidden md:flex h-full w-60 flex-col border-r border-border/40 bg-background overflow-hidden">
      {/* Logo / Brand */}
      <div className="shrink-0 border-b px-3 py-4 flex items-center gap-2">
        <Logo />
      </div>

      {/* Navigation Area */}
      <ScrollArea className="flex-1 min-h-0 px-3 py-4">
        <nav className="space-y-6">
          {navItems.map((section, sectionId) => (
            <div key={sectionId}>
              {section.title && (
                <h4 className="mb-2 px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {section.title}
                </h4>
              )}

              <div className="space-y-1">
                {section.items.map((item, id) => {
                  const isActive = pathname === item.href;
                  // Icon Mapper Function
                //   const Icon = getIconComponent(item.icon);

                  return (
                    <Link
                      href={item.href}
                      key={id}
                      className={cn(
                        "group relative flex items-center gap-3 px-3 py-2.5 text-sm font-semibold transition-all duration-200",
                        isActive
                          ? "bg-primary/10 text-primary shadow-sm"
                          : "text-muted-foreground hover:bg-accent/50 hover:text-foreground",
                      )}
                    >
                      {isActive && (
                        <div className="absolute left-0 h-5 w-1 rounded-r-full bg-primary" />
                      )}
                      {/* <Icon className={cn("w-4.5 h-4.5 transition-colors", isActive ? "text-primary" : "group-hover:text-foreground")} /> */}
                      <span>{item.title}</span>
                    </Link>
                  );
                })}
              </div>

              {sectionId < navItems.length - 1 && (
                <Separator className="my-4" />
              )}
            </div>
          ))}
        </nav>
      </ScrollArea>

      {/* User Dropdown At Bottom */}
      <div className="shrink-0 border-t px-3 py-4">
        <UserDropdown userInfo={userInfo} />
      </div>
    </div>
  );
}

export default DashboardSidebarContent