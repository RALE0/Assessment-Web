import { cn } from "@/lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
  children?: React.ReactNode;
}

export function EmptyState({
  title = "No data available",
  description = "Data will appear when available",
  icon: Icon,
  className,
  children
}: EmptyStateProps) {
  return (
    <div className={cn(
      "flex flex-col items-center justify-center text-center py-12 px-4",
      className
    )}>
      {Icon && (
        <Icon className="h-12 w-12 text-gray-400 mb-4" />
      )}
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-500 max-w-sm mb-4">
        {description}
      </p>
      {children}
    </div>
  );
}