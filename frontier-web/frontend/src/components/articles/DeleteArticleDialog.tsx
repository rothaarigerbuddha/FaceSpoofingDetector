'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { deleteArticle } from '@/services/article.service'
import { IArticle } from '@/types/article.types'

interface DeleteArticleDialogProps {
  article: IArticle
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function DeleteArticleDialog({ article, open, onOpenChange }: DeleteArticleDialogProps) {
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleDelete = async () => {
    setLoading(true)
    try {
      await deleteArticle(article.id)
      toast.success('Article deleted successfully.')
      onOpenChange(false)
      router.push('/dashboard')
      router.refresh()
    } catch (error) {
      console.error('Error deleting article:', error)
      toast.error('Failed to delete article.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="rounded-none border-border max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="font-serif text-xl font-normal text-foreground">
            Delete Article
          </AlertDialogTitle>
          <AlertDialogDescription className="text-sm text-muted-foreground leading-relaxed">
            Are you sure you want to delete{' '}
            <span className="text-foreground font-medium">"{article.title}"</span>?
            <br />
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter className="gap-2 sm:gap-2">
          <AlertDialogCancel
            disabled={loading}
            className="rounded-none border-border text-[10px] uppercase tracking-[0.2em] font-light h-9 px-4"
          >
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={loading}
            className="rounded-none bg-destructive text-destructive-foreground hover:bg-destructive/90 text-[10px] uppercase tracking-[0.2em] font-light h-9 px-4"
          >
            {loading ? 'Deleting...' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}