import { getUserInfo, getUserPermissions as getMyPermissions } from "@/services/auth.service";
import { hasRequiredPermission } from "@/lib/authUtils";
import { redirect } from "next/navigation";
import { getUsers } from "@/services/user.service";
import { getRoles } from "@/services/admin.service";
import UsersManager from "@/components/admin/UsersManager";

export default async function UsersPage() {
    const userInfo = await getUserInfo();
    if (!userInfo) redirect("/login");

    const userPermissions = await getMyPermissions(userInfo.username);

    if (!hasRequiredPermission(userPermissions, ["users.manage"])) {
        redirect("/dashboard");
    }

    const [users, roles] = await Promise.all([
        getUsers(),
        getRoles(),
    ]);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-1">User Management</h1>
            <p className="text-gray-500 text-sm mb-6">
                Create and manage system users and their role assignments.
            </p>

            <UsersManager users={users} roles={roles} />
        </div>
    );
}
