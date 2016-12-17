
function init(){
    var map = L.map('mapid')

    // var localities = L.tileLayer('http://localhost:8080/geoserver/gwc/service/tms/1.0.0/loceng%3Alocality_bdys_display@EPSG%3A900913@png/{z}/{x}/{-y}.png', {
    //     opacity: 0.4
    // }).addTo(map);

    //var url = 'https://{s}.tiles.mapbox.com/v4/mapbox.mapbox-streets-v6/{z}/{x}/{y}.vector.pbf?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpandmbXliNDBjZWd2M2x6bDk3c2ZtOTkifQ._QA7i5Mpkd_m30IGElHziw';
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

            L.DomEvent.stop(e);
        })
        // .on('mouseover', function(e) {	// The .on method attaches an event handler
        // 	elayer.options.fillcolor = '#990000'

        // 	L.DomEvent.stop(e);
        // })
        .addTo(map);

    //map.setView({ lat: 47.040182144806664, lng: 9.667968750000002 }, 0);
    map.setView([-33.85, 151.0], 12);
}