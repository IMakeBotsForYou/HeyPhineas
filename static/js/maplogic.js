function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function showSteps(directionResult, markerArray, stepDisplay, map) {
  // For each step, place a marker, and add the text to the marker's infowindow.
  // Also attach the marker to an array so we can keep track of it and remove it
  // when calculating new routes.
  const myRoute = directionResult.routes[0].legs[0];
  for (let i = 0; i < myRoute.steps.length; i++) {
    const marker = (markerArray[i] =
      markerArray[i] || new google.maps.Marker());
    marker.setMap(map);
    marker.setPosition(myRoute.steps[i].start_location);
    attachInstructionText(
      stepDisplay,
      marker,
      myRoute.steps[i].instructions,
      map
    );
  }
}

var first = true;
var onChangeHandler = null;
var user_locations = {}
var markerArray = [];
var current_directions;
var destination = null;
var step_index = 0;
deshalit = {"lat": 31.89961596028198, "lng": 34.816320411774875};
colours =
["#9a465c",
"#469a83",
"#29a0b1",
"#167d7f",
"#98d7c2",
"#ddffe7",
"#9a4686",
"#9a5946",
"#9a8346",
"#5c9a46"];

colours_index = 0;
paths = {}



function initMap() {
      // Instantiate a directions service.
      const directionsService = new google.maps.DirectionsService();

      // Create a map and center it on my house.
      const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: { lat: 31.894756, lng: 34.809322 },
      });

      socket.on('update_location', function(data){
        var name = data[0];
        var latlng = data[1];
        var myLatLng = new google.maps.LatLng(latlng[0], latlng[1])
        console.log(`${name}, ${latlng}`);
        if (name in user_locations){
            user_locations[name].location = myLatLng;
        } else {
            user_locations[name] = {"location": myLatLng}
        }

        if ('marker' in user_locations[name]){
            user_locations[name]["marker"].setPosition(myLatLng);
        } else {
            var marker = new google.maps.Marker({
                position: myLatLng,
                label: name,
                map: map
            });
            user_locations[name]["marker"] = marker;
        }
      });

      $("#make_step").on("click", function() {
        if (current_directions != null && current_directions.length > step_index - 1){
            step_index += 1;
            socket.emit('my_location', current_directions[step_index])
            socket.emit('step')
            console.log(current_directions[step_index]);
        }
      });

      var place_markers = [];
      socket.on('recommended_places', function(data){
            for (let i = 0; i < place_markers.length; i++) {
                place_markers[i].setMap(null);
            }

            for(let i = 0; i < data.length; i++){
                var location = data[i].location;

                var myLatLng = new google.maps.LatLng(location[0], location[1]);
                var marker = new google.maps.Marker({
                    position: myLatLng,
                    label: data[i].name,
                    map: map
                });

                place_markers.push(marker);
                place_markers[place_markers.length-1].addListener("click", () => {
                    //socket.emit('knn_select', user_locations[data[i][0]]["marker"].label)
                    console.log(place_markers[place_markers.length-1].label);
                });
            }
       });


      $("#start_origin").on("click", function() {
        const myInterval = setInterval(move_towards_next_point, 1000);
        const meters = 10;
        const ten_metres = meters * 0.0000089;
        function move_towards_next_point() {

            var current_pos = user_locations[user].marker.getPosition().toJSON();
            var my_lat = current_pos.lat;
            var my_long = current_pos.lng;
            var next_point = current_directions[step_index];


            var theta = Math.atan((next_point.lng-my_lng)/(next_point.lat-my_lat));

            var new_lat = my_lat + ten_metres*Math.sin(theta);
            var new_long = my_long + ten_metres*Math.cos(theta)/Math.cos(my_lat * 0.018);

            user_locations[user].marker.setPosition(new google.maps.LatLng(new_lat, new_long));
            user_locations[user].position = new google.maps.LatLng(new_lat, new_long);


        }
      });




      socket.on('user_paths', function(data){


        for(let i = 0; i < data.length; i++){
            let name = data[i][0];
            let coords = data[i][1];
            let path = [];


            for(let i = 0; i < coords.length; i++){
                path.push({lat: coords[i][0], lng: coords[i][1]})
            }

             var user_path;

            if (!(name in paths)){
                paths[name] = {"path": user_path, "colour": colours[colours_index]};
                colours_index += 1;
                colours_index %= colours.length;
            } else
                paths[name].path = user_path

            user_path = new google.maps.Polyline({
                path: path,
                geodesic: true,
                strokeOpacity: 1.0,
                strokeColor: paths[name].colour,
                strokeWeight: 5,
                map: map
            });
        };
      });

      socket.on('party_member_coords', function(data){
        var request_directions = data[0];
        data = data[1];

        for(let i = 0; i < data.length; i++){
            var name = data[i][0];
            var latlng = data[i][1];
            var myLatLng = new google.maps.LatLng(latlng[0], latlng[1])
            console.log(`${name}, ${latlng}`);

            if (name in user_locations){
                user_locations[name].location = myLatLng;
            } else {
                user_locations[name] = {"location": myLatLng}
            }

            if ('marker' in user_locations[name]){
                user_locations[name]["marker"].setPosition(myLatLng);
            } else {
                var marker = new google.maps.Marker({
                    position: myLatLng,
                    label: name,
                    map: map
                });
                user_locations[name]["marker"] = marker;
            }
        }
        for(let i = 0; i < data.length; i++){
            user_locations[data[i][0]]["marker"].addListener("click", () => {
                console.log( user_locations[data[i][0]]["marker"].label);
                socket.emit('knn_select', user_locations[data[i][0]]["marker"].label)
            });
        }
        if (request_directions){
            first = true;
            onChangeHandler();
        }
    });

      socket.on('user_added_locations', function(data){
        for(let i = 0; i < data.length; i++){
            var name = data[i][0];
            var latlng = data[i][1];
            var myLatLng = new google.maps.LatLng(latlng[0], latlng[1])
            var m = new google.maps.Marker({
                    position: myLatLng,
                    label: name,
                    map: map,
                    icon: "https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png"
            });
            markerArray.push(m);
        }
      });
      socket.on('knn_results', function(data){
        for(name in user_locations){
            user_locations[name].marker.setIcon('https://maps.google.com/mapfiles/ms/icons/red-dot.png');
        }
        for(let i=0; i<data.length;i++){
            var name = data[i];
            user_locations[name].marker.setIcon('http://maps.google.com/mapfiles/ms/icons/green-dot.png');
        }
      });
      // Create a renderer for directions and bind it to the map.
      const directionsRenderer = new google.maps.DirectionsRenderer({ map: map });
      // Instantiate an info window to hold step text.
      const stepDisplay = new google.maps.InfoWindow();

      onChangeHandler = function () {
          calculateAndDisplayRoute(
          directionsRenderer,
          directionsService,
          markerArray,
          stepDisplay,
          map
        );
      };
      // Listen to change events from the start and end lists.
      directionsRenderer.setMap(map); // Existing map object displays directions
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


