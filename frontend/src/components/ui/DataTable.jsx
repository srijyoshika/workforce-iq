import React from 'react';
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
} from 'lucide-react';
import clsx from 'clsx';
import Input from './Input';
import Button from './Button';
import EmptyState from './EmptyState';
import { TableSkeleton } from './Skeleton';

export function DataTable({
  columns = [],
  data = [],
  total = 0,
  page = 1,
  pageSize = 20,
  totalPages = 1,
  isLoading = false,
  sortBy = '',
  sortOrder = 'asc',
  onSort,
  onPageChange,
  onPageSizeChange,
  searchQuery = '',
  onSearchChange,
  searchPlaceholder = 'Search records...',
  filterComponent,
  actionComponent,
  onRowClick,
  emptyTitle = 'No data available',
  emptyDescription = 'No matching records found.',
  className = '',
}) {
  const handleSort = (columnKey, sortable) => {
    if (!sortable || !onSort) return;
    if (sortBy === columnKey) {
      onSort(columnKey, sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      onSort(columnKey, 'asc');
    }
  };

  const startRecord = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRecord = Math.min(page * pageSize, total);

  return (
    <div className={`rounded-xl border border-slate-200/90 bg-white shadow-card overflow-hidden flex flex-col ${className}`}>
      {/* Controls Bar */}
      {(onSearchChange || filterComponent || actionComponent) && (
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50/50">
          <div className="flex flex-1 items-center gap-3 w-full sm:w-auto">
            {onSearchChange && (
              <div className="w-full sm:w-72">
                <Input
                  icon={Search}
                  placeholder={searchPlaceholder}
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="bg-white h-9 text-xs"
                />
              </div>
            )}
            {filterComponent}
          </div>
          {actionComponent && <div className="flex items-center gap-2 self-end sm:self-auto">{actionComponent}</div>}
        </div>
      )}

      {/* Table Content */}
      <div className="flex-1 overflow-x-auto relative">
        {isLoading ? (
          <TableSkeleton rows={pageSize > 10 ? 8 : pageSize} cols={columns.length} />
        ) : data.length === 0 ? (
          <EmptyState title={emptyTitle} description={emptyDescription} />
        ) : (
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/80 font-bold uppercase tracking-wider text-slate-500">
                {columns.map((col, idx) => (
                  <th
                    key={col.key || idx}
                    className={clsx(
                      'py-3 px-4 font-semibold select-none',
                      col.sortable && 'cursor-pointer hover:bg-slate-100 transition-colors',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center',
                      col.className
                    )}
                    onClick={() => handleSort(col.sortKey || col.key, col.sortable)}
                  >
                    <div
                      className={clsx(
                        'flex items-center gap-1.5',
                        col.align === 'right' && 'justify-end',
                        col.align === 'center' && 'justify-center'
                      )}
                    >
                      <span>{col.header}</span>
                      {col.sortable && (
                        <span className="text-slate-400">
                          {sortBy === (col.sortKey || col.key) ? (
                            sortOrder === 'asc' ? (
                              <ArrowUp className="h-3.5 w-3.5 text-blue-600" />
                            ) : (
                              <ArrowDown className="h-3.5 w-3.5 text-blue-600" />
                            )
                          ) : (
                            <ArrowUpDown className="h-3 w-3 opacity-40 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {data.map((row, rowIdx) => (
                <tr
                  key={row.id || rowIdx}
                  onClick={() => onRowClick && onRowClick(row)}
                  className={clsx(
                    'transition-colors hover:bg-slate-50/80',
                    onRowClick && 'cursor-pointer'
                  )}
                >
                  {columns.map((col, colIdx) => (
                    <td
                      key={col.key || colIdx}
                      className={clsx(
                        'py-3 px-4 text-slate-700',
                        col.align === 'right' && 'text-right',
                        col.align === 'center' && 'text-center',
                        col.className
                      )}
                    >
                      {col.cell ? col.cell(row) : row[col.accessorKey || col.key] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      {total > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between border-t border-slate-100 bg-slate-50/50 px-4 py-3 gap-3 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>
              Showing <span className="font-semibold text-slate-800">{startRecord}</span> to{' '}
              <span className="font-semibold text-slate-800">{endRecord}</span> of{' '}
              <span className="font-semibold text-slate-800">{total}</span> records
            </span>

            {onPageSizeChange && (
              <div className="ml-4 flex items-center gap-1.5">
                <span>Rows:</span>
                <select
                  value={pageSize}
                  onChange={(e) => onPageSizeChange(Number(e.target.value))}
                  className="rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  {[10, 20, 50, 100].map((sz) => (
                    <option key={sz} value={sz}>
                      {sz}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1">
            <span className="mr-2">
              Page <span className="font-semibold text-slate-800">{page}</span> of{' '}
              <span className="font-semibold text-slate-800">{totalPages || 1}</span>
            </span>

            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || isLoading}
              onClick={() => onPageChange(1)}
              className="h-8 w-8 p-0"
              title="First Page"
            >
              <ChevronsLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1 || isLoading}
              onClick={() => onPageChange(page - 1)}
              className="h-8 w-8 p-0"
              title="Previous Page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages || isLoading}
              onClick={() => onPageChange(page + 1)}
              className="h-8 w-8 p-0"
              title="Next Page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages || isLoading}
              onClick={() => onPageChange(totalPages)}
              className="h-8 w-8 p-0"
              title="Last Page"
            >
              <ChevronsRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default DataTable;
