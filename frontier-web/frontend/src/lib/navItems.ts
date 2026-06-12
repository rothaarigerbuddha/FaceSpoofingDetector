import { NavSection } from "@/types/dashboard.types";
import { hasRequiredPermission } from "./authUtils";

const ALL_NAV_SECTIONS: NavSection[] = [
      {
          items: [
              {
                  title: "Articles",
                  href: `/dashboard/list-articles`,
                  icon: "FileText",
              },
              {
                  title: "Create Article",
                  href: "/dashboard/create-article",
                  icon: "Plus",
                  permissions: ["posts.write"]
              },
              {
                  title: "Users Management",
                  href: "/dashboard/users",
                  icon: "Users",
                  permissions: ["users.manage"]
              },
              {
                  title: "Roles & Permissions",
                  href: "/dashboard/roles-permissions",
                  icon: "Shield",
                  permissions: ["users.manage"]
              }
          ]
      }
];

export const getNavItemsByPermissions = (userPermissions: string[]): NavSection[] => {
    return ALL_NAV_SECTIONS.map(section => ({
        ...section,
        items: section.items.filter(item => hasRequiredPermission(userPermissions, item.permissions))
    })).filter(section => section.items.length > 0);
};