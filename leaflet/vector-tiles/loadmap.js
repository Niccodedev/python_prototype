var map;

var colours = ['#edf8fb','#ccece6','#99d8c9','#66c2a4','#41ae76','#238b45','#005824']; ``
var themeGrades = [2, 4, 6, 8, 10, 12, 14]

function init(){
    map = L.map('mapid')

    var url = 'http://localhost:8080/geoserver/gwc/service/tms/1.0.0/loceng%3Alocality_bdys_display@EPSG%3A900913@pbf/{z}/{x}/{-y}.pbf';

    var vectorTileOptions = {
        rendererFactory: L.canvas.tile,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://www.mapbox.com/about/maps/">MapBox</a>',
        vectorTileLayerStyles: {
            locality_bdys_display: {
                weight: 1,
                color: '#666666',
                fillColor: '#66c2c4',
                fillOpacity: 1,
                fill: true,
                stroke: true
            }
        },
        interactive: true,	// Make sure that this VectorGrid fires mouse/pointer events
        getFeatureId: function(f) {
            return f.properties.gid;
        }
    };

    var pbfLayer = L.vectorGrid.protobuf(url, vectorTileOptions)
        .on('click', function(e) {	// The .on method attaches an event handler
            L.popup()
                .setContent(e.layer.properties.locality_name + ', ' + e.layer.properties.state + ' ' + e.layer.properties.postcode)
                .setLatLng(e.latlng)
                .openOn(map);

            console.log(e.l);

            L.DomEvent.stop(e);
        })
//         .on('mouseover', function(e) {	// The .on method attaches an event handler
//         	highlightFeature(e);
//
//         	L.DomEvent.stop(e);
//         })
        .addTo(map);

    map.setView([-33.85, 151.0], 12);
}

function style(feature) {
    var renderVal = parseInt(feature.properties.percent);

    return {
        weight: 1,
        opacity: 0.4,
        color: '#666',
        fillOpacity: 0.7,
        fillColor: getColor(renderVal)
    };
}

 // get color depending on ratio of count versus max value
 function getColor(d) {
   return d > 12 ? colours[6]:
          d > 10 ? colours[5]:
          d > 8 ? colours[4]:
          d > 6 ? colours[3]:
          d > 4 ? colours[2]:
          d > 2 ? colours[1]:
                  colours[0];
 }

function highlightFeature(e) {
    var layer = e.target;

    layer.setStyle({
        color: '#444',
        weight: 2,
        opacity: 0.9,
        fillOpacity: 0.7
    });

    if (!L.Browser.ie && !L.Browser.opera) {
        layer.bringToFront();
    }

//    info.update(layer.feature.properties);
}
