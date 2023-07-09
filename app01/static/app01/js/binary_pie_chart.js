function drawPieChart(data, elementId) {
  const width = 464;
  const height = Math.min(width, 250);

  const color = d3.scaleOrdinal()
      .domain(data.map(d => d.name))
      .range(["#00DFA2", "#FF0060"]);

  const pie = d3.pie()
      .sort(null)
      .value(d => d.value);

  const arc = d3.arc()
      .innerRadius(0)
      .outerRadius(Math.min(width, height) / 2 - 1);

  const labelRadius = arc.outerRadius()() * 0.8;

  const arcLabel = d3.arc()
      .innerRadius(labelRadius)
      .outerRadius(labelRadius);

  const arcs = pie(data);

  const svg = d3.create("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [-width / 2, -height / 2, width, height])
      .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

  svg.append("g")
      .attr("stroke", "white")
    .selectAll("path")
    .data(arcs)
    .join("path")
      .attr("fill", d => color(d.data.name))
      .attr("d", arc)
    .append("title")
      .text(d => `${d.data.name}: ${d.data.value.toLocaleString("en-US")}`);

  svg.append("g")
      .attr("text-anchor", "middle")
    .selectAll("text")
    .data(arcs)
    .join("text")
      .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
      .call(text => text.append("tspan")
          .attr("y", "-0.4em")
          .attr("font-weight", "bold")
          .text(d => d.data.name))
      .call(text => text.filter(d => (d.endAngle - d.startAngle) > 0.25).append("tspan")
          .attr("x", 0)
          .attr("y", "0.7em")
          .attr("fill-opacity", 0.7)
          .text(d => d.data.value.toLocaleString("en-US")));

  // Insert the SVG into your HTML
  document.getElementById(elementId).appendChild(svg.node());
}

// Call this function whenever the AJAX request successfully updates the vote data
function updatePieChart(approveVotes, rejectVotes, elementId) {
  const data = [
    { name: 'Approve', value: approveVotes },
    { name: 'Reject', value: rejectVotes }
  ];

  // Clear the existing chart
  document.getElementById(elementId).innerHTML = '';

  // Draw the new chart
  drawPieChart(data, elementId);
}

export { drawPieChart, updatePieChart };
