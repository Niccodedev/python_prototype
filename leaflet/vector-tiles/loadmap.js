
//cd minus34/GitHub/prototypes/leaflet/vector-tiles/

var map;
var pbfLayer;
var minZoom = 8;
var maxZoom = 14;

var colours = ['#edf8fb','#ccece6','#99d8c9','#66c2a4','#41ae76','#238b45','#005824']; ``
//var themeGrades = [2, 4, 6, 8, 10, 12, 14]

function init(){
    map = L.map('mapid')

    var tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains: 'abcd',
        minZoom: minZoom,
        maxZoom: maxZoom
    }).addTo(map);

    var url = 'http://localhost:8080/geoserver/gwc/service/tms/1.0.0/loceng%3Alocality_bdys_display_web@EPSG%3A900913@pbf/{z}/{x}/{-y}.pbf';

    var vectorTileOptions = {
        rendererFactory: L.svg.tile,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://www.mapbox.com/about/maps/">MapBox</a>',
        vectorTileLayerStyles: {
            locality_bdys_display_web: function(properties, zoom) {
                return defaultStyle(properties.address_count);
            }
        },
        interactive: true,	// Make sure that this VectorGrid fires mouse/pointer events
        getFeatureId: function(f) { // Required because polygons span different tiles
            return f.properties.gid;
        }
    };

    pbfLayer = L.vectorGrid.protobuf(url, vectorTileOptions)
        .on('click', function(e) {	// The .on method attaches an event handler
            L.popup()
                .setContent(e.layer.properties.gid + ' - ' + e.layer.properties.locality_name + ', ' + e.layer.properties.state + ' ' + e.layer.properties.postcode + '</br>' + e.layer.properties.address_count + ' addresses')
                .setLatLng(e.latlng)
                .openOn(map);

            L.DomEvent.stop(e);
        })
        .on('mouseover', function(e) {
            highlightFeature(e);
         	L.DomEvent.stop(e);
        })
        .on('mouseout', function(e) {
            resetFeature(e);
         	L.DomEvent.stop(e);
        })        .addTo(map);

    map.setView([-33.85, 151.0], 12);
}

function defaultStyle(renderVal) {

    return {
        weight: 1,
        opacity: 0.2,
        color: '#666',
        fillOpacity: 0.7,
        fillColor: getColor(renderVal),
        fill: true
    };
}

 // get color depending on ratio of count versus max value
 function getColor(d) {
   var col = d > 10000 ? colours[6]:
          d > 5000 ? colours[5]:
          d > 4000 ? colours[4]:
          d > 3000 ? colours[3]:
          d > 2000 ? colours[2]:
          d > 1000 ? colours[1]:
                     colours[0];

   return col;

 }

function highlightFeature(e) {
    var id = e.layer.properties.gid;
    var renderVal = e.layer.properties.address_count;

    highlightStyle = {
        weight: 3,
        opacity: 0.9,
        color: '#444',
        fillOpacity: 0.7,
        fillColor: getColor(renderVal),
        fill: true
    };

    pbfLayer.setFeatureStyle(id, highlightStyle);

//    if (!L.Browser.ie && !L.Browser.opera) {
//        e.layer.bringToFront();
//    }

    //info.update(layer.feature.properties);
}

function resetFeature(e) {
    var id = e.layer.properties.gid;

    pbfLayer.resetFeatureStyle(id);
}