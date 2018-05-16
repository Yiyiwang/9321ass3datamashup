var json={'a': 'First', 'b': 'Second', 'c': 'Third'};


function initMap() {

    var card = document.getElementById('pac-card');
    var input = document.getElementById('pac-input');

    var autocomplete = new google.maps.places.Autocomplete(input);

    var infowindow = new google.maps.InfoWindow();
    var infowindowContent = document.getElementById('infowindow-content');

    infowindow.setContent(infowindowContent);

    autocomplete.addListener('place_changed', function() {

        console.log("PLACE CHANGED");

        infowindow.close();

        var place = autocomplete.getPlace();

        if (!place.geometry) {
            // User entered the name of a Place that was not suggested and
            // pressed the Enter key, or the Place Details request failed.
            window.alert("No details available for input: '" + place.name + "'");
            return;
        }

        // NOT USED AT THE MOMENT
        var address = '';
        if (place.address_components) {
            address = [
                (place.address_components[0] && place.address_components[0].short_name || ''),
                (place.address_components[1] && place.address_components[1].short_name || ''),
                (place.address_components[2] && place.address_components[2].short_name || '')
            ].join(' ');
        }

    });

}


function handleLocationSearch() {

    document.getElementById('locationResponse').innerHTML = "";
    ul = makeUL();
    document.getElementById('locationResponse').appendChild(makeUL(json));
}


function makeUL() {
    // Create the list element:
    var list = document.createElement('list');
    list.class = "ui middle aligned selection";
    list.style = "wirdth:100%; margin-top: 10px";

    for(var i = 0; i < Object.keys(json).length; i++) {
        // Create the list item:
        var item = document.createElement('div');
        item.class = "listitem";
        //item.style = "background-color:whitesmoke; margin-bottom:10px; height:60px";

        var img = document.createElement('img');

        img.class = 'ui avatar image';
        img.src = 'resources/bis_avat.png';
        img.style = "height:40%";

        var header = document.createElement('header');
        header.innerHTML = Object.values(json)[i];

        item.appendChild(img);
        item.appendChild(header);

        // Add it to the list:
        list.appendChild(item);
    }

    // Finally, return the constructed list:
    return list;
}

function myMap()
{
    myCenter=new google.maps.LatLng(41.878114, -87.629798);
    var mapOptions= {
        center:myCenter,
        zoom:12, scrollwheel: false, draggable: false,
        mapTypeId:google.maps.MapTypeId.ROADMAP
    };
    var map=new google.maps.Map(document.getElementById("googleMap"),mapOptions);

    var marker = new google.maps.Marker({
        position: myCenter,
    });
    marker.setMap(map);
}

// Modal Image Gallery
function onClick(element) {
    document.getElementById("img01").src = element.src;
    document.getElementById("modal01").style.display = "block";
    var captionText = document.getElementById("caption");
    captionText.innerHTML = element.alt;
}


function myFunction() {
    var navbar = document.getElementById("myNavbar");
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        navbar.className = "w3-bar" + " w3-card" + " w3-animate-top" + " w3-white";
    } else {
        navbar.className = navbar.className.replace(" w3-card w3-animate-top w3-white", "");
    }
}

// Used to toggle the menu on small screens when clicking on the menu button
function toggleFunction() {
    var x = document.getElementById("navDemo");
    if (x.className.indexOf("w3-show") == -1) {
        x.className += " w3-show";
    } else {
        x.className = x.className.replace(" w3-show", "");
    }
}

initMap();

