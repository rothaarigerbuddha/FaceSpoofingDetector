"use client";

import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, SquarePen, Eye, Trash2 } from "lucide-react";
import { IArticle } from "@/types/article.types";
import { useRouter } from "next/navigation";
import DeleteArticleDialog from "./DeleteArticleDialog";
import { hasRequiredPermission } from "@/lib/authUtils";

interface ArticleTableActionsProps {
  article: IArticle;
  userPermissions: string[];
}

export function ArticleTableActions({ article, userPermissions }: ArticleTableActionsProps) {
  const router = useRouter(); 
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          className="inline-flex items-center justify-center uppercase font-light transition-all duration-200 cursor-pointer disabled:opacity-40 disabled:pointer-events-none select-none text-foreground hover:bg-muted h-8 w-8 p-0 rounded-md"
        >
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => router.push(`/articles/${article.slug}`)}>
            <Eye className="mr-2 h-4 w-4" />
            <span>View</span>
          </DropdownMenuItem>
          {hasRequiredPermission(userPermissions, ['posts.write']) && (
            <DropdownMenuItem onClick={() => router.push(`/dashboard/update/${article.id}`)}>
              <SquarePen className="mr-2 h-4 w-4" />
              <span>Edit</span>
            </DropdownMenuItem>
          )}
          {(hasRequiredPermission(userPermissions, ['posts.write']) || hasRequiredPermission(userPermissions, ['posts.delete'])) && (
            <DropdownMenuSeparator />
          )}
          {hasRequiredPermission(userPermissions, ['posts.delete']) && (
            <DropdownMenuItem
              className="text-destructive focus:bg-destructive/10 focus:text-destructive"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              <span>Delete</span>
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      
      <DeleteArticleDialog
        article={article}
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
      />
    </>
  );
}
