"use server"

import { httpClient } from "@/lib/axios/httpClient";
import { IArticle, IArticlePaginatedResponse } from "@/types/article.types";

export interface IGetAllArticlesParams {
    q ?: string;
    page ?: number;
    pageSize ?: number;
    published ?: boolean;
}


export const getAllArticles = async (params : IGetAllArticlesParams = {}) : Promise<IArticlePaginatedResponse> => {

    const queryParams : Record<string, any> = {};

    if(params.q) queryParams.q = params.q;
    if(params.page) queryParams.page = params.page;
    if(params.pageSize) queryParams.pageSize = params.pageSize;
    if(params.published !== undefined) queryParams.published = params.published;

    const res = await httpClient.get("/posts", {
        params: queryParams
    })

    return {
        items : res.items,
        total : res.total,
        page : res.page,
        pageSize : res.pageSize
    }
}

export const getPostBySlug = async (slug: string) : Promise<IArticle> => {
    const res = await httpClient.get(`/posts/${slug}`);
    return res;
}


export const uploadImage = async (formData: FormData) => {
    const res = await httpClient.post("/uploads", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });
    return res;
}

export const createArticle = async (articleData: Partial<IArticle>) => {
    const res = await httpClient.post("/posts", articleData, {
        headers: {
            "Content-Type": "application/json",
        },
    });
    return res;
}

export const updateArticle = async (id: string | number, articleData: Partial<IArticle>) => {
    const res = await httpClient.put(`/posts/${id}`, articleData, {
        headers: {
            "Content-Type": "application/json",
        },
    });
    return res;
}

export const deleteArticle = async (id: string | number): Promise<void> => {
  await httpClient.delete(`/posts/${id}`);
}