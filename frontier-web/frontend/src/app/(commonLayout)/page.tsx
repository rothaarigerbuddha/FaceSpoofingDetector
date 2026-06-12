import FeaturedArticle from "@/components/home/FeaturedArticle";
import ArticleGrid from "@/components/home/ArticleGrid";
import { getAllArticles } from "@/services/article.service";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default async function Home(
  props: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>
  }
) {
  const searchParams = await props.searchParams;
  
  const rawPage = searchParams.page;
  let page = 1;
  if (typeof rawPage === 'string') {
    const parsed = parseInt(rawPage, 10);
    if (!isNaN(parsed) && parsed > 0) {
      page = parsed;
    }
  }

  const rawQ = searchParams.q;
  const q = typeof rawQ === 'string' ? rawQ : undefined;

  const initialArticlesResponse = await getAllArticles({ page, pageSize: 9, published: true, q });

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-white font-sans dark:bg-black">
      {!q && <FeaturedArticle />}
      {/* {q && <Link href="/" className="text-2xl mt-6 text-left w-full container">Back to all </Link>} */}
      {q && (
        <div className="w-full container mt-8 space-y-1">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to all
          </Link>
          <div className="flex items-baseline gap-2 mt-6">
            <p className="text-sm font-medium text-muted-foreground uppercase tracking-widest">
              Search Results for:
            </p>
            <h2 className="text-sm font-bold uppercase tracking-widest text-foreground">
              {q}
            </h2>
          </div>
        </div>
      )}
       <ArticleGrid data={initialArticlesResponse} q={q} />
    </div>
  );
}
