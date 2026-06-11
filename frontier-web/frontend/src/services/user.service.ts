"use server"

import { httpClient } from "@/lib/axios/httpClient";
import { revalidatePath } from "next/cache";


export async function getUsers() {
    try {
        const users = await httpClient.get("/users");
        return Array.isArray(users) ? users : [];
    } catch (error) {
        console.error("Failed to fetch users:", error);
        return [];
    }
}

export async function createUser(formData: FormData) {
    try {
        const username = formData.get("username")?.toString();
        const password = formData.get("password")?.toString();
        const roleIdsStr = formData.get("roleIds")?.toString();

        if (!username) return { error: "Username is required" };
        if (!password) return { error: "Password is required (min 6 chars)" };

        const roleIds = roleIdsStr ? JSON.parse(roleIdsStr) : undefined;

        await httpClient.post("/users", { username, password, roleIds });

        revalidatePath("/dashboard/users");
        return { success: true };
    } catch (error: any) {
        const msg = typeof error?.response?.data === "string"
            ? error.response.data
            : "Failed to create user";
        return { error: msg };
    }
}

export async function updateUserRoles(userId: number, roleIds: number[]) {
    try {
        await httpClient.put(`/users/${userId}/roles`, { roleIds });
        revalidatePath("/dashboard/users");
        return { success: true };
    } catch (error: any) {
        const msg = typeof error?.response?.data === "string"
            ? error.response.data
            : "Failed to update roles";
        return { error: msg };
    }
}

export async function deleteUser(id: number) {
    try {
        await httpClient.delete(`/users/${id}`);
        revalidatePath("/dashboard/users");
        return { success: true };
    } catch (error: any) {
        return { error: "Delete failed" };
    }
}
