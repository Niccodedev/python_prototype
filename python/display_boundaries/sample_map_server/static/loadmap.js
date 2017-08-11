"use strict";

var dataUrl = "../get-data";

var map;
var info;
var geojsonLayer;
var currLayer;

var table_name = "";
var minZoom = 4;
var maxZoom = 16;
var currentZoomLevel = 0;

// used for random colour generation
var currMapMin = 0;
var currMapMax = 255;

var highlightColour = "#ffff00";
var colourRamp;
var colourRange = ["#1f1f1f", "#e45427"]; // dark grey > orange/red

// get querystring values
// code from http://forum.jquery.com/topic/getting-value-from-a-querystring
// get querystring as an array split on "&"
var querystring = location.search.replace("?", "").split("&");

// declare object
var queryObj = {};

// loop through each name-value pair and populate object
var i;
for (i = 0; i < querystring.length; i+=1) {
    // get name and value
    queryObj[querystring[i].split("=")[0]] = querystring[i].split("=")[1];
}

// get/set table name from querystring
if (queryObj.t) {
//   table_name = "locality_bdys";
//} else {
    table_name = queryObj.t.toString();
}

// start zoom level
if (!queryObj.z) {
    currentZoomLevel = 14;
} else {
    currentZoomLevel = queryObj.z;
}


function init() {
    // create colour ramp
    colourRamp = new Rainbow();
    colourRamp.setSpectrum(colourRange[0], colourRange[1]);
    colourRamp.setNumberRange(0, 255);

    //Initialize the map on the "map" div - only use canvas if supported (can be slow on Safari)
    var elem = document.createElement("canvas");
    if (elem.getContext && elem.getContext("2d")) {
        map = new L.Map("map", {preferCanvas: true});
    } else {
        map = new L.Map("map", {preferCanvas: false});
    }

    // acknowledge the data provider
    map.attributionControl.addAttribution("Census data &copy; <a href='http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material'>ABS</a>");

    // create non-interactive pane (i.e. no mouse events) for basemap tiles
    map.createPane("basemap");
    map.getPane("basemap").style.zIndex = 650;
    map.getPane("basemap").style.pointerEvents = "none";

    // load CartoDB basemap in the foreground with no mouse events
    L.tileLayer("http://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", {
        attribution: "&copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='http://cartodb.com/attributions'>CartoDB</a>",
        subdomains: "abcd",
        minZoom: minZoom,
        maxZoom: maxZoom,
        pane: "basemap",
        opacity: 0.4
    }).addTo(map);

    // set the view to a given center and zoom
    map.setView(new L.LatLng(-33.85, 151.15), currentZoomLevel);

    // get bookmarks
    var bmStorage = {
        getAllItems: function (callback) {
            $.getJSON("bookmarks.json",
                function (json) {
                    callback(json);
                });
        }
    };

    // add bookmark control to map
    var bm = new L.Control.Bookmarks({
        position: "topleft",
        localStorage: false,
        storage: bmStorage
    }).addTo(map);

    // add control that shows info on mouseover
    info = L.control();
    info.onAdd = function () {
        this._div = L.DomUtil.create("div", "info");
        L.DomEvent.disableScrollPropagation(this._div);
        L.DomEvent.disableClickPropagation(this._div);
        this.update();
        return this._div;
    };
    info.update = function (props) {
        var infoStr = "";

        if (props) {
            infoStr = "<span style='font-weight: bold; font-size:1.5em'>" + props.name + "&nbsp;" + props.state + "</span><br/>";
        } else {
            infoStr = "pick a boundary";
        }

        this._div.innerHTML = infoStr;
    };
    info.addTo(map);

    // get a new set of data when map panned or zoomed
    map.on("moveend", function () {
        getData();
    });

    // get the first lot of data
    getData();
}

function getData() {

    console.time("got boundaries");

    // get new zoom level and boundary
    currentZoomLevel = map.getZoom();

    //restrict to the zoom levels that have data
    if (currentZoomLevel < minZoom) {
        currentZoomLevel = minZoom;
    }
    if (currentZoomLevel > maxZoom) {
        currentZoomLevel = maxZoom;
    }

    // get map extents
    var bb = map.getBounds();
    var sw = bb.getSouthWest();
    var ne = bb.getNorthEast();

    // build URL
    var ua = [];
    ua.push(dataUrl);
    ua.push("?ml=");
    ua.push(sw.lng.toString());
    ua.push("&mb=");
    ua.push(sw.lat.toString());
    ua.push("&mr=");
    ua.push(ne.lng.toString());
    ua.push("&mt=");
    ua.push(ne.lat.toString());
    if (table_name) {
        ua.push("&t=");
        ua.push(table_name);
    }
    ua.push("&z=");
    ua.push((currentZoomLevel).toString());

    var requestString = ua.join("");

//    console.log(requestString);

    //Fire off AJAX request
    $.getJSON(requestString, gotData);
}

function gotData(json) {
    console.timeEnd("got boundaries");
    console.time("parsed GeoJSON");

    if (json !== null) {
        if(geojsonLayer !== undefined) {
            geojsonLayer.clearLayers();
        }

        // add data to map layer
        geojsonLayer = L.geoJson(json, {
            style : style,
            onEachFeature : onEachFeature
        }).addTo(map);
    } else {
        alert("No data returned!")
    }

    console.timeEnd("parsed GeoJSON");
}

function style(feature) {
    // colour bdys randomly
    var renderVal = parseInt(Math.random() * 255.0);
    var col = getColor(renderVal);

    return {
        weight : 2,
        opacity : 1.0,
        color : col,
        fillOpacity : 1.0,
        fillColor : col
    };
}

// get color depending on ratio of count versus max value
function getColor(val) {
    var colour = "#" + colourRamp.colourAt(val);
    return colour;
}

function onEachFeature(feature, layer) {
    layer.on({
        click : highlightFeature,
        mouseover : highlightFeature,
        mouseout : resetHighlight
    });
}

function highlightFeature(e) {
    if (currLayer !== undefined) {
        geojsonLayer.resetStyle(currLayer);
    }

    currLayer = e.target;

    if (currLayer !== undefined) {

        currLayer.setStyle({
            weight: 2.5,
            opacity: 0.8,
            color: highlightColour
        });

        //    if (!L.Browser.ie && !L.Browser.edge && !L.Browser.opera) {
        currLayer.bringToFront();
        //    }

        info.update(currLayer.feature.properties);
    }
}

function resetHighlight(e) {
    geojsonLayer.resetStyle(e.target);
    info.update();
}

// function zoomToFeature(e) {
//    map.fitBounds(e.target.getBounds());
// }
