"use server";

import { httpClient } from "@/lib/axios/httpClient";
import { revalidatePath } from "next/cache";

export async function getRoles() {
    try {
        const roles = await httpClient.get("/roles");
        return Array.isArray(roles) ? roles : [];
    } catch (error) {
        console.error("Failed to fetch roles:", error);
        return [];
    }
}

export async function getPermissions() {
    try {
        const permissions = await httpClient.get("/permissions");
        return Array.isArray(permissions) ? permissions : [];
    } catch (error) {
        console.error("Failed to fetch permissions:", error);
        return [];
    }
}

export async function createRole(formData: FormData) {
    try {
        const name = formData.get("name")?.toString();
        const permissionIdsStr = formData.get("permissionIds")?.toString();
        
        if (!name) return { error: "Role name is required" };
        
        // 1. Create Role
        const roleResponse = await httpClient.post("/roles", { name });
        
        // 2. Assign initial permissions if any exist
        if (permissionIdsStr && roleResponse?.id) {
            const permissionIds = JSON.parse(permissionIdsStr);
            if (Array.isArray(permissionIds) && permissionIds.length > 0) {
                await httpClient.put(`/roles/${roleResponse.id}/permissions`, { permissionIds });
            }
        }
        
        revalidatePath("/dashboard/roles-permissions");
        return { success: true };
    } catch (error: any) {
        console.error("Failed to create role:", error);
        const errorMessage = typeof error?.response?.data === 'string' 
            ? error.response.data 
            : "Failed to create role";
        return { error: errorMessage };
    }
}

export async function updateRolePermissions(roleId: number, permissionIds: number[]) {
    try {
        await httpClient.put(`/roles/${roleId}/permissions`, { permissionIds });
        revalidatePath("/dashboard/roles-permissions");
        return { success: true };
    } catch (error: any) {
        return { error: typeof error?.response?.data === 'string' ? error.response.data : "Update failed" };
    }
}

export async function deleteRole(id: number) {
    try {
        await httpClient.delete(`/roles/${id}`);
        revalidatePath("/dashboard/roles-permissions");
        return { success: true };
    } catch (error: any) {
        return { error: "Delete failed" };
    }
}

export async function createPermission(formData: FormData) {
    try {
        const name = formData.get("name")?.toString();
        if (!name) return { error: "Permission name is required" };
        
        await httpClient.post("/permissions", { name });
        
        revalidatePath("/dashboard/roles-permissions");
        return { success: true };
    } catch (error: any) {
        console.error("Failed to create permission:", error);
        const errorMessage = typeof error?.response?.data === 'string' 
            ? error.response.data 
            : "Failed to create permission";
        return { error: errorMessage };
    }
}

export async function deletePermission(id: number) {
    try {
        await httpClient.delete(`/permissions/${id}`);
        revalidatePath("/dashboard/roles-permissions");
        return { success: true };
    } catch (error: any) {
        return { error: "Delete failed" };
    }
}

