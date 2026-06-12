import axios, { AxiosInstance } from "axios";
import { cookies } from "next/headers";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5160";

if (!BASE_URL) {
  throw new Error("API_BASE_URL or NEXT_PUBLIC_API_BASE_URL is not defined in environment variables");
}

export interface ApiRequestOptions {
    params?: Record<string, any>;
    headers?: Record<string, string>;
}

const axiosInstance = async () : Promise<AxiosInstance> => {
    const cookieStore = await cookies();
    const token = cookieStore.get("access_token")?.value;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const instance = axios.create({
        baseURL: BASE_URL,
        withCredentials: true,
        headers
    });

    return instance;
}


const httpGet = async (endpoint: string, options?: ApiRequestOptions) => {
    try {
        
        const instance = await axiosInstance();
        const response = await instance.get(endpoint, {
            params: options?.params,
            headers: options?.headers
        });

        return response.data;

    } catch (error) {
        console.log(`GET request to ${endpoint} failed:`, error);
        throw error;
    }
}

const httpPost = async (endpoint: string, data: any, options?: ApiRequestOptions) => {
    try {
        const instance = await axiosInstance();
        const response = await instance.post(endpoint, data, {
            params: options?.params,
            headers: options?.headers
        });

        return response.data;
    } catch (error) {
        console.log(`POST request to ${endpoint} failed:`, error);
        throw error;
    }
}


const httpPut = async (endpoint: string, data: any, options?: ApiRequestOptions) => {
    try {
        const instance = await axiosInstance();
        const response = await instance.put(endpoint, data, {
            params: options?.params,
            headers: options?.headers
        });

        return response.data;
    } catch (error) {
        console.log(`PUT request to ${endpoint} failed:`, error);
        throw error;
    }
}

const httpDelete = async (endpoint: string, options?: ApiRequestOptions) => {
    try {
        const instance = await axiosInstance();
        const response = await instance.delete(endpoint, {
            params: options?.params,
            headers: options?.headers
        });

        return response.data;
    } catch (error) {
        console.log(`DELETE request to ${endpoint} failed:`, error);
        throw error;
    }
}

export const httpClient = {
    get: httpGet,
    post: httpPost,
    put: httpPut,
    delete: httpDelete
}