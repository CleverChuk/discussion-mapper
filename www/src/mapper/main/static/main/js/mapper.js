
$(function(){
    // This code uses version 3 of d3js
// Set margins and sizes
var margin = {
    top: 20,
    bottom: 50,
    right: 30,
    left: 50
}

var width = 960 - margin.left - margin.right
var height = 550 - margin.top - margin.bottom


//Load Color Scale
var c10 = d3.scale.category10()
var sentimentColor  = {"Positive":"#3AE71E", "Negative":"red","Neutral":"blue"}

//Create an SVG element and append it to the DOM
var svg = d3.select(".graph")
    .append("svg")
    .classed("svg-content-responsive", true)
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 " + (height + margin.top + margin.bottom) + " " + (width + margin.left + margin.right))
    .call(d3.behavior.zoom().on("zoom", function () {
        svg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")
    }))
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")

var mSvg = d3.select(".mgraph")
    .append("svg")
    .classed("svg-content-responsive", true)
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 " + (height + margin.top + margin.bottom) + " " + (width + margin.left + margin.right))
    .call(d3.behavior.zoom().on("zoom", function () {
        mSvg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")
    }))
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")")


// Functions
function render(graph, canvas) {
    radiusFunc = node => {
      return 25//node.score / 5 > 10 ? node.score / 5 : 20
    }

    //Extract data from graph
    let nodes = graph.nodes,
      links = graph.links

    //Create Force Layout
    var force = d3.layout.force()
      .size([width, height])
      .nodes(nodes)
      .links(links)
      .gravity(0.05)
      .charge(-200)
      .linkDistance(200)

    //Add links to SVG
    var link = canvas.selectAll(".link")
      .data(links)

    link.enter().append("line")
      .attr("stroke-width", "2")
      .attr("stroke","#ccc")
      .attr("class", "link")
    link.exit().remove()
    

    //Add nodes to SVG
    var node = canvas.selectAll(".node")
      .data(nodes)
    node.enter().append("g")
      .attr("class", "node")
      .call(force.drag)

    //Add circles to each node
    node.append("circle")
      .attr("r", radiusFunc)
      .attr("fill", d =>{
          if(d.type == "sentiment") return sentimentColor[d.name]
          else if(d.type == "author") return "#f79489"
          else if(d.type == "comment") return "brown"
          else return "cyan"
      })

    node.append("title")
    .text(d =>{
      if(d.type == "comment") return d.body
      else return ""
    })
      node.append('text')
        .attr("text-anchor","middle")
        .attr("pointer-events","none")
        .text(d => getNodeText(d))

    node.exit().remove()




    //This function will be executed once force layout is done with its calculations
    force.on("tick", function () {
      //Set X and Y of node
      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y)
        //Shift node a little
        .attr("transform", d => "translate(" + d.x + "," + d.y + ")")

      //Set X, Y of link
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y)

    })
    //Start the force layout calculation
    force.start()
  }


function addPropertyControl(nodes) {
    let properties = null
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].type == "comment") {
        properties = Object.getOwnPropertyNames(nodes[i])
        break;
      }
    }
    var dropDownMenu = document.getElementsByClassName("dropdown-menu")[0];

    properties.forEach(prop => {
      var checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.className = "prop-control"

      var label = document.createElement("a");
      label.className = "dropdown-item"
      label.href = "#"
      label.innerHTML = prop;
      label.style.marginLeft = "10px"
      label.style.marginRight = "10px"


      var group = document.createElement("div")
      group.className = "dropdown-item"
      group.appendChild(checkbox)
      group.appendChild(label)

      dropDownMenu.appendChild(label)
    })
}

function getNodeText(node){
    if(node.type == "author") return node["name"]
    else if(node.type == "sentiment") return node["name"]
    else return node.type
}

loadGraph()
function loadGraph(){
    $.ajax(
        {
            url:'api/',
            type : 'GET',
            success : function(json){  
                var data = JSON.parse(json.graph)
                addPropertyControl(data.nodes)
                render(data, svg)
            },
            error : function(xhr, errormsg, erro){}
        }
    );
}
})
