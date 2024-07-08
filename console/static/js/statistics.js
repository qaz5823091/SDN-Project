const CONF = {
    host: "http://api.sdn.com",
    svg_style: "border-2 border-gray-200 border-dashed rounded-lg dark:border-gray-700 mt-10 p-4",
    svg_color: "LightSeaGreen"
}

const width = 928
const height = 500
const marginTop = 30
const marginRight = 30
const marginBottom = 50
const marginLeft = 60

var data
var switches
var ports = []

async function getData() {
    switches = await d3.json(CONF.host + '/stats/switches')
    for (var item in switches) {
        ports = await d3.json(CONF.host + '/stats/port/' + switches[0])
    }

    data = ports['1']
    console.log(data)
}

function drawBarChart(target_x, target_y) {
    // x-axis setting
    const x = d3
        .scaleBand()
        .domain(data.map((d) => d[target_x]))
        .range([marginLeft, width - marginRight])
        .padding(0.1);

    // y-axis setting
    const y = d3
        .scaleLinear()
        .domain([0, d3.max(data, (d) => d[target_y])])
        .nice()
        .range([height - marginBottom, marginTop]);

    // svg container
    const svg = d3
        .create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [0, 0, width, height])
        .attr("style", "max-width: 100%; height: auto;")
        .attr("class", CONF.svg_style)

    // rect
    svg.append("g")
        .attr("fill", "steelblue")
        .selectAll()
        .data(data)
        .join("rect")
        .attr("x", (d) => x(d[target_x]))
        .attr("y", (d) => y(d[target_y]))
        .attr("width", x.bandwidth())
        .attr("height", (d) => y(0) - y(d[target_y]))

    // x-axis attribute
    svg.append("g")
        .attr("transform", `translate(0,${height - marginBottom})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("transform", "rotate(-45)");

    // y-axis attribute
    svg.append("g")
        .attr("transform", `translate(${marginLeft},0)`)
        .call(d3.axisLeft(y));

    // y-axis label
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", marginLeft - 40)
        .attr("x", 0 - height / 2)
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text(target_y);

    const node = svg.node()
    const viewer = document.getElementById("statistics-viewer")
    const container = document.createElement("div")
    const title = document.createElement("h2")

    container.className = "p-4"
    title.textContent = target_y;
    title.className = "text-2xl"

    container.appendChild(title)
    container.appendChild(node)
    viewer.appendChild(container)
}

function drawPieChart() {
    var data =  [
        {name: "<5", value: 19912018},
        {name: "5-9", value: 20501982},
        {name: "10-14", value: 20679786},
        {name: "15-19", value: 21354481},
        {name: "20-24", value: 22604232},
        {name: "25-29", value: 21698010},
        {name: "30-34", value: 21183639},
        {name: "35-39", value: 19855782},
        {name: "40-44", value: 20796128},
        {name: "45-49", value: 21370368},
        {name: "50-54", value: 22525490},
        {name: "55-59", value: 21001947},
        {name: "60-64", value: 18415681},
        {name: "65-69", value: 14547446},
        {name: "70-74", value: 10587721},
        {name: "75-79", value: 7730129},
        {name: "80-84", value: 5811429},
        {name: "≥85", value: 5938752}
    ]

    const width = 928;
    const height = Math.min(width, 500);

    // Create the color scale.
    const color = d3.scaleOrdinal()
        .domain(data.map(d => d.name))
        .range(d3.quantize(t => d3.interpolateSpectral(t * 0.8 + 0.1), data.length).reverse())

    // Create the pie layout and arc generator.
    const pie = d3.pie()
        .sort(null)
        .value(d => d.value);

    const arc = d3.arc()
        .innerRadius(0)
        .outerRadius(Math.min(width, height) / 2 - 1);

    const labelRadius = arc.outerRadius()() * 0.8;

    // A separate arc generator for labels.
    const arcLabel = d3.arc()
        .innerRadius(labelRadius)
        .outerRadius(labelRadius);

    const arcs = pie(data);

    // Create the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

    // Add a sector path for each value.
    svg.append("g")
        .attr("stroke", "white")
        .selectAll()
        .data(arcs)
        .join("path")
        .attr("fill", d => color(d.data.name))
        .attr("d", arc)
        .append("title")
        .text(d => `${d.data.name}: ${d.data.value.toLocaleString("en-US")}`);

    // Create a new arc generator to place a label close to the edge.
    // The label shows the value if there is enough room.
    svg.append("g")
        .attr("text-anchor", "middle")
        .selectAll()
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

    d3.select("#statistics-viewer").append(() => svg.node())
}

async function main() {
    await getData();

    
    drawBarChart('port_no', 'rx_packets')
    drawBarChart('port_no', 'tx_packets')
    drawBarChart('port_no', 'rx_bytes')
    drawBarChart('port_no', 'tx_bytes')
    //drawPieChart()
}


main();
