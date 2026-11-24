/**
 * DataTable — compact professional table.
 * columns: [{key, label, className, render}]
 */
export default function DataTable({
  columns = [],
  rows = [],
  onRowClick,
  emptyMessage = 'No records found.',
}) {
  if (!rows.length) {
    return (
      <div className="table-wrap">
        <div className="state-box" style={{ padding: 32 }}>
          <div className="desc">{emptyMessage}</div>
        </div>
      </div>
    )
  }
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} className={col.className || ''}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.id ?? i}
              className={onRowClick ? 'clickable' : ''}
              onClick={
                onRowClick ? () => onRowClick(row) : undefined
              }
            >
              {columns.map((col) => (
                <td key={col.key} className={col.className || ''}>
                  {col.render
                    ? col.render(row[col.key], row)
                    : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
