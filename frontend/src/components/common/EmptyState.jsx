// Empty state component shown when a list or section has no content yet.


export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-4">
          <Icon size={24} className="text-secondary-text" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-primary-text mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-secondary-text max-w-xs">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
