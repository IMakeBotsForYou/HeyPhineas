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
var step_index = 0;
deshalit = {"lat": 31.89961596028198, "lng": 34.816320411774875}
function initMap() {
      // Instantiate a directions service.
      const directionsService = new google.maps.DirectionsService();

      // Create a map and center it on my house.
      const map = new google.maps.Map(document.getElementById("map"), {
        zoom: 16,
        center: { lat: 31.894756, lng: 34.809322 },
      });

      $("#make_step").on("click", function() {
        if (current_directions != null && current_directions.length < step_index - 1){
            step_index += 1;
            socket.emit('my_location', current_directions[step_index])
        }
      });

      socket.on('update_location', function(data){
        var name = data[0];
        var lat = data[1];
        var lng = data[2];
        var myLatLng = new google.maps.LatLng(lat, lng)

        user_locations[name].location = myLatLng
        user_locations[name]["marker"].setPosition(myLatLng);
      });

      socket.on('party_member_coords', function(data){
        var request_directions = data[0];
        data = data[1];
        names = [];

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
                var marker = new google.maps.Marker({
                    position: myLatLng,
                    label: name,
                    map: map
                });
                user_locations[name]["marker"] = marker;
            }
//            if(name == "Dan"){
//                document.getElementById("secret_start").value = name;
//            }else{
//                document.getElementById("secret_end").value = name;
//            }
        }
        for(let i = 0; i < data.length; i++){
            user_locations[data[i][0]]["marker"].addListener("click", () => {
                console.log( user_locations[data[i][0]]["marker"].label);
                socket.emit('knn_select', user_locations[data[i][0]]["marker"].label)
            });
        }
        if (request_directions){
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


  // Retrieve the start and end locations and create a DirectionsRequest using
  // WALKING directions.
//  secret_start = document.getElementById("secret_start").value;
//  secret_end =   document.getElementById("secret_end").value;

  if(secret_end == '' || secret_start == ''){
    return;
  }
  origin = user_locations[user].location;
//  destination = user_locations[secret_end].location;
  destination = deshalit;
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

          socket.emit('in_progress');

          document.getElementById("warnings-panel").innerHTML =
          "<b>" + directionsData.warnings + "</b>";

          directionsRenderer.setDirections(result);


        //showSteps(result, markerArray, stepDisplay, map);
          document.getElementById('msg').innerHTML = " Driving distance is " + directionsData.legs[0].distance.text + " (" + directionsData.legs[0].duration.text + ").";
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