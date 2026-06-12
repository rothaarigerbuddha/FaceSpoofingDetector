"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { IArticlePaginatedResponse } from "@/types/article.types";
import { ArticleTableActions } from "./ArticleTableActions";
import { formatDate } from "@/lib/utils";

interface ArticleTableProps {
  data: IArticlePaginatedResponse;
  userPermissions: string[];
}

export function ArticleTable({ data, userPermissions }: ArticleTableProps) {
  const { items } = data;

  return (
    <div className="border mt-4">
      <Table>
        <TableHeader className="bg-muted/50">
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>Author</TableHead>
            <TableHead>Published</TableHead>
            <TableHead>Created At</TableHead>
            <TableHead className="w-20"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items && items.length > 0 ? (
            items.map((article) => (
              <TableRow key={article.id}>
                <TableCell className="font-medium">{article.title}</TableCell>
                <TableCell>{article.author}</TableCell>
                <TableCell>
                  {article.published ? (
                    <span className="text-green-700 dark:text-green-400 bg-green-500/10 px-2 py-1 rounded-full text-xs">Yes</span>
                  ) : (
                    <span className="text-muted-foreground bg-muted px-2 py-1 rounded-full text-xs">No</span>
                  )}
                </TableCell>
                <TableCell>{formatDate(article.createdAtUtc)}</TableCell>
                <TableCell>
                  <ArticleTableActions article={article} userPermissions={userPermissions} />
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                No articles found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}
