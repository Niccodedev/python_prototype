var restUrl = "../get-data";
var map = null;
var info = null;
var geojsonLayer = null;
var maxZoom = 4;
var minZoom = 15;
var valueType = "percent";
var zoomLevel = 10


var colours = []

function init() {
	//Initialize the map on the "map" div
	map = new L.Map('map');

	// load CartoDB basemap tiles
	var tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
			attribution : '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
			subdomains : 'abcd',
			minZoom : 4,
			maxZoom : 15
		}).addTo(map);

	//Set the view to a given center and zoom
	map.setView(new L.LatLng(-37.81, 144.96), zoomLevel);

	// Get bookmarks/
	var storage = {
		getAllItems : function (callback) {
			$.getJSON('bookmarks.json',
				function (json) {
				callback(json);
			});
		}
	};

	//Add bookmark control
	var bmControl = new L.Control.Bookmarks({
			position : 'topleft',
			localStorage : false,
			storage : storage
		}).addTo(map);

	//Acknowledge the PSMA Data
	map.attributionControl.addAttribution('Address info derived from <a href="http://data.gov.au/dataset/geocoded-national-address-file-g-naf">PSMA G-NAF</a>');

	// control that shows hex info on hover
	info = L.control();

	info.onAdd = function (map) {
		this._div = L.DomUtil.create('div', 'info');
		this.update();
		return this._div;
	};

	info.update = function (props) {
		switch (valueType) {
		case "percent":
			this._div.innerHTML = (props ? '<b>' + props.percent.toLocaleString(['en-AU']) + '%</b> increase' : 'pick a hex');
			break;
		case "difference":
			this._div.innerHTML = (props ? '<b>' + props.difference.toLocaleString(['en-AU']) + '</b> new addresses' : 'pick a hex');
			break;
		default:
			this._div.innerHTML = (props ? '<b>' + props.percent.toLocaleString(['en-AU']) + '%</b> increase' : 'pick a hex');
        }
    };

    info.addTo(map);

    //Add radio buttons to choose map theme
    var themer = L.control({
            position : 'bottomright'
        });
    themer.onAdd = function (map) {
        var div = L.DomUtil.create('div', 'info themer');
        div.innerHTML = '<h4>Address<br/>increase</h4>' +
            '<div><input id="radio1" type="radio" name="radio" value="percent" checked="checked"><label for="radio1"><span><span></span></span>Percent</label></div>' +
            '<div><input id="radio2" type="radio" name="radio" value="difference"><label for="radio2"><span><span></span></span>Volume</label></div>'
            return div;
    };

    themer.addTo(map);

    $("input:radio[name=radio]").click(function () {
        valueType = $(this).val();
        //Reload the boundaries
        getBoundaries();
    });

    //Get a new set of boundaries when map panned or zoomed
    //TO DO: Handle map movement due to popup
    map.on('moveend', function (e) {
        getBoundaries();
    });

    map.on('zoomend', function (e) {
        map.closePopup();
        //getBoundaries();
    });

    //Get the first set of boundaries
    getBoundaries();
}

	function style(feature) {

		var renderVal;

		switch (valueType) {
		case "percent":
			colours = ['#fee5d9','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#99000d']
			renderVal = parseInt(feature.properties.percent);
			break;
		case "difference":
			colours = ['#feedde','#fdd0a2','#fdae6b','#fd8d3c','#f16913','#d94801','#8c2d04']
			renderVal = parseInt(feature.properties.difference);
			break;
		default:
			colours = ['#fee5d9','#fcbba1','#fc9272','#fb6a4a','#ef3b2c','#cb181d','#99000d']
			renderVal = parseInt(feature.properties.percent);
		}

		return {
			weight : 0,
			opacity : 0.0,
			color : '#666',
			fillOpacity : getOpacity(renderVal),
			fillColor : getColor(renderVal)
		};
	}

	// get color depending on ratio of count versus max value
	function getColor(d) {

		switch (valueType) {
		case "percent":
			return d > 500 ? colours[6] :
			d > 200 ? colours[5] :
			d > 100 ? colours[4] :
			d > 50 ? colours[3] :
			d > 25 ? colours[2] :
			d > 0 ? colours[1] :
			        colours[0];
			break;
		case "difference":
		    zoomDiff = 11 - zoomLevel;
		    if (zoomDiff > 0) {
                d = d / Math.pow(4, zoomDiff)
		    }

			return d > 500 ? colours[6] :
			d > 200 ? colours[5] :
			d > 100 ? colours[4] :
			d > 50 ? colours[3] :
			d > 25 ? colours[2] :
			d > 0 ? colours[1] :
			        colours[0];
			break;
		default:
			return d > 500 ? colours[6] :
			d > 200 ? colours[5] :
			d > 100 ? colours[4] :
			d > 50 ? colours[3] :
			d > 25 ? colours[2] :
			d > 0 ? colours[1] :
			        colours[0];
		}
	}

	// get color depending on ratio of count versus max value
	function getOpacity(d) {

		switch (valueType) {
		case "percent":
			return d > 500 ? 0.7 :
			d > 200 ? 0.6 :
			d > 100 ? 0.5 :
			d > 50 ? 0.4 :
			d > 25 ? 0.3 :
			d > 0 ? 0.2 :
			        0.1;
			break;
		case "difference":
		    zoomDiff = 11 - zoomLevel;
		    if (zoomDiff > 0) {
                d = d / Math.pow(4, zoomDiff)
		    }

			return d > 500 ? 0.7 :
			d > 200 ? 0.6 :
			d > 100 ? 0.5 :
			d > 50 ? 0.4 :
			d > 25 ? 0.3 :
			d > 0 ? 0.2 :
			        0.1;
			break;
		default:
			return d > 500 ? 0.7 :
			d > 200 ? 0.6 :
			d > 100 ? 0.5 :
			d > 50 ? 0.4 :
			d > 25 ? 0.3 :
			d > 0 ? 0.2 :
			        0.1;
		}
	}


	function highlightFeature(e) {

		var layer = e.target;

		layer.setStyle({
			weight : 2,
			opacity : 0.9,
			fillOpacity : 0.7
		});

		if (!L.Browser.ie && !L.Browser.opera) {
			layer.bringToFront();
		}

		info.update(layer.feature.properties);
	}

	function resetHighlight(e) {
		geojsonLayer.resetStyle(e.target);
		info.update();
	}

	function zoomToFeature(e) {
		map.fitBounds(e.target.getBounds());
	}

	function onEachFeature(feature, layer) {
		layer.on({
			mouseover : highlightFeature,
			mouseout : resetHighlight
		});
	}

	function getBoundaries() {

		console.time("got boundaries");

		//Get zoom level
		zoomLevel = map.getZoom();
		//    console.log("Zoom level = " + zoomLevel.toString());

		//restrict to the zoom levels that have data
		if (zoomLevel < maxZoom)
			zoomLevel = maxZoom;
		if (zoomLevel > minZoom)
			zoomLevel = minZoom;

		//Get map extents
		var bb = map.getBounds();
		var sw = bb.getSouthWest();
		var ne = bb.getNorthEast();

		//Build URL with querystring - selects census bdy attributes, stats and the census boundary geometries as minimised GeoJSON objects
//		var ua = [];
//		ua.push(restUrl);
//		ua.push("?ml=");
//		ua.push(sw.lng.toString());
//		ua.push("&mb=");
//		ua.push(sw.lat.toString());
//		ua.push("&mr=");
//		ua.push(ne.lng.toString());
//		ua.push("&mt=");
//		ua.push(ne.lat.toString());
//		ua.push("&z=");
//		ua.push((zoomLevel).toString());
		var ua = [];
		ua.push(restUrl);
		ua.push("/");
		ua.push(sw.lng.toString());
		ua.push("/");
		ua.push(sw.lat.toString());
		ua.push("/");
		ua.push(ne.lng.toString());
		ua.push("/");
		ua.push(ne.lat.toString());
		ua.push("/");
		ua.push((zoomLevel).toString());
		ua.push("/");
        //    ua.push("&t=");
        //    ua.push(valueType);

		var reqStr = ua.join('');

		//Fire off AJAX request
		$.getJSON(reqStr, loadBdysNew);
	}

	function loadBdysNew(json) {

		console.timeEnd("got boundaries");
		console.time("parsed GeoJSON");

		if (json != null) {
			try {
				geojsonLayer.clearLayers();
			} catch (err) {
				//dummy
			}

			// TO FIX: ERRORS NOT BEING TRAPPED
			// try {
				geojsonLayer = L.geoJson(json, {
						style : style,
						onEachFeature : onEachFeature
					}).addTo(map);
			// } catch (err) {
			// 	alert("Couldn't get data!");
			// }
		}

		console.timeEnd("parsed GeoJSON");
	}
