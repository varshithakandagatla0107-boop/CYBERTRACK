// Shared API helpers. The authenticated fetch wrapper lives in
// AuthContext (api function). This module holds formatting utils.

export const formatINR = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—'
  }
  return '₹' + Number(value).toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })
}

export const formatDateTime = (iso) => {
  if (!iso) return '—'
  const d = new Date(iso.replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const maskAccount = (id) => {
  if (!id) return ''
  if (id.length <= 3) return id
  return 'X'.repeat(id.length - 3) + id.slice(-3)
}
