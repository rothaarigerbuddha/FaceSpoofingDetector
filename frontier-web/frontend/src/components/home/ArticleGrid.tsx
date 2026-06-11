import { IArticlePaginatedResponse } from '@/types/article.types'
import ArticleCard from './ArticleCard'
import AppButton from '../ui/AppButton'
import Link from 'next/link'

export default function ArticleGrid({ data, q }: { data: IArticlePaginatedResponse, q?: string }) {
  const hasNext = (data.page * data.pageSize) < data.total;
  const hasPrevious = data.page > 1;

  const getHref = (targetPage: number) => {
    return `/?page=${targetPage}${q ? `&q=${encodeURIComponent(q)}` : ''}`;
  }

  return (
    <section className="container py-16">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-14">
        {data.items.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>
      
      <div className='flex items-center justify-center gap-4 mt-12'>
        {hasPrevious && (
          <Link href={getHref(data.page - 1)}>
             <AppButton className='w-fit'>
                Previous
             </AppButton>
          </Link>
        )}
        
        {hasNext && (
          <Link href={getHref(data.page + 1)}>
            <AppButton className='w-fit'>
               Next
            </AppButton>
          </Link>
        )}
      </div>
    </section>
  )
}