function calculateAndDisplayRoute(
  directionsRenderer,
  directionsService,
  markerArray,
  stepDisplay,
  map
) {
    if(user == "Admin"){
    return;
    }

  // Retrieve the start and end locations and create a DirectionsRequest using
  // WALKING directions.
//  secret_start = document.getElementById("secret_start").value;
//  secret_end =   document.getElementById("secret_end").value;

  if(secret_end == '' || secret_start == ''){
    return;
  }
  var origin = user_locations[user].location;
  if(destination == null){
    destination = deshalit;
  }

  if (first){
      directionsService
        .route({
          origin: origin,
          destination: destination,
          travelMode: google.maps.TravelMode.WALKING,
        })
        .then((result) => {
          // Route the directions and pass the response to a function to create
          // markers for each step.
          var directionsData = result.routes[0] // Get data about the mapped route
          var myRoute = directionsData.legs[0]
          current_directions = [];
          for(let i = 0; i < myRoute.steps.length; i++){
             var step = myRoute.steps[i];
             for(let i = 0; i < step.path.length; i++){
                var coords = step.path[i];
                current_directions.push([coords.lat(), coords.lng()]);
             }
          }
          step_index = 0;
          first = false;

          socket.emit('send_current_path', current_directions);

          document.getElementById("warnings-panel").innerHTML =
          "<b>" + directionsData.warnings + "</b>";

          directionsRenderer.setDirections(result);


        //showSteps(result, markerArray, stepDisplay, map);
          document.getElementById('msg').innerHTML = " Walking distance is " + directionsData.legs[0].distance.text + " (" + directionsData.legs[0].duration.text + ").";
        })
    }
}

function attachInstructionText(stepDisplay, marker, text, map) {
  google.maps.event.addListener(marker, "click", () => {
    // Open an info window when the marker is clicked on, containing the text
    // of the step.
    stepDisplay.setContent(text);
    stepDisplay.open(map, marker);
  });
}