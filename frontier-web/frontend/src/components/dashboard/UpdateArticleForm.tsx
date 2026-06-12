// 'use client'

// import { useState, useCallback } from 'react'
// import dynamic from 'next/dynamic'
// import { Input } from '@/components/ui/input'
// import { Label } from '@/components/ui/label'
// import { Textarea } from '@/components/ui/textarea'
// import 'react-quill-new/dist/quill.snow.css'
// import { generateSlug, getImageUrlFromPath } from '@/lib/utils'
// import { createArticle, updateArticle, uploadImage } from '@/services/article.service'
// import { toast } from 'sonner'
// import AppButton from '../ui/AppButton'
// import { IArticle } from '@/types/article.types'

// const ReactQuill = dynamic(() => import('react-quill-new'), { ssr: false })


// export default function UpdateArticleForm({article} : {article: IArticle}) {
//   const [title, setTitle] = useState(article.title ?? '')
//   const [slug, setSlug] = useState(article.slug ?? '')
//   const [content, setContent] = useState(article.content ?? '')
//   const [notes, setNotes] = useState(article.notes ?? '')
//   const [author, setAuthor] = useState(article.author ?? '')
//   const [image, setImage] = useState<File | null>(null)
//   const [imagePreview, setImagePreview] = useState<string | null>(null)
//   const [loading, setLoading] = useState(false)

//   const handleTitleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
//     const val = e.target.value
//     setTitle(val)
//     setSlug(generateSlug(val))
//   }, [])

//   const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const file = e.target.files?.[0] ?? null
//     setImage(file)
//     if (file) {
//       setImagePreview(URL.createObjectURL(file))
//     } else {
//       setImagePreview(null)
//     }
//   }

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault()
//     setLoading(true)
//     try {
      
//       const formData = new FormData()
//       if (image) formData.append('file', image)

//       const imageUpRes = image ? await uploadImage(formData) : null;

//       const articleData = {
//         title,
//         slug,
//         content,
//         notes,
//         author,
//         image:  getImageUrlFromPath(imageUpRes.url),
//         published: true,
//       }
    
//       const result = await updateArticle(article.id, articleData);

//       toast.success('Article updated successfully!')

//     } catch (error) {
//       setLoading(false)
//       console.error("Error submitting article:", error)
//     }
//      finally {
//       setLoading(false)
//     }
//   }

//   const inputClass =
//     'rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200'

//   const labelClass =
//     'text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-light'

//   return (
//     <form onSubmit={handleSubmit} className="flex flex-col gap-10 font-sans">

//       {/* Title + Slug */}
//       <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
//         <div className="flex flex-col gap-2">
//           <Label htmlFor="title" className={labelClass}>Title *</Label>
//           <Input
//             id="title"
//             value={title}
//             onChange={handleTitleChange}
//             placeholder="Article title"
//             required
//             className={inputClass}
//           />
//         </div>

//         {/* Author */}
//         <div className="flex flex-col gap-2 max-w-sm">
//             <Label htmlFor="author" className={labelClass}>Author *</Label>
//             <Input
//             id="author"
//             value={author}
//             onChange={(e) => setAuthor(e.target.value)}
//             placeholder="Author name"
//             required
//             className={inputClass}
//             />
//         </div>
//       </div>



//       {/* Cover Image */}
//       <div className="flex flex-col gap-3">
//         <Label className={labelClass}>Cover Image</Label>
//         <label
//           htmlFor="image"
//           className="flex flex-col items-center justify-center w-full h-48 border border-dashed border-border hover:border-foreground transition-colors duration-200 cursor-pointer overflow-hidden relative"
//         >
//           {imagePreview ? (
//             // eslint-disable-next-line @next/next/no-img-element
//             <img
//               src={imagePreview}
//               alt="Cover preview"
//               className="absolute inset-0 w-full h-full object-cover"
//             />
//           ) : (
//             <div className="flex flex-col items-center gap-2 text-muted-foreground">
//               <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
//                 <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
//                 <polyline points="17 8 12 3 7 8"/>
//                 <line x1="12" y1="3" x2="12" y2="15"/>
//               </svg>
//               <span className="text-xs uppercase tracking-[0.15em]">Upload cover image</span>
//               <span className="text-[10px] text-muted-foreground/60">PNG, JPG, WEBP</span>
//             </div>
//           )}
//           <input
//             id="image"
//             type="file"
//             accept="image/*"
//             onChange={handleImageChange}
//             className="sr-only"
//           />
//         </label>
//         {imagePreview && (
//           <button
//             type="button"
//             onClick={() => { setImage(null); setImagePreview(null) }}
//             className="self-start text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-colors"
//           >
//             Remove image
//           </button>
//         )}
//       </div>

