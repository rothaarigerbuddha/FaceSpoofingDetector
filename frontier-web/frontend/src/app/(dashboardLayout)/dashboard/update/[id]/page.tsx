import UpdateArticleForm from '@/components/dashboard/UpdateArticleForm';
import { getPostBySlug } from '@/services/article.service';
import { getUserInfo, getUserPermissions } from '@/services/auth.service';
import { hasRequiredPermission } from '@/lib/authUtils';
import { redirect } from 'next/navigation';
import React from 'react'
export default async function BlogPostPage({ params }: { params: Promise<{ id: string }> }) {
  const userInfo = await getUserInfo();
  if (!userInfo) redirect('/login');

  const userPermissions = await getUserPermissions(userInfo.username);
  if (!hasRequiredPermission(userPermissions, ['posts.write'])) {
    redirect('/dashboard/list-articles'); // or unauthorized page
  }

  const { id } = await params;

  let article;

  try {
    article = await getPostBySlug(id);
  } catch (error) {
    console.error('Error fetching article:', error);
  }

  if (!article) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-gray-400 text-lg">
        No Article Found
      </div>
    );
  }
  return (
       <div className="container py-16 max-w-4xl">
         <div className="flex flex-col gap-3 mb-12">
           <h1 className="font-serif text-4xl text-foreground font-normal">
             Update Article
           </h1>
         </div>
   
         <UpdateArticleForm article={article}
         />
       </div>
  )
}

