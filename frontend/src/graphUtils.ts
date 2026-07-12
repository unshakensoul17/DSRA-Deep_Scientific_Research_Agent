export const calculateCircularLayout = (nodes: any[], edges: any[], width = 600, height = 400) => {
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;

  const positionedNodes = nodes.map((node, i) => {
    const angle = (i / (nodes.length || 1)) * 2 * Math.PI;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle)
    };
  });

  const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));

  const positionedEdges = edges.map(edge => {
    const source = nodeMap.get(edge.source);
    const target = nodeMap.get(edge.target);
    return {
      ...edge,
      x1: source ? source.x : centerX,
      y1: source ? source.y : centerY,
      x2: target ? target.x : centerX,
      y2: target ? target.y : centerY
    };
  });

  return { nodes: positionedNodes, edges: positionedEdges };
};
