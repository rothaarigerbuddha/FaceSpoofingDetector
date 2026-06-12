import { getImageUrlFromPath } from '@/lib/utils';
import { Article, IArticle } from '@/types/article.types'
import Image from 'next/image'
import Link from 'next/link'


export default function ArticleCard({ article }: { article: IArticle }) {

  const articleImage = article.image?.startsWith('http') ? article.image : getImageUrlFromPath(article.image);

  return (
    <Link href={`/articles/${article.slug}`} className="group flex flex-col">
      {/* Image */}
      <div className="relative overflow-hidden aspect-4/3 mb-4">
        <img
          src={articleImage || '/images/placeholder.png'}
          alt={article.title}
          // fill
          className="object-cover transition-transform duration-500 ease-out group-hover:scale-[1.04]"
          // sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
      </div>

      {/* Text */}
      <div className="flex flex-col gap-2">
        {/* <span className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-light">
          {article.category}
        </span> */}

        <h3 className="font-serif text-xl leading-snug text-foreground group-hover:opacity-70 transition-opacity duration-200">
          {article.title}
        </h3>

        <p className="text-sm text-muted-foreground leading-relaxed font-light line-clamp-3">
          {article.notes}
        </p>
      </div>
    </Link>
  )
}