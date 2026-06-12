"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuGroup,
} from "@/components/ui/dropdown-menu";
import { UserInfo } from "@/types/user.types";
import { ChevronUp, LogOut, User } from "lucide-react";
import Link from "next/link";
import { logoutUser } from "@/services/auth.service";
import { useRouter } from "next/navigation";

interface UserDropdownProps {
  userInfo: UserInfo;
}

const UserDropdown = ({ userInfo }: UserDropdownProps) => {
  const router = useRouter();

  const handleLogout = async () => {
    await logoutUser();
    router.push("/login");
  };

  const initial = userInfo.username.charAt(0).toUpperCase();
  const rolesLabel = userInfo.roles.join(", ") || "No role";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild className="w-full">
        <div className="flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none">
          {/* Avatar Initial */}
          <div className="h-8 w-8 shrink-0 rounded-full bg-primary/10 flex items-center justify-center">
            <span className="text-sm font-semibold text-primary">
              {initial}
            </span>
          </div>

          {/* Username & Role */}
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium truncate">{userInfo.username}</p>
            <p className="text-xs text-muted-foreground truncate">{rolesLabel}</p>
          </div>

          {/* Chevron indicator */}
          <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
        </div>
      </DropdownMenuTrigger>

      <DropdownMenuContent side="top" align="start" className="w-56 mb-1">
        <DropdownMenuGroup>
          <DropdownMenuLabel>
            <div className="flex flex-col space-y-1">
              <p className="text-sm font-medium">{userInfo.username}</p>
              <p className="text-xs text-primary">{rolesLabel}</p>
            </div>
          </DropdownMenuLabel>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-red-600"
        >
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default UserDropdown;
