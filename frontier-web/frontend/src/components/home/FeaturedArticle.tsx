// src/components/home/FeaturedArticle.tsx
import { FeaturedArticleProps } from '@/types/article.types'
import Image from 'next/image'
import Link from 'next/link'

export default function FeaturedArticle({
  title = 'Vitaliy Shchepanskyi.',
  subtitle = 'The Measure of Fragility',
  excerpt = 'There are cracks that remain unfilled not because they are empty, but because they are already filled with what has happened.',
  slug = '/articles/featured',
  imageUrl = 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1400&q=85',
  imageAlt = 'Featured article',
  category = 'Featured',
}: FeaturedArticleProps) {
  return (
    <section className="container mt-6">
      <div className='w-full bg-[#e8e8e6] dark:bg-zinc-500 '>
        <Link href={slug} className="group block">
        <div className="grid grid-cols-1 md:grid-cols-[5fr_8fr] min-h-130">

          {/* Left — text panel */}
          <div className="flex flex-col justify-center px-10 py-16 md:px-14 lg:px-20">
            <span className="text-[10px] uppercase tracking-[0.25em] text-zinc-600 dark:text-zinc-300 mb-8 ">
              {category}
            </span>

            <h2 className="font-serif text-3xl md:text-4xl leading-snug text-zinc-800 dark:text-zinc-100 mb-6 font-normal">
              {title}
              <br />
              {subtitle}
            </h2>

            <p className="text-sm text-zinc-500 dark:text-zinc-300 leading-relaxed max-w-xs font-light">
              {excerpt}
            </p>

            <div className="mt-10 flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-300 tracking-widest uppercase">
              <span className="inline-block w-5 h-px bg-zinc-400 dark:bg-zinc-300 transition-all duration-300 group-hover:w-10" />
              Read
            </div>
          </div>

          {/* Right — image */}
          <div className="relative overflow-hidden min-h-80 md:min-h-0">
            <Image
              src={imageUrl}
              alt={imageAlt}
              fill
              priority
              className="object-cover transition-transform duration-700 ease-out group-hover:scale-[1.03]"
              sizes="(max-width: 768px) 100vw, 60vw"
            />
           
          </div>
        </div>
      </Link>
      </div>
    </section>
  )
}