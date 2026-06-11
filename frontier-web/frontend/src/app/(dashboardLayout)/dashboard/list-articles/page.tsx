import { getAllArticles } from "@/services/article.service";
import { ArticleTable } from "@/components/articles/ArticleTable";
import { ArticleSearch } from "@/components/articles/ArticleSearch";
import { ArticlePagination } from "@/components/articles/ArticlePagination";
import { getUserInfo, getUserPermissions } from "@/services/auth.service";

export default async function ListArticlePage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const searchParams = await props.searchParams;
  const q = typeof searchParams.q === "string" ? searchParams.q : "";
  const page = typeof searchParams.page === "string" ? parseInt(searchParams.page, 10) : 1;
  const pageSize = 10;

  const data = await getAllArticles({ q, page, pageSize });

  const userInfo = await getUserInfo();
  const userPermissions = userInfo ? await getUserPermissions(userInfo.username) : [];

  return (
    <div className="flex flex-col gap-4 p-4 md:p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Articles</h1>
      </div>
      
      <div className="flex items-center justify-between">
        <ArticleSearch />
      </div>

      <ArticleTable data={data} userPermissions={userPermissions} />
      
      <ArticlePagination 
        page={data.page} 
        pageSize={data.pageSize} 
        total={data.total} 
      />
    </div>
  );
}
