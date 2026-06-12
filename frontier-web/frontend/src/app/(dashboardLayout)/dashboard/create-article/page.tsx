import CreateArticleForm from '@/components/dashboard/CreateArticleForm'

export default function CreateArticlePage() {
  return (
    <div className="container py-16 max-w-4xl">
      <div className="flex flex-col gap-3 mb-12">
        <h1 className="font-serif text-4xl text-foreground font-normal">
          New Article
        </h1>
      </div>

      <CreateArticleForm
      />
    </div>
  )
}