//       {/* Content — React Quill */}
//       <div className="flex flex-col gap-3">
//         <Label className={labelClass}>Content *</Label>
//         <div className="border border-border [&_.ql-toolbar]:border-border [&_.ql-toolbar]:border-x-0 [&_.ql-toolbar]:border-t-0 [&_.ql-container]:border-0 [&_.ql-editor]:min-h-[320px] [&_.ql-editor]:text-sm [&_.ql-editor]:text-foreground [&_.ql-editor]:font-sans [&_.ql-editor.ql-blank::before]:text-muted-foreground [&_.ql-editor.ql-blank::before]:not-italic">
//           <ReactQuill
//             theme="snow"
//             value={content}
//             onChange={setContent}
//             placeholder="Write your article..."
//             modules={{
//               toolbar: [
//                 [{ header: [1, 2, 3, false] }],
//                 ['bold', 'italic', 'underline', 'strike', 'blockquote'],
//                 [{ list: 'ordered' }, { list: 'bullet' }],
//                 ['link', 'image'],
//                 ['clean'],
//               ],
//             }}
//           />
//         </div>
//       </div>

//       {/* Notes (optional) */}
//       <div className="flex flex-col gap-2">
//         <Label htmlFor="notes" className={labelClass}>
//           Annoation  <span className="normal-case tracking-normal opacity-50">(optional)</span>
//         </Label>
//         <Textarea
//           id="notes"
//           value={notes}
//           onChange={(e) => setNotes(e.target.value)}

//           rows={3}
//           className="rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200 resize-none"
//         />
//       </div>

//       {/* Submit */}
//       <div className="flex items-center gap-4 pt-2 border-t border-border">
//         <AppButton type="submit" size="lg" disabled={loading}>
//           {loading ? 'Updating...' : 'Update Article'}
//         </AppButton>
//       </div>

//     </form>
//   )
// }

















'use client'

import { useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import 'react-quill-new/dist/quill.snow.css'
import { generateSlug, getImageUrlFromPath } from '@/lib/utils'
import { updateArticle, uploadImage } from '@/services/article.service'
import { toast } from 'sonner'
import { IArticle } from '@/types/article.types'
import AppButton from '@/components/ui/AppButton'

const ReactQuill = dynamic(() => import('react-quill-new'), { ssr: false })


export default function UpdateArticleForm({ article }: { article: IArticle }) {
  const [title, setTitle] = useState(article.title ?? '')
  const [slug, setSlug] = useState(article.slug ?? '')
  const [content, setContent] = useState(article.content ?? '')
  const [notes, setNotes] = useState(article.notes ?? '')
  const [author, setAuthor] = useState(article.author ?? '')
  const [image, setImage] = useState<File | null>(null)
  // Fix 4: initialize preview with the existing article image
  const [imagePreview, setImagePreview] = useState<string | null>(article.image ?? null)
  const [loading, setLoading] = useState(false)

  const handleTitleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setTitle(val)
    setSlug(generateSlug(val))
  }, [])

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null
    setImage(file)
    if (file) {
      setImagePreview(URL.createObjectURL(file))
    } else {
      setImagePreview(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      // Fix 1 & 5: only upload + build new URL if a new file was selected,
      // otherwise keep the existing article.image untouched
      let imageUrl = article.image ?? null
      if (image) {
        const formData = new FormData()
        formData.append('file', image)
        const imageUpRes = await uploadImage(formData)
        imageUrl = getImageUrlFromPath(imageUpRes?.url ?? null)
      }

      // Fix 3: include slug in the payload
      const articleData = {
        title,
        slug,
        content,
        notes,
        author,
        image: imageUrl,
        published: true,
      }

      // Fix 2: removed unused `result` variable
      await updateArticle(article.id, articleData)
      toast.success('Article updated successfully!')
    } catch (error) {
      console.error('Error submitting article:', error)
      toast.error('Failed to update article.')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200'

  const labelClass =
    'text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-light'

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-10 font-sans">

      {/* Title + Author */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex flex-col gap-2">
          <Label htmlFor="title" className={labelClass}>Title *</Label>
          <Input
            id="title"
            value={title}
            onChange={handleTitleChange}
            placeholder="Article title"
            required
            className={inputClass}
          />
        </div>

        <div className="flex flex-col gap-2 max-w-sm">
          <Label htmlFor="author" className={labelClass}>Author *</Label>
          <Input
            id="author"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Author name"
            required
            className={inputClass}
          />
        </div>
      </div>

      {/* Cover Image */}
      <div className="flex flex-col gap-3">
        <Label className={labelClass}>Cover Image</Label>
        <label
          htmlFor="image"
          className="flex flex-col items-center justify-center w-full h-48 border border-dashed border-border hover:border-foreground transition-colors duration-200 cursor-pointer overflow-hidden relative"
        >
          {imagePreview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={imagePreview}
              alt="Cover preview"
              className="absolute inset-0 w-full h-full object-cover"
            />
          ) : (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <span className="text-xs uppercase tracking-[0.15em]">Upload cover image</span>
              <span className="text-[10px] text-muted-foreground/60">PNG, JPG, WEBP</span>
            </div>
          )}
          <input
            id="image"
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            className="sr-only"
          />
        </label>
        {imagePreview && (
          <button
            type="button"
            // Fix 4: reset to null (not the original) so the upload area shows
            onClick={() => { setImage(null); setImagePreview(null) }}
            className="self-start text-[10px] uppercase tracking-[0.2em] text-muted-foreground hover:text-foreground transition-colors"
          >
            Remove image
          </button>
        )}
      </div>

      {/* Content — React Quill */}
      <div className="flex flex-col gap-3">
        <Label className={labelClass}>Content *</Label>
        <div className="border border-border [&_.ql-toolbar]:border-border [&_.ql-toolbar]:border-x-0 [&_.ql-toolbar]:border-t-0 [&_.ql-container]:border-0 [&_.ql-editor]:min-h-[320px] [&_.ql-editor]:text-sm [&_.ql-editor]:text-foreground [&_.ql-editor]:font-sans [&_.ql-editor.ql-blank::before]:text-muted-foreground [&_.ql-editor.ql-blank::before]:not-italic">
          <ReactQuill
            theme="snow"
            value={content}
            onChange={setContent}
            placeholder="Write your article..."
            modules={{
              toolbar: [
                [{ header: [1, 2, 3, false] }],
                ['bold', 'italic', 'underline', 'strike', 'blockquote'],
                [{ list: 'ordered' }, { list: 'bullet' }],
                ['link', 'image'],
                ['clean'],
              ],
            }}
          />
        </div>
      </div>

      {/* Notes (optional) */}
      <div className="flex flex-col gap-2">
        <Label htmlFor="notes" className={labelClass}>
          Annotation <span className="normal-case tracking-normal opacity-50">(optional)</span>
        </Label>
        <Textarea
          id="notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="rounded-none border-0 border-b border-border bg-transparent px-0 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:border-foreground transition-colors duration-200 resize-none"
        />
      </div>

      {/* Submit */}
      <div className="flex items-center gap-4 pt-2 border-t border-border">
        <AppButton type="submit" size="lg" disabled={loading}>
          {loading ? 'Updating...' : 'Update Article'}
        </AppButton>
      </div>

    </form>
  )
}