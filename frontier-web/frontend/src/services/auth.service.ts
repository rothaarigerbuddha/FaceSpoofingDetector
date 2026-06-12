"use server"

import { httpClient } from "@/lib/axios/httpClient";
import { setCookie, deleteCookie, getCookie } from "@/lib/cookieUtils";

export async function logoutUser() {
    await deleteCookie("access_token");
}
export async function loginUser(payload: { username: string; password: string }) {
  try {
    const res = await httpClient.post("/auth/login", payload);

    if (!res.access_token) {
      throw new Error("Login failed: no token received.");
    }

    const { access_token, token_type, expires_in } = res;

    await setCookie("access_token", access_token, expires_in);

    return { access_token, token_type, expires_in };

  } catch (error: any) {
    if (error?.response) {
      const status: number = error.response.status;
      const data = error.response.data;

      if (status === 401) {
        const detail = data?.detail ?? "Invalid username or password.";
        throw new Error(detail);
      }

      if (data) {
        const message =
          typeof data === "string"
            ? data
            : data?.message ?? data?.title ?? `Server error (${status})`;
        throw new Error(message);
      }

      throw new Error(`Server error (${status}).`);
    }

    throw new Error("Unable to reach the server. Please check your connection.");
  }
}




export async function getUserInfo() {
    const token = await getCookie("access_token");

    if (!token) return null;

    try {
        // JWT is base64url: header.payload.signature — decode only the payload
        const payloadBase64 = token.split(".")[1];
        // base64url → base64
        const base64 = payloadBase64.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = Buffer.from(base64, "base64").toString("utf-8");
        const claims = JSON.parse(jsonPayload);

        // The backend stores: ClaimTypes.Name = username, ClaimTypes.Role = role(s)
        // .NET maps these to "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
        // and "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
        const username =
            claims["http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"] ??
            claims["name"] ??
            claims["unique_name"] ??
            "Unknown";

        const roleClaim =
            claims["http://schemas.microsoft.com/ws/2008/06/identity/claims/role"] ??
            claims["role"] ??
            [];

        const roles: string[] = Array.isArray(roleClaim) ? roleClaim : [roleClaim];

        return { username, roles };
    } catch {
        return null;
    }
}

export async function getUserPermissions(username: string): Promise<string[]> {
    try {
        const users = await httpClient.get("/users");
        
        if (!Array.isArray(users)) return [];

        const user = users.find((u: any) => u.username === username);

        if (!user || !Array.isArray(user.roles)) return [];

        const permissions = user.roles.flatMap((role: any) => 
            Array.isArray(role.permissions) 
                ? role.permissions.map((p: any) => p.name) 
                : []
        );

        return Array.from(new Set(permissions));
    } catch (error) {
        console.error("Failed to fetch user permissions", error);
        return [];
    }
}
