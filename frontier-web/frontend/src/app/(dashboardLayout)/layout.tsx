import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import React from "react";
export const dynamic = "force-dynamic";

const RootDashboardLayout = async ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex h-screen overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <DashboardSidebar />

      {/* Right side: navbar + scrollable content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-muted/10 p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default RootDashboardLayout;