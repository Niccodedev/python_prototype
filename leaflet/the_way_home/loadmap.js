"use strict";

var map;

function init(){
    map = L.map('mapdiv');

    var light_tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains: 'abcd'
//        className: 'lightTiles'
    }).addTo(map);


    var dark_tiles = L.tileLayer('http://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="http://cartodb.com/attributions">CartoDB</a>',
        subdomains: 'abcd'
//        className: 'darkTiles',
//        clip-path='url(#clip)'
    }).addTo(map);

//    var x = document.getElementsByClassName("example");


    $('svg').on('mousemove',function(e){
        $('.a').attr('cx',e.pageX).attr('cy',e.pageY)
    });

    map.setView([-33.85, 151.0], 12);

    var images = document.getElementsByTagName("img");

    for (var i = 0; i < images.length; i++) {
        if (images[i].src.indexOf('/light_all/') > 0) {
            images[i].className += ' tile-light';
//            console.log(images[i].classList);
        }

        if (images[i].src.indexOf('/dark_all/') > 0) {
            images[i].className += ' tile-dark';
//            console.log(images[i].src);
        }

    }

//
//
//    console.log(list);
}
