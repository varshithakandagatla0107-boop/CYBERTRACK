import { useEffect, useRef } from 'react'
import cytoscape from 'cytoscape'

const COLORS = {
  high: '#dc2626',
  medium: '#d97706',
  low: '#94a3b8',
  selected: '#2563eb',
  path: '#2563eb',
}

/**
 * NetworkGraph — Cytoscape.js visualisation.
 * Props:
 *   nodes: [{id, label, risk_score, risk_category, ...}]
 *   edges: [{source, target, weight, count, suspicious}]
 *   selectedId: centre account
 *   highlightPath: array of account ids
 *   onNodeClick(accountId)
 *   height
 */
export default function NetworkGraph({
  nodes = [],
  edges = [],
  selectedId,
  highlightPath = [],
  onNodeClick,
  height = 520,
}) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return
    if (cyRef.current) {
      cyRef.current.destroy()
      cyRef.current = null
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: buildElements(nodes, edges, selectedId, highlightPath),
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'font-size': 9,
            'color': '#334155',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': 1.5,
            'border-color': '#ffffff',
            'text-outline-color': '#fbfcfe',
            'text-outline-width': 2,
          },
        },
        {
          selector: 'node[?isCentre]',
          style: {
            'border-width': 3,
            'border-color': COLORS.selected,
            'font-size': 11,
            'font-weight': 'bold',
          },
        },
        {
          selector: 'node[?inPath]',
          style: {
            'border-width': 3,
            'border-color': COLORS.path,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': '#b6c2d1',
            'target-arrow-color': '#b6c2d1',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.8,
            'curve-style': 'bezier',
            'opacity': 0.75,
          },
        },
        {
          selector: 'edge[?suspicious]',
          style: {
            'line-color': '#ef4444',
            'target-arrow-color': '#ef4444',
            'width': 'data(width)',
            'opacity': 0.9,
          },
        },
        {
          selector: 'edge[?inPath]',
          style: {
            'line-color': COLORS.path,
            'target-arrow-color': COLORS.path,
            'width': 4,
            'opacity': 1,
            'z-index': 10,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        nodeRepulsion: 9000,
        idealEdgeLength: 90,
        gravity: 0.3,
        padding: 30,
      },
      wheelSensitivity: 0.2,
      minZoom: 0.2,
      maxZoom: 3,
    })

    cy.on('tap', 'node', (evt) => {
      const id = evt.target.id()
      if (onNodeClick) onNodeClick(id)
    })

    cyRef.current = cy
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy()
        cyRef.current = null
      }
    }
  }, [nodes, edges, selectedId, highlightPath])

  const fit = () => cyRef.current?.fit(undefined, 30)
  const zoomIn = () => cyRef.current?.zoom({
    level: cyRef.current.zoom() * 1.3,
    renderedPosition: { x: 0, y: 0 },
  })
  const zoomOut = () => cyRef.current?.zoom({
    level: cyRef.current.zoom() / 1.3,
    renderedPosition: { x: 0, y: 0 },
  })

  return (
    <div
      className="graph-container"
      style={{ height }}
      ref={containerRef}
    >
      <div className="graph-toolbar">
        <button className="btn btn-sm" onClick={fit}>Reset view</button>
        <button className="btn btn-sm" onClick={zoomIn}>Zoom +</button>
        <button className="btn btn-sm" onClick={zoomOut}>Zoom −</button>
      </div>
      <div className="graph-legend">
        <div className="legend-item">
          <span className="legend-dot" style={{ background: COLORS.high }} />
          High risk
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: COLORS.medium }} />
          Medium risk
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: COLORS.low }} />
          Normal
        </div>
        <div className="legend-item">
          <span className="legend-dot" style={{ background: COLORS.selected }} />
          Selected / path
        </div>
      </div>
    </div>
  )
}

function buildElements(nodes, edges, selectedId, highlightPath) {
  const maxWeight = Math.max(
    1, ...edges.map((e) => e.weight || 1)
  )
  const pathSet = new Set(highlightPath)

  const cyNodes = nodes.map((n) => {
    const cat = n.risk_category || 'low'
    let color = COLORS.low
    if (cat === 'high') color = COLORS.high
    else if (cat === 'medium') color = COLORS.medium
    const degree = n.degree || 1
    const size = 14 + Math.min(degree * 1.6, 22)
    return {
      data: {
        id: n.id,
        label: n.label || n.id,
        color,
        size,
        risk: n.risk_score || 0,
        isCentre: n.id === selectedId,
        inPath: pathSet.has(n.id),
      },
    }
  })

  const pathEdges = new Set()
  if (highlightPath.length > 1) {
    for (let i = 0; i < highlightPath.length - 1; i++) {
      pathEdges.add(`${highlightPath[i]}->${highlightPath[i + 1]}`)
    }
  }

  const cyEdges = edges.map((e, i) => {
    const width = 1 + 3.5 * Math.sqrt((e.weight || 1) / maxWeight)
    const key = `${e.source}->${e.target}`
    return {
      data: {
        id: `e${i}-${key}`,
        source: e.source,
        target: e.target,
        width,
        weight: e.weight,
        count: e.count,
        suspicious: !!e.suspicious && !pathEdges.has(key),
        inPath: pathEdges.has(key),
      },
    }
  })

  return [...cyNodes, ...cyEdges]
}
