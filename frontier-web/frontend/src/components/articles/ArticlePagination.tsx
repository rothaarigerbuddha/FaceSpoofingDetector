"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

interface ArticlePaginationProps {
  page: number;
  pageSize: number;
  total: number;
}

export function ArticlePagination({ page, pageSize, total }: ArticlePaginationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  const createPageUrl = (pageNumber: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", pageNumber.toString());
    return `${pathname}?${params.toString()}`;
  };

  const handlePageChange = (e: React.MouseEvent<HTMLAnchorElement>, pageNumber: number) => {
    e.preventDefault();
    router.push(createPageUrl(pageNumber));
  };

  return (
    <Pagination className="mt-4 justify-end">
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious 
            href={page > 1 ? createPageUrl(page - 1) : "#"} 
            onClick={(e) => {
                if (page <= 1) e.preventDefault();
                else handlePageChange(e, page - 1);
            }}
            className={page <= 1 ? "pointer-events-none opacity-50" : ""}
          />
        </PaginationItem>
        <PaginationItem>
          <div className="text-sm px-4">
            Page {page} of {totalPages}
          </div>
        </PaginationItem>
        <PaginationItem>
          <PaginationNext 
            href={page < totalPages ? createPageUrl(page + 1) : "#"} 
            onClick={(e) => {
                if (page >= totalPages) e.preventDefault();
                else handlePageChange(e, page + 1);
            }}
            className={page >= totalPages ? "pointer-events-none opacity-50" : ""}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
