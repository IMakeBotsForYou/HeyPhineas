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
var running_speed = 5;
var running_delay = 150;

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

      socket.on('my_location', function(data){
        var name = data[0];
        var location = data[1];
        console.log("my_location", name, location);

        var myLatLng = new google.maps.LatLng(location[0], location[1]);

        if (name in user_locations){
            user_locations[name].location = myLatLng;
        } else {
            user_locations[name] = {"location": myLatLng};
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

      socket.on('update_destination', function(data){
        lat = data[0];
        lng = data[1];
        destination = new google.maps.LatLng(lat, lng);
        first = true;
        step_index = 0;
        onChangeHandler();
//        console.log(data);
      });

//      var slider = document.getElementById("running_speed_slider");
//      slider.oninput = function() {
//          running_speed =  this.value;
////          console.log(500000, running_delay);
//      }

      $("#make_step").on("click", function() {
        if (current_directions != null && current_directions.length > step_index - 1){
            step_index += 1;
            socket.emit('my_location', current_directions[step_index])
            socket.emit('step')
//            console.log(current_directions[step_index]);
        }
      });

      var suggestion_markers = [];

      socket.on('location_suggestion', function(data){
            for (let i = 0; i < suggestion_markers.length; i++) {
                suggestion_markers[i].setMap(null);
            }

            for(let i = 0; i < data.length; i++){
                var place = data[i];
                console.log(place);
                var location = place.location;

                var myLatLng = new google.maps.LatLng(location.lat, location.lng);
                var marker = new google.maps.Marker({
                    position: myLatLng,
                    label: data[i].name,
                    map: map,
                    icon: place.icon
                });

                suggestion_markers.push(marker);
            }

            suggestion_markers.forEach(function(item){
                item.addListener('click', () => {
                    console.log(item.label);
                });
            });
      });


      $("#start_origin").on("click", function() {
            var meter = running_speed;
            var unit = meter * 0.0000089;
            function move_towards_next_point() {
            try{
                var current_pos = user_locations[user].marker.getPosition().toJSON();
                var my_lat = current_pos.lat;
                var my_long = current_pos.lng;
                var next_point = current_directions[step_index];
            } catch(e){
            console.log(e);
            clearInterval(myInterval);
            console.log('stop simulation!! 1');

                return;
            }
            if(next_point == undefined || next_point == null){
                clearInterval(myInterval);
                console.log('stopp simulation!! 2');
                return;
             }

            var new_lat = 0;
            var new_long = 0;

            var d = distance(next_point[0], next_point[1], my_lat, my_long);
            if (d < unit){
                new_lat = next_point[0];
                new_long = next_point[1];
            } else
            {

            var percent = unit / d;
            console.log(next_point[0]-my_lat, next_point[1]-my_long)
            new_lat = my_lat + (next_point[0]-my_lat) * percent;
            new_long = my_long + (next_point[1]-my_long) * percent;
//                console.log(1, my_lat, my_long);
            }

            if (new_lat == next_point[0]){
//                console.log(2, new_lat, new_long);
                step_index += 1;
                if(current_directions.length == step_index)
                    clearInterval(myInterval);
                socket.emit('step');
            }
//            console.log(3, new_lat, new_long);
            var new_loc = new google.maps.LatLng( new_lat, new_long )
//            user_locations[user].marker.setPosition(new_loc);
//            user_locations[user].location = new_loc;
            socket.emit('my_location', [new_lat, new_long, step_index])
            }

            var myInterval = setInterval(move_towards_next_point, running_delay);
            console.log('start simulation!!');

            function distance(lat1, lng1, lat2, lng2){
                return Math.sqrt((lat1-lat2)*(lat1-lat2)+(lng2-lng1)*(lng2-lng1));
            }
            function toDegrees (angle) {
              return angle * (180 / Math.PI);
            }
            function toRadians (angle) {
              return angle * (Math.PI / 180);
            }


      });




      socket.on('user_paths', function(data){
        for(let i = 0; i < data.length; i++){
            // this loop goes through users
            // get current user
            var current_user_data = data[i];
            // name
            var user_name = current_user_data[0];
            // path
            var user_path = current_user_data[1];
            // format path into google maps' LatLng format
            var formatted_user_path = user_path.map(x =>  new google.maps.LatLng(x.lat, x.lng));
//            console.log(1, user_name, user_path, formatted_user_path);

            if (name in paths){
                paths[name].path.setMap(null);
                paths[name].path = new google.maps.Polyline({
                    path: formatted_user_path,
                    geodesic: true,
                    strokeOpacity: 1.0,
                    strokeColor: paths[name].colour,
                    strokeWeight: 5,
                    map: map
                });
                console.log(2);
            } else{
                paths[name] = {"path": null, "colour": colours[colours_index]};
                colours_index += 1;
                colours_index %= colours.length;

                paths[name].path = new google.maps.Polyline({
                    path: formatted_user_path,
                    geodesic: true,
                    strokeOpacity: 1.0,
                    strokeColor: paths[name].colour,
                    strokeWeight: 5,
                    map: map
                });
                console.log(3);
            }
            console.log(4, paths[name].path);
        }
    });

      socket.on('party_member_coords', function(data){
        var request_directions = data[0];
        data = data[1];
        console.log("party_member_coords", request_directions, data);
        for(let i = 0; i < data.length; i++){
            var name = data[i][0];
            var latlng = data[i][1];
            var myLatLng = new google.maps.LatLng(latlng[0], latlng[1])

            if (name in user_locations){
                user_locations[name].location = myLatLng;
            } else {
                user_locations[name] = {"location": myLatLng}
            }

            if ('marker' in user_locations[name]){
                user_locations[name]["marker"].setPosition(myLatLng);
            } else {
                user_locations[name]["marker"] = new google.maps.Marker({
                    position: myLatLng,
                    label: name,
                    map: map
                });
            }
        }
//        for(let i = 0; i < data.length; i++){
//            user_locations[data[i][0]]["marker"].addListener("click", () => {
//                console.log( user_locations[data[i][0]]["marker"].label);
//                socket.emit('knn_select', user_locations[data[i][0]]["marker"].label)
//            });
//        }
        if (request_directions){
            first = true;
            onChangeHandler();
        }
    });
      var user_added_locations = {};
      socket.on('user_added_locations', function(data){
        var user_location_markers = [];
        for(let i = 0; i < data.length; i++){
            var name = data[i][0];
            var latlng = data[i][1];
            if(`${latlng[0]}, ${latlng[1]}` in user_added_locations){

            } else {
                var myLatLng = new google.maps.LatLng(latlng[0], latlng[1])
                var m = new google.maps.Marker({
                        position: myLatLng,
                        label: name,
                        map: map,
                        icon: "https://developers.google.com/maps/documentation/javascript/examples/full/images/beachflag.png"
                });
                markerArray.push(m);
                user_location_markers.push(m);
                user_added_locations[`${latlng[0]}, ${latlng[1]}`] = 1;
                user_location_markers[i].addListener("click", () => {
                socket.emit('request_destination_update', [user_location_markers[i].getPosition().lat(), user_location_markers[i].getPosition().lng()])
                map.setCenter(user_location_markers[i].getPosition());
                });
            }
        }
      });

      function color_dot_link(colour){
        return "https://maps.google.com/mapfiles/ms/icons/"+ colour + "-dot.png"
      }
      socket.on('user_colors', function(data){
         console.log(data);
         for (const [username, colour] of Object.entries(data)) {
            if (username in user_locations)
            user_locations[username].marker.setIcon(color_dot_link(colour));
         }
      });

//      socket.on('knn_results', function(data){
//        for(name in user_locations){
//            user_locations[name].marker.setIcon('https://maps.google.com/mapfiles/ms/icons/red-dot.png');
//        }
//        for(let i=0; i<data.length;i++){
//            var name = data[i];
//            user_locations[name].marker.setIcon('http://maps.google.com/mapfiles/ms/icons/green-dot.png');
//        }
//        // user_colors
//      });
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

  if (!(user in user_locations)){
        socket.emit('user_added_locations_get');
        socket.emit('party_members_list_get');
        socket.emit('online_members_get');
        socket.emit('get_destination')
        // TEMP

        socket.emit('get_coords_of_party')
        console.log("pussy")
        return;
  } else {
  var origin = user_locations[user].location;
}
  if (first && destination != null){
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
                console.log(i, coords.lat(), coords.lng())
             }
          }
          step_index = 0;
          first = false;
          socket.emit('send_current_path', current_directions);
          if (leader_of_party){
            socket.emit('send_dest', destination);
          }
//          document.getElementById("warnings-panel").innerHTML =
//          "<b>" + directionsData.warnings + "</b>";
　
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