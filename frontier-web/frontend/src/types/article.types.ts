
export interface FeaturedArticleProps {
  title?: string
  subtitle?: string
  excerpt?: string
  slug?: string
  imageUrl?: string
  imageAlt?: string
  category?: string
}

export interface Article {
  id: string
  title: string
  excerpt: string
  slug: string
  imageUrl: string
  imageAlt: string
  category: string
  date: string
}

export interface IArticle {
  id: number;
  title: string;
  slug: string;
  content: string;
  notes?: string | null;
  author: string;
  image: string | null;
  published: boolean;
  createdAtUtc: string;
  updatedAtUtc: string;
}

export interface IArticlePaginatedResponse {
  items: IArticle[];
  total: number;
  page: number;
  pageSize: number;
}