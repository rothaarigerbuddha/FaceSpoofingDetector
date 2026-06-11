import { getUserInfo, getUserPermissions as getMyPermissions } from "@/services/auth.service";
import { hasRequiredPermission } from "@/lib/authUtils";
import { redirect } from "next/navigation";
import { getRoles, getPermissions } from "@/services/admin.service";
import RolesPermissionsManager from "@/components/admin/RolesPermissionsManager";

export default async function RolesPermissionsPage() {
    const userInfo = await getUserInfo();
    if (!userInfo) redirect("/login");

    const userPermissions = await getMyPermissions(userInfo.username);
    
    if (!hasRequiredPermission(userPermissions, ["users.manage"])) {
        redirect("/dashboard");
    }

    const [roles, permissions] = await Promise.all([
        getRoles(),
        getPermissions()
    ]);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-2">Roles & Permissions Management</h1>
            <p className="text-gray-600">This area is restricted to administrators.</p>
            
            <RolesPermissionsManager roles={roles} permissions={permissions} />
        </div>
    );
}
