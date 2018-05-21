
var autocomplete = null;

function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: -33.8688, lng: 151.2195},
        zoom: 13
    });
    var card = document.getElementById('pac-card');
    var input = document.getElementById('pac-input');
    var types = document.getElementById('type-selector');
    var strictBounds = document.getElementById('strict-bounds-selector');

    map.controls[google.maps.ControlPosition.TOP_RIGHT].push(card);

    autocomplete = new google.maps.places.Autocomplete(input);

    // Bind the map's bounds (viewport) property to the autocomplete object,
    // so that the autocomplete requests use the current map bounds for the
    // bounds option in the request.
    autocomplete.bindTo('bounds', map);

    var infowindow = new google.maps.InfoWindow();
    var infowindowContent = document.getElementById('infowindow-content');
    infowindow.setContent(infowindowContent);
    var marker = new google.maps.Marker({
        map: map,
        anchorPoint: new google.maps.Point(0, -29)
    });

    autocomplete.addListener('place_changed', function() {
        infowindow.close();
        marker.setVisible(false);
        var place = autocomplete.getPlace();
        if (!place.geometry) {
            // User entered the name of a Place that was not suggested and
            // pressed the Enter key, or the Place Details request failed.
            window.alert("No details available for input: '" + place.name + "'");
            return;
        }

        // If the place has a geometry, then present it on a map.
        if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
        } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17);  // Why 17? Because it looks good.
        }
        marker.setPosition(place.geometry.location);
        marker.setVisible(true);

        var address = '';
        if (place.address_components) {
            address = [
                (place.address_components[0] && place.address_components[0].short_name || ''),
                (place.address_components[1] && place.address_components[1].short_name || ''),
                (place.address_components[2] && place.address_components[2].short_name || '')
            ].join(' ');
        }

        infowindowContent.children['place-icon'].src = place.icon;
        infowindowContent.children['place-name'].textContent = place.name;
        infowindowContent.children['place-address'].textContent = address;
        infowindow.open(map, marker);

        handleSearch()

    });

    // Sets a listener on a radio button to change the filter type on Places
    // Autocomplete.
    function setupClickListener(id, types) {
        var radioButton = document.getElementById(id);
        radioButton.addEventListener('click', function() {
            autocomplete.setTypes(types);
        });
    }

    setupClickListener('changetype-all', []);
    setupClickListener('changetype-address', ['address']);
    setupClickListener('changetype-establishment', ['establishment']);
    setupClickListener('changetype-geocode', ['geocode']);

    document.getElementById('use-strict-bounds')
        .addEventListener('click', function() {
            console.log('Checkbox clicked! New state=' + this.checked);
            autocomplete.setOptions({strictBounds: this.checked});
        });
}

function handleSearch() {

    place = autocomplete.getPlace();
    loc = place.geometry.location;

    console.log(loc.lat());
    console.log(loc.lng());

    var host = "http://127.0.0.1";
    var port = ":5000";
    var geocords_params = loc.lat().toString() + "/"  + loc.lng().toString();
    // get top restaurant type by location
    $.ajax({
        url: host + port + "/analytics/top_restaurant_types/"
            + geocords_params
        , type: "GET"
        , success: function(response){
            alert(
                "Fancy " + response[0][0] + "?\n"
                + "It's featured in " + response[0][1] + " restaurants in this area."
            );
            $.each(response, function(i, v){
                console.log(v)
            });
        }
        , error: function(error){
            console.log(error)
        }
    });

    url_string = "http://127.0.0.1:5000/restaurants/" +
        loc.lat().toString() + "/" +
        loc.lng().toString(); //+ "?" +
        //"radius=100";

    console.log(url_string);

    /*fetch(url_string)
        .then(function (response) {
            if (response.status !== 200) {
                console.log('Looks like there was a problem. Status Code: ' +
                    response.status);
                return;
            }

            // Examine the text in the response
            response.json().then(function(data) {
                populate_results(data)

            });
        })
    */

    // ONLY FOR DEBGUD, NOT CONNECTED TO API, UNCOMMENT ABOVE

    data = [
        {
            "name": "PETER",
            "data": [
                {
                    "name": "Google",
                    "rating": 4
                },
                {
                    "name": "Tripadvisor",
                    "rating": 5
                }
            ]


        },
        {
            "name": "FIshers",
            "data": [
                {
                    "name": "Google",
                    "rating": 4
                },
                {
                    "name": "Tripadvisor",
                    "rating": 5
                }
            ]


        },
        {
            "name": "Rollings",
            "data": [
                {
                    "name": "Google",
                    "rating": 4
                },
                {
                    "name": "Tripadvisor",
                    "rating": 5
                }
            ]

        }
    ];

    populate_UI(data)

}

function populate_results(data){

    // FINDS RESULTS WITH MORE THEN 1 SOURCE
    var best_results = [];

    var restaurants = data.restaurants;

    for (var i = 0; i < restaurants.length; i++){

        restaurant = restaurants[i];

        if (restaurant["sources"].length > 1){

            console.log("RESTAURANT WITH MORE THEN 1 SOURCE FOUND");

            rest_info = {
                "name": restaurant.name,
                "data": []
            };

            for( var s = 0; s < restaurant.sources.length; s++){

                source = restaurant.sources[s];

                result = {
                    "name": source.name,
                    "rating": source.rating.aggregate_rating
                };

                rest_info['data'].push(result)

            }

            best_results.push(rest_info);

        }

    }
    
    
    populate_UI(best_results);

    console.log(best_results);
    console.log("DONE");
    
}

function populate_UI(data) {

    for(var i = 0; i < data.length; i++){

        restaurant = data[i];

        var html =
            '<div style="background-color: whitesmoke">'+
            '<div class="content" style="display: inline-block; vertical-align: middle">' +
                '<div class="header">' + restaurant.name + '</div>' +
            '</div>';

        for(var s = 0; s < restaurant.data.length; s++){

            html +=
                '<div style="display: inline-block;">'+
                '<img class="ui avatar image" src="resources/bis_avat.png">' +
                '<div>' + restaurant.data[s].rating + '</div>'+
                '</div>'
        }

        html += '</div>';

        myList = document.getElementById('locationResponse');

        myList.insertAdjacentHTML('beforeend', html);

    }
}

function htmlToElements(html) {
    var template = document.createElement('template');
    template.innerHTML = html;
    return template.content.childNodes;
}

initMap();