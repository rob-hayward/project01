function drawPieChart(data, elementId) {
  const width = 618.7;
  const height = Math.min(width, 333.3);

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
    .style("fill", "white")  // Make the text color white
    .style("font-weight", "bold")  // Make the text bold
    .style("font-size", "2em") // Increase the font size
    .call(text => text.append("tspan")
        .attr("y", "-0.0em")
        .text(d => `${d.data.name} Votes: ${d.data.value.toLocaleString("en-US")}`)) // Combine label and votes
    .call(text => text.append("tspan")
        .attr("x", 0)
        .attr("y", "0.8em")
        .attr("fill-opacity", 0.7)
        .text(d => `${d.data.percentage}%`));


  // Insert the SVG into your HTML
  document.getElementById(elementId).appendChild(svg.node());
}

function updatePieChart(approveVotes, rejectVotes, approvePercentage, rejectPercentage, elementId) {
  const data = [
    { name: 'Approve', value: approveVotes, percentage: approvePercentage },
    { name: 'Reject', value: rejectVotes, percentage: rejectPercentage }
  ];

  data.sort((a, b) => a.name.localeCompare(b.name));

  // Clear the existing chart
  document.getElementById(elementId).innerHTML = '';

  // Draw the new chart
  drawPieChart(data, elementId);
}

export { drawPieChart, updatePieChart };
